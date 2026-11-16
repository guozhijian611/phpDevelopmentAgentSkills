#!/usr/bin/env python3
"""Create isolated source copies and project-scoped Compose resources. Python stdlib only."""
import argparse, json, os, re, secrets, shutil, subprocess, tempfile
from pathlib import Path
ASSETS=Path(__file__).resolve().parents[1]/"assets"
def run(cmd, **kw): subprocess.run(cmd, check=True, **kw)
def main():
 p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest="action",required=True)
 c=sub.add_parser("create"); c.add_argument("--source",required=True); c.add_argument("--php-image"); c.add_argument("--node-image",default="node:22-bookworm"); c.add_argument("--db-image"); c.add_argument("--db",choices=["mysql","pgsql"],default="mysql"); c.add_argument("--pnpm-version",default="10.11.0")
 c.add_argument("--backend",default="server"); c.add_argument("--frontend",default="saiadmin-artd")
 c.add_argument("--copy-vendor",action="store_true",help="Copy prepared baseline vendor, never plugin runtime or secrets")
 d=sub.add_parser("compose"); d.add_argument("lab"); d.add_argument("args",nargs=argparse.REMAINDER)
 a=p.parse_args()
 if a.action=="compose":
  root=Path(a.lab).resolve(); meta=json.loads((root/"lab.json").read_text())
  if root.name!=meta['project'] or not root.name.startswith('sai6lab-'): raise SystemExit('Invalid lab identity')
  args=a.args; args=args[1:] if args[:1]==['--'] else args
  if not args: raise SystemExit('Compose arguments required')
  if any(x in args for x in ['-p','--project-name','-f','--file','--project-directory']): raise SystemExit('Do not override lab scope')
  run(['docker','compose','--project-name',meta['project'],'--project-directory',str(root),'-f',str(root/'compose.json'),*args]); return
 src=Path(a.source).resolve()
 for name in [a.backend,a.frontend]:
  if not re.fullmatch(r'[A-Za-z0-9_-]+',name) or not (src/name).is_dir(): raise SystemExit('Invalid source directory: '+name)
 if a.backend == a.frontend: raise SystemExit('Backend and frontend must differ')
 if not (src/a.backend/'composer.json').exists(): raise SystemExit('Missing composer.json')
 req=json.loads((src/a.backend/'composer.json').read_text()).get('require',{})
 if 'saithink/saiadmin' not in req: raise SystemExit('Verify SaiAdmin 6 baseline before creating lab')
 lock=src/a.backend/'composer.lock'
 if a.copy_vendor and (not lock.exists() or not (src/a.backend/'vendor/autoload.php').is_file()): raise SystemExit('--copy-vendor requires composer.lock and vendor/autoload.php')
 if lock.exists():
  versions={x['name']:x['version'] for x in json.loads(lock.read_text()).get('packages',[])}
  for package in ['saithink/saiadmin','saithink/saipackage']:
   if not versions.get(package,'').lstrip('v').startswith('6.'): raise SystemExit('Expected locked 6.x package: '+package)
 if not re.fullmatch(r'\d+\.\d+\.\d+',a.pnpm_version): raise SystemExit('pnpm version must be exact x.y.z')
 root=Path(tempfile.mkdtemp(prefix='sai6lab-')); project=root.name
 def ignore(directory,names):
  excluded={'.git','node_modules','runtime','.DS_Store'}
  if not a.copy_vendor: excluded.add('vendor')
  if Path(directory)==src/a.backend: excluded.add('.env')
  return set(names)&excluded
 app=root/'app'; app.mkdir()
 for name in [a.backend,a.frontend]: shutil.copytree(src/name,app/name,ignore=ignore,symlinks=False)
 # Backend runtime and credentials are deliberately fresh. Frontend public Vite settings are retained.
 secret=secrets.token_hex(16)
 env={'DB_TYPE':a.db,'DB_HOST':'db','DB_PORT':'3306','DB_NAME':'saiadmin','DB_USER':'root','DB_PASSWORD':secret,'DB_PREFIX':'','DB_CHARSET':'utf8mb4','CACHE_MODE':'file','REDIS_HOST':'redis','REDIS_PORT':'6379','REDIS_PASSWORD':'','REDIS_DB':'0','CAPTCHA_MODE':'cache','FRONTEND_DIR':a.frontend}
 if a.db=='pgsql': env.update(DB_PORT='5432',DB_USER='postgres',DB_CHARSET='utf8',DB_SCHEMA='public')
 # .env file itself is left absent for the core installation wizard.
 (root/'db-secret').write_text(secret); os.chmod(root/'db-secret',0o600)
 (root/'backend-env.json').write_text(json.dumps(env,indent=2)); os.chmod(root/'backend-env.json',0o600)
 shutil.copy(ASSETS/'Dockerfile',root/'Dockerfile')
 (root/'.dockerignore').write_text('app/\n*.json\ndb-secret\n')
 php={'image':a.php_image} if a.php_image else {'build':{'context':'.'},'image':project+'-php'}
 backend={**php,'working_dir':'/app/'+a.backend,'volumes':['./app:/app'],'environment':env,'entrypoint':['docker-php-entrypoint'],'command':['php','start.php','start'],'ports':['127.0.0.1::8787'],'depends_on':{'db':{'condition':'service_healthy'},'redis':{'condition':'service_started'}}}
 compose={'services':{'db':{'image':a.db_image or 'mysql:8.4','environment':{'MYSQL_ROOT_PASSWORD':secret,'MYSQL_DATABASE':'saiadmin'},'volumes':['db:/var/lib/mysql'],'healthcheck':{'test':['CMD-SHELL','MYSQL_PWD="$$MYSQL_ROOT_PASSWORD" mysqladmin ping -h 127.0.0.1 -uroot --silent'],'interval':'3s','timeout':'3s','retries':40}},'redis':{'image':'redis:8-alpine'},'backend':backend,'frontend':{'image':a.node_image,'working_dir':'/app/'+a.frontend,'volumes':['./app:/app','node_modules:/app/'+a.frontend+'/node_modules','pnpm:/pnpm'],'environment':{'VITE_API_PROXY_URL':'http://backend:8787','VITE_PORT':'3006','PNPM_HOME':'/pnpm'},'command':['sh','-lc','corepack enable && corepack prepare pnpm@'+a.pnpm_version+' --activate && pnpm install --frozen-lockfile && pnpm exec vite --host 0.0.0.0 --port 3006 --strictPort'],'ports':['127.0.0.1::3006']}},'volumes':{'db':{},'node_modules':{},'pnpm':{}}}
 if a.db=='pgsql':
  compose['services']['db']={'image':a.db_image or 'postgres:17-alpine','environment':{'POSTGRES_PASSWORD':secret,'POSTGRES_DB':'saiadmin'},'volumes':['db:/var/lib/postgresql/data'],'healthcheck':{'test':['CMD-SHELL','pg_isready -h 127.0.0.1 -U postgres -d saiadmin'],'interval':'3s','timeout':'3s','retries':40}}
 (root/'compose.json').write_text(json.dumps(compose,indent=2));os.chmod(root/'compose.json',0o600)
 (root/'lab.json').write_text(json.dumps({'project':project,'source':str(src),'backend':a.backend,'frontend':a.frontend,'db':a.db},indent=2))
 print(root)
if __name__=='__main__': main()
