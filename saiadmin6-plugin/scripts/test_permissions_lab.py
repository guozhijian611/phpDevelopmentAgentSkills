#!/usr/bin/env python3
"""Real HTTP permission matrix and ZIP lifecycle, only in a freshly initialized lab.py environment."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from fixture_package import install, uninstall
from lab_fixture import Lab

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lab',required=True,type=Path)
    p.add_argument('--disposable-fixture',required=True,action='store_true');a=p.parse_args();lab=Lab(a.lab)
    skill=Path(__file__).resolve().parents[1];statefile=lab.server/'runtime/labpermit-fixture.json'
    if (lab.server/'plugin/labpermit').exists() or statefile.exists():p.error('Requires a fresh lab without labpermit')
    target=lab.server/'permission_fixture.php';pending=target.with_suffix('.partial')
    shutil.copyfile(skill/'tests/permission_fixture.php',pending);pending.replace(target)
    def fixture(mode,*args):
        output=lab.compose('exec','-T','backend','php','permission_fixture.php','--disposable-fixture',mode,*args).strip()
        if output:print(output,flush=True)
    with tempfile.TemporaryDirectory(prefix='sai6-permission-zips-') as temp:
        subprocess.run([sys.executable,str(skill/'scripts/build_permission_example.py'),'--output-dir',temp],check=True,stdout=subprocess.DEVNULL)
        old=Path(temp)/'labpermit-1.0.0.zip';new=Path(temp)/'labpermit-1.1.0.zip'
        install(lab,old);fixture('setup');state=json.loads(statefile.read_text());admin=lab.token()
        def req(action,data=None,who='actor',method=None):
            return lab.request('/app/labpermit/items/'+action,data,admin if who=='admin' else state['tokens'].get(who),method)
        def ok(action,data=None,who='actor',method=None):
            r=req(action,data,who,method);assert r.get('code')==200,(action,r.get('message'));return r.get('data')
        def deny(action,data=None,who='actor',method=None):
            r=req(action,data,who,method);assert r.get('code')!=200,('Unexpected access',action);return r
        assert len(ok('index')['items'])==1
        before=ok('read?id='+str(state['items']['actor']))
        install(lab,new);assert ok('read?id='+str(state['items']['actor']))==before
        print('PASS old ZIP upgrade preserves rows and maps legacy grants',flush=True)
        install(lab,new,repeat=True)
        for action,method,payload in [('index','GET',None),('read?id=1','GET',None),('stats','GET',None),('children?id=1','GET',None),('save','POST',{}),('update','PUT',{}),('destroy','DELETE',{})]:
            r=deny(action,payload,'menuOnly',method);assert '权限不足' in r.get('message','')
        deny('index',who='none');deny('index',who='anonymous')
        role=state['roles']['actor']
        def scope(value):
            r=lab.request('/core/role/read?id='+str(role),token=admin);assert r.get('code')==200
            data={k:r['data'][k] for k in ['id','name','code','level','status']};data['data_scope']=value
            assert lab.request('/core/role/update',data,admin,'PUT').get('code')==200
        for value,keys in [(1,['actor','peer','child','other']),(2,['other']),(3,['actor','peer']),(4,['actor','peer','child']),(5,['actor'])]:
            if value==2:fixture('custom')
            scope(value);data=ok('index');expected={int(state['items'][k]) for k in keys}
            assert {int(r['id']) for r in data['items']}==expected and data['total']==len(expected)
            assert ok('index?limit=1')['total']==len(expected) and len(ok('index?limit=1')['items'])==1
            assert ok('stats')['count']==len(expected)
            assert int(ok('stats')['sum'])==sum(['actor','peer','child','other'].index(k)+1 for k in keys)
            for key in ['actor','peer','child','other']:
                action='read?id='+str(state['items'][key]);children='children?id='+str(state['items'][key])
                if key in keys:ok(action);assert len(ok(children))==1
                else:deny(action);deny(children)
        fixture('custom','empty');scope(2);assert ok('index')['total']==0;scope(5)
        own=state['items']['actor'];foreign=state['items']['other']
        deny('destroy',{'ids':[own,foreign]},method='DELETE');ok('read?id='+str(own))
        deny('update',{'id':foreign,'label':'blocked'},method='PUT')
        ok('update',{'id':own,'label':'own edited','created_by':state['users']['other']},method='PUT')
        assert int(ok('read?id='+str(own))['created_by'])==int(state['users']['actor'])
        created=ok('save',{'label':'server-owned','created_by':state['users']['other']})
        assert int(ok('read?id='+str(created['id']))['created_by'])==int(state['users']['actor'])
        # Warm a session, revoke its point, then run idempotent registration again.
        ok('stats');fixture('permission','labpermit:items:stats');deny('stats');ok('index')
        fixture('probe')
        if lab.meta['db']=='pgsql':fixture('pgsql')
        protected=lab.request('/app/saipackage/install/uninstall',{'appName':'labpermit'},admin)
        assert protected.get('code')!=200;ok('index')
        if lab.meta['db']=='pgsql':fixture('pgsql')
        print('PASS five scopes, SQL totals/aggregates, nested rows, forged owners, atomic batches and warmed-session revocation',flush=True)
        fixture('cleanup');uninstall(lab)
        lab.compose('restart','backend');lab.wait();fixture('uninstalled')
        install(lab,new);assert ok('index',who='admin')['total']==0
        uninstall(lab)
        lab.compose('restart','backend');lab.wait()
        print('PASS '+lab.meta['db']+' complete ZIP permission fixture and empty reinstall; lab retained for inspection',flush=True)
if __name__=='__main__':main()
