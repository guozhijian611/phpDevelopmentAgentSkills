#!/usr/bin/env python3
"""Local HTTP protocol regression; no live credentials or real marketplace writes."""
import base64, contextlib, hashlib, importlib.util, io, json, os, subprocess, sys, tempfile, threading, unittest, zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/saistore.py'
spec=importlib.util.spec_from_file_location('saistore',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def respond(self,data=None,code=200,message='success'):
        raw=json.dumps({'code':code,'message':message,'data':data}).encode()
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));
        if self.path=='/prod/core/captcha':self.send_header('Set-Cookie','captcha=nonce; Path=/prod')
        self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        server=self.server;server.calls.append(('GET',self.path))
        if self.path=='/prod/core/captcha':return self.respond({'uuid':'challenge-id','image':'data:image/png;base64,'+base64.b64encode(b'\x89PNG\r\n\x1a\nfixture').decode(),'result':'MUST-NOT-USE'})
        if self.path=='/prod/redirect':
            self.send_response(302);self.send_header('Location',server.base+'/other-origin-target');self.end_headers();return
        if self.headers.get('Authorization')!='Bearer access-A':return self.respond(code=401)
        if '/read?' in self.path:return self.respond({'id':9,'appname':'example','app_status':server.app_status})
        if '/versionList?' in self.path:return self.respond(server.versions)
        if '/index?' in self.path:return self.respond({'total':0,'data':[]})
        self.respond(code=404)
    def do_POST(self):
        server=self.server;raw=self.rfile.read(int(self.headers.get('Content-Length','0')));server.calls.append(('POST',self.path))
        if self.path=='/prod/core/login':
            server.login=json.loads(raw)
            if self.headers.get('Cookie')!='captcha=nonce':return self.respond(code=400,message='missing captcha cookie')
            if server.reject_login:return self.respond(code=400,message='rejected '+server.login['password'])
            return self.respond({'access_token':'access-A','refresh_token':'refresh-B','expires_in':3600})
        if self.headers.get('Authorization')!='Bearer access-A':return self.respond(code=401)
        if self.path.endswith('/uploadFile') or self.path.endswith('/uploadImage'):
            server.uploaded=raw;server.upload_headers=dict(self.headers);return self.respond({'url':'/uploads/logo.png' if self.path.endswith('/uploadImage') else 'https://files.example.test/package.zip'})
        data=json.loads(raw);server.writes.append((self.path,data))
        if self.path.endswith('/addVersion'):
            if server.reject_version:return self.respond(code=400,message='version rejected')
            server.versions.append(data);return self.respond(11)
        if self.path.endswith('/submitReview'):server.app_status=1;return self.respond(True)
        if self.path.endswith('/save'):return self.respond(9)
        self.respond(code=404)

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='saistore fixture 中文 ');self.root=Path(self.temp.name)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.server.base='http://127.0.0.1:'+str(self.server.server_port)
        self.server.calls=[];self.server.writes=[];self.server.versions=[];self.server.reject_login=False;self.server.reject_version=False;self.server.app_status=0
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=self.server.base+'/prod';self.state=m.State(self.root/'private',self.base)
        self.transport=m.Transport(self.base,allow_http=True);self.client=m.Client(self.state,self.transport,non_interactive=True)
        self.zip=self.root/'plugin.zip';self.package()
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def package(self,extra=None,app='example',version='1.2.3'):
        with zipfile.ZipFile(self.zip,'w') as z:
            z.writestr('info.ini',f'app = {app}\nversion = {version}\nsupport = 6.x\ntitle = Example\nabout = Example plugin\nauthor = Fixture\n');z.writestr('config.json','{}')
            z.writestr('plugin/'+app+'/config/app.php','<?php return [];')
            if extra:z.writestr(extra,'bad')
    def login(self):self.state.save('fixture-user',{'access_token':'access-A','refresh_token':'refresh-B','expires_in':3600})
    def test_manual_captcha_password_not_stored_and_token_permissions(self):
        answers=iter(['fixture-user','USER-CODE'])
        with contextlib.redirect_stderr(io.StringIO()) as output:
            m.interactive_login(self.state,self.transport,open_image=False,input_fn=lambda _:next(answers),password_fn=lambda _:'dummy-private-password',interactive=True)
        self.assertEqual(self.server.login,{'username':'fixture-user','password':'dummy-private-password','code':'USER-CODE','uuid':'challenge-id'})
        value=self.state.load();self.assertEqual(value['refresh_token'],'refresh-B')
        self.assertNotIn('dummy-private-password',self.state.path.read_text()+output.getvalue())
        self.assertEqual(self.state.path.stat().st_mode&0o777,0o600);self.assertEqual(self.state.root.stat().st_mode&0o777,0o700)
    def test_noninteractive_login_and_http_refusal_send_nothing(self):
        with self.assertRaises(m.AuthRequired):m.interactive_login(self.state,self.transport,interactive=False)
        with self.assertRaises(m.StoreError):m.Transport(self.base).request('POST','/core/login',data={'password':'dummy'})
        self.assertEqual(self.server.calls,[])
    def test_wrong_login_error_is_redacted(self):
        self.server.reject_login=True;answers=iter(['fixture-user','USER-CODE','q'])
        with contextlib.redirect_stderr(io.StringIO()) as output:
            with self.assertRaises(m.StoreError) as error:m.interactive_login(self.state,self.transport,open_image=False,input_fn=lambda _:next(answers),password_fn=lambda _:'dummy-secret',interactive=True)
        self.assertNotIn('dummy-secret',str(error.exception)+output.getvalue());self.assertFalse(self.state.path.exists())
    def test_redirect_not_followed_or_forwarded(self):
        with self.assertRaises(m.StoreError):self.transport.request('GET','/redirect',token='access-A')
        self.assertEqual(self.server.calls,[('GET','/prod/redirect')])
    def test_token_origin_binding_and_unsafe_cache(self):
        self.login();data=json.loads(self.state.path.read_text());data['base_url']='https://different.test';m.private_json(self.state.path,data)
        with self.assertRaises(m.StoreError):self.state.load()
        m.private_json(self.state.path,{'base_url':self.base,'access_token':'access-A','refresh_token':'refresh-B'});os.chmod(self.state.path,0o644)
        with self.assertRaises(m.StoreError):self.state.load()
    def test_package_rejects_traversal_credentials_and_wrong_support(self):
        for bad in ['../escape','plugin/example/.env','plugin/other/file.php']:
            self.package(bad)
            with self.assertRaises(m.StoreError):m.validate_package(self.zip)
        self.package();self.assertEqual(m.validate_package(self.zip)['app'],'example')
    def test_dry_run_is_offline_and_no_credential_writes(self):
        value=m.upload_version(self.client,self.zip,9,'changes',dry_run=True)
        self.assertTrue(value['dry_run']);self.assertEqual(self.server.calls,[]);self.assertFalse(self.state.root.exists())
    def test_multipart_upload_readback_and_explicit_review_separation(self):
        self.login();value=m.upload_version(self.client,self.zip,9,'changes',kind=3)
        self.assertEqual(value['stage'],'complete');self.assertFalse(value['submit_review'])
        self.assertIn(b'name="file"',self.server.uploaded);self.assertIn(self.zip.read_bytes(),self.server.uploaded)
        self.assertEqual(self.server.upload_headers['Authorization'],'Bearer access-A')
        self.assertEqual(self.server.writes[0][1],{'app_id':9,'version':'1.2.3','type':3,'remark':'changes','file_path':'https://files.example.test/package.zip','status':1})
        self.assertFalse(any('/submitReview' in p for _,p in self.server.calls))
        receipt=Path(value['receipt']);self.assertEqual(receipt.stat().st_mode&0o777,0o600)
        with self.assertRaises(m.StoreError):m.upload_version(self.client,self.zip,9,'changes')
        count=len(self.server.writes);value=m.upload_version(self.client,self.zip,9,'changes',resume=True)
        self.assertTrue(value['resumed']);self.assertEqual(len(self.server.writes),count)
    def test_existing_version_and_wrong_app_do_not_upload(self):
        self.login();self.server.versions=[{'version':'1.2.3','file_path':'other'}]
        with self.assertRaises(m.StoreError):m.upload_version(self.client,self.zip,9,'changes')
        self.server.versions=[];self.package(app='wrong')
        with self.assertRaises(m.StoreError):m.upload_version(self.client,self.zip,9,'changes')
        self.assertFalse(any(p.endswith('/uploadFile') for _,p in self.server.calls))
    def test_version_failure_resumes_without_uploading_again(self):
        self.login();self.server.reject_version=True
        with self.assertRaises(m.StoreError):m.upload_version(self.client,self.zip,9,'changes')
        self.assertEqual(sum(p.endswith('/uploadFile') for _,p in self.server.calls),1)
        self.server.reject_version=False;m.upload_version(self.client,self.zip,9,'changes',resume=True)
        self.assertEqual(sum(p.endswith('/uploadFile') for _,p in self.server.calls),1)
    def test_cli_status_never_prints_tokens(self):
        self.login();r=subprocess.run([sys.executable,str(SCRIPT),'--base-url',self.base,'--config-dir',str(self.state.root),'auth','status'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertNotIn('access-A',r.stdout+r.stderr);self.assertNotIn('refresh-B',r.stdout+r.stderr)
    def test_command_line_password_is_rejected_without_echo(self):
        r=subprocess.run([sys.executable,str(SCRIPT),'--password','dummy-command-secret','auth','login'],capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0);self.assertNotIn('dummy-command-secret',r.stdout+r.stderr)
    def test_uncertain_upload_not_automatically_replayed(self):
        self.login()
        def fail(*a):raise m.UncertainWrite('fixture connection failed')
        self.transport.upload=fail
        with self.assertRaises(m.UncertainWrite):m.upload_version(self.client,self.zip,9,'changes')
        with self.assertRaises(m.StoreError):m.upload_version(self.client,self.zip,9,'changes',resume=True)
        self.assertFalse(any(p.endswith('/addVersion') for _,p in self.server.calls))
    def test_image_upload_refs_and_pair_rotation(self):
        self.login();image=self.root/'logo.png';image.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
        self.assertTrue(m.upload_image(self.client,image,dry_run=True)['dry_run']);self.assertEqual(self.server.calls,[])
        result=m.upload_image(self.client,image)
        self.assertEqual(m.asset_value({'asset_ref':result['asset_ref']},self.root,self.base),self.server.base+'/uploads/logo.png')
        with self.assertRaises(m.StoreError):m.asset_value({'asset_ref':result['asset_ref']},self.root,'https://different.test')
        value=self.state.save('second-user',{'access_token':'new-access','refresh_token':'new-refresh'})
        self.assertEqual(value['refresh_token'],'new-refresh');self.assertNotIn('access-A',self.state.path.read_text())
    def test_create_manifest_and_review_workflow(self):
        self.login();manifest=self.root/'app.json'
        manifest.write_text(json.dumps({'title':'Example','appname':'example','about':'example plugin','logo':'https://files.example.test/logo.png','screenshots':['https://files.example.test/screen.png'],'support':['2'],'content':'# Example'}))
        self.assertTrue(m.create_app(self.client,manifest,dry_run=True)['dry_run']);self.assertEqual(self.server.calls,[])
        self.assertEqual(m.create_app(self.client,manifest)['stage'],'created')
        with contextlib.redirect_stdout(io.StringIO()):m.main(['--base-url',self.base,'--config-dir',str(self.state.root),'--allow-http','--non-interactive','submit-review','--app-id','9'])
        self.assertEqual(self.server.app_status,1)

if __name__=='__main__':unittest.main()
