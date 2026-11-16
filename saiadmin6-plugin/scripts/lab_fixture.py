"""Shared local-only transport for disposable fixture commands; not an application dependency."""
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

class Lab:
    def __init__(self, path):
        self.root=Path(path).resolve();self.meta=json.loads((self.root/'lab.json').read_text())
        if self.root.name!=self.meta['project'] or not self.root.name.startswith('sai6lab-'):raise ValueError('Invalid lab identity')
        for key in ['backend','frontend']:
            if not re.fullmatch(r'[A-Za-z0-9_-]+',self.meta[key]):raise ValueError('Invalid lab directory')
        if self.meta['db'] not in ['mysql','pgsql']:raise ValueError('Unsupported fixture database')
        self.server=self.root/'app'/self.meta['backend'];self.url=None

    def compose(self,*args):
        r=subprocess.run([sys.executable,str(Path(__file__).with_name('lab.py')),'compose',str(self.root),*map(str,args)],capture_output=True,text=True)
        if r.returncode:
            log=self.root/'fixture-command-error.log';log.write_text(r.stdout + r.stderr);log.chmod(0o600)
            raise RuntimeError('Lab command failed; inspect private diagnostic: '+str(log))
        return r.stdout

    def refresh_url(self):
        address=self.compose('port','backend','8787').strip()
        if not re.fullmatch(r'127\.0\.0\.1:\d+',address):raise ValueError('Only loopback fixture endpoints are accepted')
        self.url='http://'+address
        return self.url

    def token(self):return (self.root/'http-token').read_text().strip()

    def request(self,path,data=None,token=None,method=None,package=None):
        if not path.startswith('/') or path.startswith('//'):raise ValueError('Expected local API path')
        headers={}
        if token:headers['Authorization']='Bearer '+token
        if package is not None:
            boundary='sai6fixture-'+uuid.uuid4().hex;headers['Content-Type']='multipart/form-data; boundary='+boundary
            data=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="fixture.zip"\r\nContent-Type: application/zip\r\n\r\n').encode()+Path(package).read_bytes()+f'\r\n--{boundary}--\r\n'.encode()
        elif data is not None:headers['Content-Type']='application/json';data=json.dumps(data).encode()
        if self.url is None:self.refresh_url()
        request=urllib.request.Request(self.url+path,data=data,headers=headers,method=method)
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):raise RuntimeError('Fixture redirect refused')
        try:response=urllib.request.build_opener(NoRedirect).open(request,timeout=90)
        except urllib.error.HTTPError as error:response=error
        try:return json.load(response)
        except json.JSONDecodeError:raise RuntimeError('Non-JSON fixture response: '+path) from None

    def wait(self,path='/core/system/user',authenticated=True,attempts=50):
        self.refresh_url()
        for _ in range(attempts):
            try:
                if authenticated:
                    result=self.request(path,token=self.token())
                    if result.get('code')==200:return
                    if result.get('code')==401:raise ValueError('Fixture session expired; do not retry writes')
                else:
                    urllib.request.urlopen(self.url+path,timeout=2).close();return
            except (OSError,RuntimeError):pass
            time.sleep(.3)
        raise RuntimeError('Host readiness timed out; no write was retried')
