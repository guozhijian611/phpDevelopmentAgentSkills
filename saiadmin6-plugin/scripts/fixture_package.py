#!/usr/bin/env python3
"""Upload/install a labpermit example once; confirm version, state AND a real route after reload."""
import argparse
import configparser
from pathlib import Path
import time
import zipfile
from lab_fixture import Lab

def install(lab,package,repeat=False):
    with zipfile.ZipFile(package) as z:
        info=configparser.ConfigParser(interpolation=None);info.read_string('[plugin]\n'+z.read('info.ini').decode())
        if info['plugin']['app']!='labpermit':raise ValueError('Only the labpermit example is accepted')
        version=info['plugin']['version']
    lab.wait();token=lab.token()
    result=lab.request('/app/saipackage/install/upload',token=token,package=package)
    if repeat:
        assert result.get('code')!=200,'Same-version upload unexpectedly succeeded'
        return
    assert result.get('code')==200,'Upload refused; inspect lab runtime before retrying'
    try:
        result=lab.request('/app/saipackage/install/install',{'appName':'labpermit'},token)
        assert result.get('code')==200,'Installation returned an error; inspect migration state'
    except (OSError,RuntimeError):print('Install response interrupted; checking state without repeating write')
    for _ in range(100):
        try:
            listing=lab.request('/app/saipackage/install/index',token=token)
            row=next((r for r in listing.get('data',{}).get('data',[]) if r.get('app')=='labpermit'),{})
            route=lab.request('/app/labpermit/items/index',token=token)
            # These examples declare no dependencies: require fully installed, not dependency-pending.
            if row.get('version')==version and int(row.get('state',0))==1 and route.get('code')==200:
                break
        except (OSError,RuntimeError):pass
        time.sleep(.3)
    else:raise RuntimeError('Install did not converge; route availability alone is not success')
    # One new worker can answer while another is still serving removed/replaced code.
    # Only after the installer completed, stabilize this disposable backend as a whole.
    lab.compose('restart','backend');lab.wait()
    print('PASS ZIP import, version, installed state and authenticated route:',version)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lab',required=True,type=Path);p.add_argument('--zip',required=True,type=Path)
    p.add_argument('--repeat',action='store_true');p.add_argument('--disposable-fixture',required=True,action='store_true');a=p.parse_args()
    install(Lab(a.lab),a.zip,a.repeat)

def uninstall(lab):
    """An interrupted response is uncertain, so confirm removal instead of sending another POST."""
    lab.wait();token=lab.token()
    try:
        result=lab.request('/app/saipackage/install/uninstall',{'appName':'labpermit'},token)
        assert result.get('code')==200,'Uninstall rejected; do not retry'
    except (OSError,RuntimeError):print('Uninstall response interrupted; checking removal without repeating write')
    for _ in range(100):
        try:
            result=lab.request('/app/saipackage/install/index',token=token)
            rows=result.get('data',{}).get('data',[])
            row=next((r for r in rows if r.get('app')=='labpermit'),None)
            if result.get('code')==200 and (not row or int(row.get('state',-1))==0) and not (lab.server/'plugin/labpermit').exists():return
        except (OSError,RuntimeError):pass
        time.sleep(.3)
    raise RuntimeError('Uninstall result remains uncertain; inspect lab state before another write')
if __name__=='__main__':main()
