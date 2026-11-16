#!/usr/bin/env python3
"""Offline protocol-state checks; no Docker or SaiAdmin server is contacted."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from fixture_package import install, uninstall
from lab_fixture import Lab

class FakeLab:
    def __init__(self,states,interrupted=False):self.states=states;self.interrupted=interrupted;self.writes=[];self.reads=0
    def wait(self):pass
    def compose(self,*args):return ''
    def token(self):return 'fixture-only'
    def request(self,path,data=None,token=None,package=None):
        if path.endswith('/upload'):self.writes.append('upload');return {'code':200}
        if path.endswith('/install'):
            self.writes.append('install')
            if self.interrupted:raise ConnectionError('reload')
            return {'code':200}
        if path.endswith('/index') and 'saipackage' in path:
            state=self.states[min(self.reads,len(self.states)-1)];self.reads+=1
            return {'data':{'data':[{'app':'labpermit','version':state[0],'state':state[1]}]}}
        return {'code':self.states[min(max(self.reads-1,0),len(self.states)-1)][2]}

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='sai6-fixture-state-');self.root=Path(self.temp.name);self.package=self.root/'fixture.zip'
        with zipfile.ZipFile(self.package,'w') as z:z.writestr('info.ini','app = labpermit\nversion = 1.1.0\n')
    def tearDown(self):self.temp.cleanup()
    def test_response_interruption_does_not_repeat_write(self):
        lab=FakeLab([('1.1.0',2,200),('1.1.0',1,500),('1.0.0',1,200),('1.1.0',1,200)],True)
        with patch('fixture_package.time.sleep'),contextlib.redirect_stdout(io.StringIO()):install(lab,self.package)
        self.assertEqual(lab.writes,['upload','install']);self.assertEqual(lab.reads,4)
    def test_route_without_completed_install_times_out(self):
        lab=FakeLab([('1.1.0',2,200)])
        with patch('fixture_package.time.sleep'),self.assertRaises(RuntimeError):install(lab,self.package)
        self.assertEqual(lab.writes,['upload','install']);self.assertEqual(lab.reads,100)
    def test_dependency_pending_not_falsely_completed(self):
        lab=FakeLab([('1.1.0',4,200)])
        with patch('fixture_package.time.sleep'),self.assertRaises(RuntimeError):install(lab,self.package)
    def test_reject_other_app(self):
        with zipfile.ZipFile(self.package,'w') as z:z.writestr('info.ini','app = business\nversion = 1.1.0\n')
        lab=FakeLab([])
        with self.assertRaises(ValueError):install(lab,self.package)
        self.assertEqual(lab.writes,[])
    def test_interrupted_uninstall_confirms_without_second_post(self):
        lab=FakeLab([]);lab.server=self.root/'server'
        def request(path,data=None,token=None):
            if data is not None:lab.writes.append('uninstall');raise ConnectionError('reload')
            return {'code':200,'data':{'data':[]}}
        lab.request=request
        with patch('fixture_package.time.sleep'),contextlib.redirect_stdout(io.StringIO()):uninstall(lab)
        self.assertEqual(lab.writes,['uninstall'])
    def test_lab_identity_and_initialized_core_rejected(self):
        root=self.root/'sai6lab-fixture';root.mkdir();server=root/'app/server';server.mkdir(parents=True)
        meta={'project':root.name,'backend':'server','frontend':'saiadmin-artd','db':'pgsql'}
        (root/'lab.json').write_text(json.dumps(meta));(server/'.env').write_text('already initialized')
        helper=Path(__file__).resolve().parents[1]/'scripts/prepare_fixture_lab.py'
        r=subprocess.run([sys.executable,str(helper),'--lab',str(root),'--disposable-fixture'],capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0);self.assertIn('Already initialized',r.stderr)
        self.assertEqual((server/'.env').read_text(),'already initialized')
        meta['project']='sai6lab-another';(root/'lab.json').write_text(json.dumps(meta))
        with self.assertRaises(ValueError):Lab(root)
if __name__=='__main__':unittest.main()
