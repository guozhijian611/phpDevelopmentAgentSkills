#!/usr/bin/env python3
"""Interactive SaiStore developer client. Python stdlib only; never stores passwords."""
from __future__ import annotations
import argparse, base64, configparser, getpass, hashlib, json, mimetypes, os, re, secrets
import stat, sys, tempfile, time, ssl, http.cookiejar, urllib.error, urllib.parse, urllib.request, webbrowser, zipfile
from pathlib import Path

DEFAULT_BASE = 'http://manage.saithink.top/prod'
APP = '/app/saistore/admin/develop/StoreApp/'
MAX_UPLOAD = 10 * 1024 * 1024  # Observed SaFileUpload default: strictly below 10 MiB.

class StoreError(Exception): pass
class AuthRequired(StoreError): pass
class UncertainWrite(StoreError): pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

def normalize_base(value):
    u=urllib.parse.urlsplit(value)
    if u.scheme not in ('http','https') or not u.hostname or u.username or u.password or u.query or u.fragment:
        raise StoreError('API 地址必须为不含账号、查询参数或 fragment 的 HTTP(S) 地址')
    if not re.fullmatch(r'(?:/[A-Za-z0-9_-]+)*/*',u.path): raise StoreError('无效的 API 前缀')
    return urllib.parse.urlunsplit((u.scheme,u.netloc.lower(),u.path.rstrip('/'),'',''))

def private_json(path, value):
    path=Path(path)
    if path.is_symlink() or path.parent.is_symlink(): raise StoreError('本地状态不能是符号链接')
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True);os.chmod(path.parent,0o700)
    fd,temp=tempfile.mkstemp(prefix='.saistore-',dir=path.parent)
    try:
        os.chmod(temp,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def read_private(path):
    path=Path(path)
    if path.is_symlink():raise StoreError('拒绝读取符号链接状态文件')
    if not path.exists():return None
    if path.stat().st_size>2*1024*1024:raise StoreError('本地状态文件过大')
    if os.name!='nt' and stat.S_IMODE(path.stat().st_mode)&0o077:raise StoreError('本地状态权限过宽，请先 chmod 600 '+str(path))
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict):raise StoreError('本地状态必须为 JSON 对象')
    return value

class State:
    def __init__(self, root, base):
        self.root=Path(root).expanduser();self.base=normalize_base(base)
        self.key=hashlib.sha256(self.base.encode()).hexdigest()[:24]
        self.path=self.root/(self.key+'.json')
    def load(self):
        value=read_private(self.path)
        if value and value.get('base_url')!=self.base:raise StoreError('令牌与目标站点不匹配')
        if value:
            if not isinstance(value.get('access_token'),str) or not isinstance(value.get('refresh_token',''),str):raise StoreError('本地令牌格式错误')
            if value.get('expires_at') is not None and not isinstance(value['expires_at'],(int,float)):raise StoreError('本地令牌时间格式错误')
        return value or {}
    def save(self, username, data):
        if not isinstance(data,dict) or not isinstance(data.get('access_token'),str) or not data['access_token']:
            raise StoreError('登录没有返回 access_token，未保存假成功')
        refresh=data.get('refresh_token')
        if refresh is not None and not isinstance(refresh,str):raise StoreError('refresh_token 格式变化，停止处理')
        expiry=None
        if isinstance(data.get('expires_in'),(int,float)) and data['expires_in']>0:expiry=time.time()+data['expires_in']
        else:
            try:expiry=float(json.loads(base64.urlsafe_b64decode(data['access_token'].split('.')[1]+'==='))['exp'])
            except (ValueError,KeyError,IndexError,TypeError):pass
        value={'base_url':self.base,'username':username,'access_token':data['access_token'],'refresh_token':refresh or '',
               'saved_at':time.time(),'expires_at':expiry}
        private_json(self.path,value);return value
    def receipt_path(self, app_id, digest):return self.root/'receipts'/(self.key+'-'+str(app_id)+'-'+digest+'.json')

class Transport:
    def __init__(self, base, allow_http=False, timeout=30):
        self.base=normalize_base(base);self.allow_http=allow_http;self.timeout=timeout
        self.opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.secrets=[]
    def redact(self,value):
        value=str(value)
        for secret in sorted(filter(None,self.secrets),key=len,reverse=True):value=value.replace(secret,'[已隐藏]')
        value=re.sub(r'(?i)(bearer\s+)[A-Za-z0-9_.~+/-]+',r'\1[已隐藏]',value)
        return re.sub(r'(?i)((?:access_token|refresh_token|password|api_key)\s*[:=]\s*)[^\s,;]+',r'\1[已隐藏]',value)[:300]
    def request(self,method,path,data=None,token=None,body=None,headers=None):
        if urllib.parse.urlsplit(self.base).scheme=='http' and not self.allow_http:
            raise StoreError('该 API 为 HTTP，账号/令牌会明文传输；确认接受后显式添加 --allow-http。不会自动关闭 HTTPS 证书校验')
        if not path.startswith('/') or path.startswith('//') or '\\' in path:raise StoreError('接口路径必须留在当前 API 站点')
        request_headers={'Accept':'application/json'}
        if token:
            if '\r' in token or '\n' in token:raise StoreError('令牌格式不正确')
            request_headers['Authorization']='Bearer '+token;self.secrets.append(token)
        request_headers.update(headers or {})
        if data is not None:
            body=json.dumps(data,ensure_ascii=False).encode();request_headers['Content-Type']='application/json'
        req=urllib.request.Request(self.base+path,data=body,method=method,headers=request_headers)
        try:
            response=self.opener.open(req,timeout=self.timeout)
            raw=response.read(2*1024*1024+1)
        except urllib.error.HTTPError as e:
            if e.code==401:raise AuthRequired('登录已过期，请重新登录') from None
            # Never expose raw HTML, redirects, headers or credential-bearing URLs.
            raise StoreError('HTTP '+str(e.code)+'；未自动重试或跟随重定向') from None
        except (urllib.error.URLError,TimeoutError,OSError) as e:
            if isinstance(getattr(e,'reason',None),ssl.SSLCertVerificationError):raise StoreError('HTTPS 证书校验失败，未绕过校验；请核对域名和服务端证书') from None
            message='连接失败（证书、网络或超时），未自动重试'
            if method not in ('GET','HEAD'):raise UncertainWrite(message+'；写入结果未知，先查询远端状态') from None
            raise StoreError(message) from None
        if len(raw)>2*1024*1024:raise StoreError('接口响应过大')
        try:envelope=json.loads(raw)
        except (ValueError,UnicodeError):raise StoreError('接口没有返回预期 JSON，未输出原始响应') from None
        if not isinstance(envelope,dict) or 'code' not in envelope:raise StoreError('接口响应契约变化')
        if envelope['code']==401:raise AuthRequired('登录已过期，请重新登录')
        if envelope['code']!=200:raise StoreError('接口拒绝：'+self.redact(envelope.get('message','请求失败')))
        return envelope.get('data')
    def upload(self,path,file,token):
        file=Path(file);boundary='saistore-'+secrets.token_hex(16)
        filename=file.name.replace('"','_').replace('\r','_').replace('\n','_')
        mime=mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        head=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: {mime}\r\n\r\n').encode()
        tail=f'\r\n--{boundary}--\r\n'.encode()
        def chunks():
            yield head
            with file.open('rb') as stream:
                while True:
                    block=stream.read(128*1024)
                    if not block:break
                    yield block
            yield tail
        result=self.request('POST',path,token=token,body=chunks(),headers={'Content-Type':'multipart/form-data; boundary='+boundary,'Content-Length':str(len(head)+file.stat().st_size+len(tail))})
        # Same response shapes accepted by the observed SaFileUpload component.
        value=result
        if isinstance(value,dict):value=value.get('data',value)
        if isinstance(value,dict):value=value.get('url')
        if not isinstance(value,str) or not value or len(value)>8192:raise StoreError('上传未返回可识别文件地址；停止后续写入，先检查远端资源')
        parsed=urllib.parse.urlsplit(value)
        if parsed.scheme not in ('','http','https') or parsed.username or parsed.password or any(ord(c)<32 for c in value):raise StoreError('上传返回了不安全的文件地址，未继续写入')
        return value

def interactive_login(state, transport, username=None, open_image=True, input_fn=input, password_fn=getpass.getpass, interactive=None):
    if interactive is None:interactive=sys.stdin.isatty() and sys.stderr.isatty()
    if not interactive:raise AuthRequired('需要交互式登录。请在本机终端运行 auth login；不要在聊天、命令参数或环境变量中提供密码')
    username=username or input_fn('用户名：').strip()
    if not username:raise StoreError('用户名不能为空')
    # Validate transport/captcha before prompting for the secret.
    for attempt in range(3):
        captcha=transport.request('GET','/core/captcha')
        if not isinstance(captcha,dict) or not captcha.get('uuid') or not isinstance(captcha.get('image'),str):raise StoreError('验证码响应契约变化')
        match=re.fullmatch(r'data:image/(png|jpeg|gif);base64,([A-Za-z0-9+/=\r\n]+)',captcha['image'])
        if not match:raise StoreError('验证码不是支持的图片格式')
        try:image=base64.b64decode(match[2],validate=True)
        except ValueError:raise StoreError('验证码图片编码不正确') from None
        magic={'png':b'\x89PNG\r\n\x1a\n','jpeg':b'\xff\xd8\xff','gif':b'GIF8'}[match[1]]
        if len(image)>2*1024*1024 or not image.startswith(magic):raise StoreError('验证码图片格式或大小不正确')
        with tempfile.TemporaryDirectory(prefix='saistore-captcha-') as temp:
            os.chmod(temp,0o700);path=Path(temp)/('captcha.'+match[1]);path.write_bytes(image);os.chmod(path,0o600)
            print('请查看验证码图片：'+str(path),file=sys.stderr)
            if open_image:webbrowser.open(path.as_uri())
            code=input_fn('验证码（输入 r 刷新，q 取消）：').strip()
            if code.lower()=='q':raise StoreError('已取消登录')
            if code.lower()=='r':continue
            password=password_fn('密码（不回显、不保存）：')
            if not password or not code:raise StoreError('密码和验证码不能为空')
            transport.secrets.append(password)
            try:
                result=transport.request('POST','/core/login',data={'username':username,'password':password,'code':code,'uuid':captcha['uuid']})
                if isinstance(result,dict):transport.secrets.extend([result.get('access_token',''),result.get('refresh_token','')])
                saved=state.save(username,result)
                print('登录成功，访问令牌已保存；'+('刷新令牌已保存。' if saved['refresh_token'] else '服务未返回刷新令牌。')+'密码未保存。',file=sys.stderr)
                return saved
            except StoreError as error:
                print('登录未成功：'+transport.redact(error),file=sys.stderr)
                if attempt==2 or input_fn('登录失败。输入 r 获取新验证码后重试，其它输入停止：').strip().lower()!='r':raise
            finally:
                transport.secrets=[v for v in transport.secrets if v!=password];password=''
    raise StoreError('本次验证码/登录尝试已达上限，请稍后重新运行')

class Client:
    def __init__(self,state,transport,non_interactive=False,no_open=False):
        self.state=state;self.transport=transport;self.non_interactive=non_interactive;self.no_open=no_open
    def token(self):
        value=self.state.load()
        if not value.get('access_token') or (value.get('expires_at') and value['expires_at']<=time.time()+15):
            if self.non_interactive:raise AuthRequired('未登录或令牌过期，请先在终端运行 auth login')
            value=interactive_login(self.state,self.transport,value.get('username'),not self.no_open)
        self.transport.secrets.extend([value.get('access_token',''),value.get('refresh_token','')])
        return value['access_token']
    def call(self,method,path,data=None):
        # Never replay an ambiguous write. Only a read may renew a rejected login once.
        try:return self.transport.request(method,path,data=data,token=self.token())
        except AuthRequired:
            if method!='GET' or self.non_interactive:raise
            value=self.state.load();interactive_login(self.state,self.transport,value.get('username'),not self.no_open)
            return self.transport.request(method,path,data=data,token=self.token())
    def app(self,app_id):
        data=self.call('GET',APP+'read?'+urllib.parse.urlencode({'id':app_id}))
        if not isinstance(data,dict) or str(data.get('id'))!=str(app_id) or not data.get('appname'):raise StoreError('应用详情响应不匹配')
        return data
    def versions(self,app_id):
        data=self.call('GET',APP+'versionList?'+urllib.parse.urlencode({'app_id':app_id}))
        if not isinstance(data,list):raise StoreError('版本列表响应契约变化')
        return data
    def apps(self,keywords=''):
        data=self.call('GET',APP+'index?'+urllib.parse.urlencode({'page':1,'limit':100,'keywords':keywords}))
        if not isinstance(data,dict) or not isinstance(data.get('data'),list):raise StoreError('应用列表响应契约变化')
        return data

def validate_package(path,frontend='saiadmin-artd'):
    path=Path(path).resolve()
    if path.suffix.lower()!='.zip' or not path.is_file() or path.stat().st_size>=MAX_UPLOAD:raise StoreError('ZIP 必须存在且小于后台控件的 10 MiB 限制')
    if not re.fullmatch(r'[A-Za-z0-9_-]+',frontend):raise StoreError('无效前端目录')
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist();names=[i.filename for i in entries]
        if len(entries)>10000 or len(names)!=len(set(names)) or sum(i.file_size for i in entries)>512*1024*1024:raise StoreError('ZIP 条目重复或解压规模过大')
        for i in entries:
            parts=i.filename.rstrip('/').split('/')
            if i.filename.startswith('/') or '\\' in i.filename or any(p in ('','..','.') for p in parts) or stat.S_ISLNK(i.external_attr>>16) or i.flag_bits&1:raise StoreError('ZIP 含越界或符号链接路径')
            if any(p in ('.git','vendor','node_modules','runtime','__pycache__') or p.startswith('.env') for p in parts):raise StoreError('ZIP 含运行目录、依赖或环境凭据')
        if 'info.ini' not in names or 'config.json' not in names:raise StoreError('ZIP 根层缺少 info.ini/config.json')
        if archive.getinfo('info.ini').file_size>65536 or archive.getinfo('config.json').file_size>1024*1024:raise StoreError('包元数据过大')
        ini=configparser.ConfigParser(interpolation=None);ini.read_string('[plugin]\n'+archive.read('info.ini').decode('utf-8-sig'));info=dict(ini['plugin'])
        app=info.get('app','').strip('"\'');version=info.get('version','').strip('"\'');support=info.get('support','').strip('"\'')
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',app) or not re.fullmatch(r'\d+\.\d+\.\d+',version):raise StoreError('app 或三段版本号不合法')
        if any(not info.get(k,'').strip() for k in ('title','about','author')):raise StoreError('info.ini 缺少 title/about/author')
        if '6.x' not in [x.strip().lower() for x in support.split('|')]:raise StoreError('本 skill 只上传声明支持 SaiAdmin 6.x 的插件')
        config=json.loads(archive.read('config.json'))
        if not isinstance(config,dict) or any(k in config and not isinstance(config[k],dict) for k in ('require','require-dev','dependencies','devDependencies')):raise StoreError('config.json 或依赖字段格式错误')
        allowed={'info.ini','config.json','install.sql','uninstall.sql','update.sql'};payload=False
        for i in entries:
            if i.is_dir():continue
            n=i.filename
            if n in allowed:continue
            if not (n.startswith('plugin/'+app+'/') or n.startswith(frontend+'/src/views/plugin/'+app+'/')):raise StoreError('ZIP 含非插件拥有的路径：'+n)
            payload=True
        if not payload or archive.testzip():raise StoreError('ZIP 为空或 CRC 校验失败')
    return {'path':str(path),'app':app,'version':version,'size':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def upload_version(client,package,app_id,notes,kind=3,resume=False,dry_run=False,frontend='saiadmin-artd'):
    info=validate_package(package,frontend)
    if not notes.strip():raise StoreError('更新日志不能为空')
    plan={'app_id':app_id,'appname':info['app'],'version':info['version'],'type':kind,'sha256':info['sha256'],'bytes':info['size'],'submit_review':False}
    if dry_run:return {'dry_run':True,**plan}
    app=client.app(app_id)
    if app['appname']!=info['app']:raise StoreError('ZIP app 与远端应用标识不一致，未上传')
    versions=client.versions(app_id)
    receipt_path=client.state.receipt_path(app_id,info['sha256']);receipt=read_private(receipt_path)
    if receipt:
        if any(receipt.get(k)!=v for k,v in {'base_url':client.state.base,'app_id':app_id,'appname':info['app'],'version':info['version'],'sha256':info['sha256']}.items()):raise StoreError('上传回执与当前任务不匹配')
        if not resume:raise StoreError('该包已有回执，请核对后使用 --resume，避免重复写入')
    existing=[v for v in versions if str(v.get('version'))==info['version']]
    if existing:
        if receipt and resume and len(existing)==1 and existing[0].get('file_path')==receipt.get('file_path'):
            receipt['stage']='complete';private_json(receipt_path,receipt)
            return {'stage':'complete','resumed':True,'version':info['version'],'app_id':app_id,'receipt':str(receipt_path)}
        raise StoreError('远端已有同版本，未重复上传或覆盖')
    if receipt and receipt.get('stage') not in ('file-uploaded',):raise StoreError('之前上传结果未知，不能自动重放；请先在后台检查资源和版本')
    if not receipt:
        token=client.token()
        if hashlib.sha256(Path(info['path']).read_bytes()).hexdigest()!=info['sha256']:raise StoreError('ZIP 在预检后发生变化，停止上传')
        receipt={'base_url':client.state.base,**plan,'stage':'upload-unknown','created_at':time.time()}
        private_json(receipt_path,receipt)
        file_path=client.transport.upload(APP+'uploadFile',info['path'],token)
        receipt.update(file_path=file_path,stage='file-uploaded');private_json(receipt_path,receipt)
    client.call('POST',APP+'addVersion',{'app_id':app_id,'version':info['version'],'type':kind,'remark':notes,'file_path':receipt['file_path'],'status':1})
    observed=client.versions(app_id)
    if not any(str(v.get('version'))==info['version'] and v.get('file_path')==receipt['file_path'] for v in observed):raise StoreError('版本尚未读回确认；回执已保留，请稍后核对并 --resume')
    receipt['stage']='complete';private_json(receipt_path,receipt)
    return {'stage':'complete','app_id':app_id,'version':info['version'],'sha256':info['sha256'],'receipt':str(receipt_path),'submit_review':False}

def upload_image(client,file,dry_run=False):
    file=Path(file).resolve()
    if not file.is_file() or file.stat().st_size>=5*1024*1024:raise StoreError('图片必须存在且小于 5 MiB')
    content=file.read_bytes();suffix=file.suffix.lower()
    good=(suffix=='.png' and content.startswith(b'\x89PNG\r\n\x1a\n')) or (suffix in ('.jpg','.jpeg') and content.startswith(b'\xff\xd8\xff')) or (suffix=='.gif' and content.startswith(b'GIF8')) or (suffix=='.webp' and content.startswith(b'RIFF') and content[8:12]==b'WEBP')
    if not good:raise StoreError('只上传签名与扩展名匹配的 PNG/JPEG/GIF/WebP 图片')
    digest=hashlib.sha256(content).hexdigest()
    if dry_run:return {'dry_run':True,'operation':'upload-image','sha256':digest,'bytes':len(content)}
    token=client.token()
    url=client.transport.upload('/core/system/uploadImage',file,token)
    origin=urllib.parse.urlsplit(client.state.base)
    url=urllib.parse.urljoin(urllib.parse.urlunsplit((origin.scheme,origin.netloc,'/','','')),url)
    ref=client.state.root/'assets'/(client.state.key+'-'+digest+'.json')
    private_json(ref,{'base_url':client.state.base,'kind':'image','sha256':digest,'url':url})
    return {'asset_ref':str(ref),'sha256':digest,'url_saved':True}

def asset_value(value,folder,base):
    if isinstance(value,dict) and set(value)=={'asset_ref'}:
        path=Path(value['asset_ref']).expanduser()
        value=read_private(path if path.is_absolute() else folder/path)
        if not value or value.get('base_url')!=base or value.get('kind')!='image':raise StoreError('图片回执与当前站点不匹配')
        return value.get('url')
    return value

def create_app(client,manifest,dry_run=False):
    manifest=Path(manifest).resolve();data=json.loads(manifest.read_text(encoding='utf-8'))
    if isinstance(data,dict):
        data['logo']=asset_value(data.get('logo'),manifest.parent,client.state.base)
        if isinstance(data.get('screenshots'),list):data['screenshots']=[asset_value(v,manifest.parent,client.state.base) for v in data['screenshots']]
    required=('title','appname','about','logo','screenshots','support','content')
    if not isinstance(data,dict) or any(not data.get(k) for k in required):raise StoreError('应用清单缺少名称、标识、简介、图标、截图、版本支持或文档')
    if any(not isinstance(data[k],str) for k in ('title','appname','about','logo','content')):raise StoreError('应用文本字段必须是字符串')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',data['appname']):raise StoreError('无效应用标识')
    if not isinstance(data['screenshots'],list) or not 1<=len(data['screenshots'])<=8 or not isinstance(data['support'],list) or '2' not in list(map(str,data['support'])):raise StoreError('需要 1–8 张截图并选择 SaiAdmin 6.x（支持值 2）')
    for asset in [data['logo'],*data['screenshots']]:
        if not isinstance(asset,str) or urllib.parse.urlsplit(asset).scheme not in ('http','https') or not urllib.parse.urlsplit(asset).hostname:raise StoreError('图标和截图需使用已上传的 HTTP(S) 资源 URL')
    allowed=set(required)|{'type','price','total_price','status'}
    if set(data)-allowed:raise StoreError('应用清单含未支持字段')
    payload={'type':1,'price':0,'total_price':0,'status':1,**data}
    if payload['type']!=1 or any(isinstance(payload[k],bool) or not isinstance(payload[k],(int,float)) or payload[k]<0 for k in ('price','total_price')):raise StoreError('应用必须是安装插件，价格必须为非负数')
    if dry_run:return {'dry_run':True,'operation':'create-app','appname':payload['appname'],'support':payload['support']}
    listed=client.apps(payload['appname'])
    if any(r.get('appname')==payload['appname'] for r in listed['data']):raise StoreError('已有同标识应用，请使用其 ID，不重复创建')
    if int(listed.get('total',len(listed['data'])))>len(listed['data']):raise StoreError('同名检索结果分页未完整，请先核对应用 ID，不自动创建')
    client.call('POST',APP+'save',payload)
    return {'stage':'created','appname':payload['appname'],'message':'请通过 apps list 核对应用 ID 后上传版本；未提交审核'}

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-url',default=DEFAULT_BASE);p.add_argument('--allow-http',action='store_true',help='明确接受当前站点 HTTP 明文传输风险；不关闭 HTTPS 校验')
    p.add_argument('--config-dir',type=Path,default=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'saiadmin6-plugin'/'saistore')
    p.add_argument('--non-interactive',action='store_true');p.add_argument('--no-open-captcha',action='store_true')
    sub=p.add_subparsers(dest='group',required=True)
    auth=sub.add_parser('auth').add_subparsers(dest='action',required=True)
    auth.add_parser('login').add_argument('--username');auth.add_parser('status');auth.add_parser('logout')
    apps=sub.add_parser('apps').add_subparsers(dest='action',required=True)
    apps.add_parser('list').add_argument('--keywords',default='')
    apps.add_parser('read').add_argument('--app-id',type=int,required=True)
    create=apps.add_parser('create');create.add_argument('--manifest',type=Path,required=True);create.add_argument('--dry-run',action='store_true')
    image=sub.add_parser('asset-upload');image.add_argument('--file',type=Path,required=True);image.add_argument('--dry-run',action='store_true')
    upload=sub.add_parser('upload');upload.add_argument('--zip',type=Path,required=True);upload.add_argument('--app-id',type=int,required=True)
    upload.add_argument('--notes-file',type=Path,required=True);upload.add_argument('--kind',choices=('major','feature','fix'),default='fix')
    upload.add_argument('--dry-run',action='store_true');upload.add_argument('--resume',action='store_true');upload.add_argument('--frontend',default='saiadmin-artd')
    review=sub.add_parser('submit-review');review.add_argument('--app-id',type=int,required=True);review.add_argument('--dry-run',action='store_true')
    return p

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if any(a.split('=',1)[0] in ('--password','--access-token','--refresh-token','--token') for a in argv):raise StoreError('不接受命令行密码或令牌；请使用交互式 auth login')
    args=parser().parse_args(argv)
    state=State(args.config_dir,args.base_url);transport=Transport(state.base,args.allow_http)
    client=Client(state,transport,args.non_interactive,args.no_open_captcha)
    if hasattr(args,'app_id') and args.app_id<1:raise StoreError('应用 ID 必须为正整数')
    if args.group=='auth':
        if args.action=='login':
            if args.non_interactive:raise StoreError('登录必须在交互终端输入密码和验证码')
            saved=interactive_login(state,transport,args.username,not args.no_open_captcha)
            output={'logged_in':True,'refresh_token_saved':bool(saved['refresh_token']),'state_file':str(state.path),'refresh_endpoint_verified':False}
        elif args.action=='logout':
            state.load()
            if state.path.exists():state.path.unlink()
            output={'local_session_removed':True,'server_revoked':False}
        else:
            data=state.load();output={'base_url':state.base,'username':data.get('username'),'access_token_saved':bool(data.get('access_token')),'refresh_token_saved':bool(data.get('refresh_token')),'expires_at':data.get('expires_at'),'state_file':str(state.path),'refresh_endpoint_verified':False}
    elif args.group=='apps':
        if args.action=='create':output=create_app(client,args.manifest,args.dry_run)
        elif args.action=='read':
            row=client.app(args.app_id);output={k:row.get(k) for k in ('id','title','appname','app_status','status','support')}
        else:
            data=client.apps(args.keywords);output={'total':data.get('total'),'data':[{k:r.get(k) for k in ('id','title','appname','app_status')} for r in data['data']]}
    elif args.group=='asset-upload':output=upload_image(client,args.file,args.dry_run)
    elif args.group=='upload':output=upload_version(client,args.zip,args.app_id,args.notes_file.read_text(encoding='utf-8'),{'major':1,'feature':2,'fix':3}[args.kind],args.resume,args.dry_run,args.frontend)
    else:
        if args.dry_run:output={'dry_run':True,'operation':'submit-review','app_id':args.app_id}
        else:
            row=client.app(args.app_id)
            if row.get('app_status')!=0:raise StoreError('应用不是草稿状态；未重复提交审核')
            client.call('POST',APP+'submitReview',{'id':args.app_id});observed=client.app(args.app_id)
            if observed.get('app_status')!=1:raise StoreError('尚未读回待审核状态，请先核对，不自动重试')
            output={'app_id':args.app_id,'app_status':1,'submitted_for_review':True,'approved':False}
    print(json.dumps(output,ensure_ascii=False,indent=2));return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (StoreError,OSError,ValueError,zipfile.BadZipFile,EOFError,KeyboardInterrupt) as error:
        # Known error messages never include request bodies or raw credentials.
        print('错误：'+str(error),file=sys.stderr);raise SystemExit(1)
