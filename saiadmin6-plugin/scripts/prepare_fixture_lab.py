#!/usr/bin/env python3
"""Initialize a fresh 6.1.5/6.1.0 lab and create a private test JWT. CLI-only, disposable fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from lab_fixture import Lab

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lab',required=True,type=Path)
    p.add_argument('--disposable-fixture',required=True,action='store_true');a=p.parse_args();lab=Lab(a.lab)
    if (lab.server/'.env').exists():p.error('Already initialized: create a new lab instead of deleting .env')
    lock=lab.server/'composer.lock';versions={v['name']:v['version'].lstrip('v') for v in json.loads(lock.read_text())['packages']}
    if versions.get('saithink/saiadmin')!='6.1.5' or versions.get('saithink/saipackage')!='6.1.0':p.error('Initializer only verified for SaiAdmin 6.1.5 / saipackage 6.1.0; inspect other contracts manually')
    controller=lab.server/'plugin/saiadmin/app/controller/InstallController.php'
    if not all(s in controller.read_text() for s in ["post('dbType'", "post('dataType'",'function install(']):p.error('Unknown core installer contract')
    process=lab.server/'config/process.php';text=process.read_text()
    before="'enable_file_monitor' => !in_array('-d', $argv) && DIRECTORY_SEPARATOR === '/',"
    if text.count(before)!=1:p.error('Unsupported development watcher; no files changed')
    # Avoid development hot reload during payload copy; leave the installer's real reload intact.
    process.write_text(text.replace(before,"'enable_file_monitor' => false, // disposable fixture",1))
    lab.compose('restart','backend');lab.wait('/core/install',authenticated=False)
    port=5432 if lab.meta['db']=='pgsql' else 3306
    for _ in range(60):
        try:lab.compose('exec','-T','backend','php','-r',f'exit(@fsockopen("db",{port}) ? 0 : 1);');break
        except RuntimeError:time.sleep(.5)
    else:raise RuntimeError('Database TCP readiness timeout')
    params={'username':'postgres' if port==5432 else 'root','password':(lab.root/'db-secret').read_text().strip(),
            'database':'saiadmin','host':'db','port':port,'dbType':lab.meta['db'],'dataType':'pure'}
    result=lab.request('/core/install/install',params)
    if result.get('code')!=200:
        diagnostic=lab.root/'core-install-error.json';diagnostic.write_text(json.dumps(result));diagnostic.chmod(0o600)
        raise RuntimeError('Core initialization failed; inspect private diagnostic: '+str(diagnostic))
    # A returned initialization response may still come from a worker scheduled for SIGUSR1 exit.
    lab.compose('restart','backend');lab.wait('/core/install',authenticated=False)
    helper=lab.server/'fixture-token.php';target=lab.server/'runtime/labpermit-admin-token.json'
    helper.write_text("<?php require __DIR__.'/vendor/autoload.php';require __DIR__.'/support/bootstrap.php';$f=__DIR__.'/runtime/labpermit-admin-token.json';file_put_contents($f,json_encode(\\Tinywan\\Jwt\\JwtToken::generateToken(['id'=>1,'plat'=>'saiadmin','username'=>'admin'])));chmod($f,0600);")
    lab.compose('exec','-T','backend','php',helper.name)
    try:token=json.loads(target.read_text())['access_token'];(lab.root/'http-token').write_text(token);(lab.root/'http-token').chmod(0o600)
    finally:helper.unlink();target.unlink(missing_ok=True)
    lab.wait()
    files=['composer.lock','plugin/saipackage/app/logic/InstallLogic.php','plugin/saipackage/app/logic/PluginMigrator.php','plugin/saiadmin/app/logic/system/SystemRoleLogic.php']
    evidence={name:hashlib.sha256((lab.server/name).read_bytes()).hexdigest() for name in files if (lab.server/name).is_file()}
    (lab.root/'baseline-sha256.json').write_text(json.dumps(evidence,indent=2))
    print('PASS core initialization, DB TCP and authenticated host readiness:',lab.meta['db'],lab.url)
if __name__=='__main__':main()
