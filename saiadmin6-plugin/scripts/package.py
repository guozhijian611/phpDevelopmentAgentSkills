#!/usr/bin/env python3
"""Validate a staged SaiAdmin 6 package and optionally create its root-flat ZIP."""
import argparse, configparser, hashlib, json, re, zipfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage');p.add_argument('--frontend',default='saiadmin-artd');p.add_argument('--zip',dest='output');a=p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_-]+',a.frontend) or a.frontend == 'plugin':p.error('Invalid frontend directory')
s=Path(a.stage).resolve(); ini=configparser.ConfigParser(interpolation=None)
ini.read_string('[plugin]\n'+(s/'info.ini').read_text());info=dict(ini['plugin']);app=info.get('app','').strip('"\'')
if not re.fullmatch('[A-Za-z][A-Za-z0-9_]*',app):raise SystemExit('Invalid app')
for k in ['title','about','author','version']:
 if not info.get(k):raise SystemExit('Missing info.ini key '+k)
if not re.fullmatch(r'\d+\.\d+\.\d+',info['version'].strip('"\'')):raise SystemExit('Use a three-component release version')
support=info.get('support','').strip("\"'")
if '6.x' not in [v.strip().lower() for v in support.split('|')]:raise SystemExit('info.ini requires support = 6.x for the SaiAdmin 6 UI')
config=json.loads((s/'config.json').read_text())
if not isinstance(config,dict):raise SystemExit('config.json must be an object')
for k in ['require','require-dev','dependencies','devDependencies']:
 if k in config and not isinstance(config[k],dict):raise SystemExit(k+' must be an object')
allowed={'info.ini','config.json','install.sql','uninstall.sql','update.sql','plugin',a.frontend}
for child in s.iterdir():
 if child.name not in allowed:raise SystemExit('Unexpected root item: '+child.name)
for folder,target in [('plugin',s/'plugin'/app),(a.frontend,s/a.frontend/'src'/'views'/'plugin'/app)]:
 if (s/folder).exists() and not target.is_dir():raise SystemExit('Expected '+str(target))
 if (s/folder).exists():
  for f in (s/folder).rglob('*'):
   if f.is_file() and target not in f.parents:raise SystemExit('File outside plugin-owned directory: '+str(f))
if not (s/'plugin'/app).is_dir() and not (s/a.frontend).is_dir():raise SystemExit('Empty plugin')
files=[]
for f in sorted(s.rglob('*')):
 if f.is_symlink():raise SystemExit('Symlink forbidden: '+str(f))
 if not f.is_file():continue
 if any(x in {'.git','vendor','node_modules','runtime','.DS_Store','__MACOSX'} for x in f.relative_to(s).parts) or f.name.startswith('.env'):raise SystemExit('Excluded artifact: '+str(f))
 files.append(f)
if a.output:
 out=Path(a.output).resolve()
 if out==s or s in out.parents:raise SystemExit('ZIP must be outside stage')
 out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for f in files:z.write(f,f.relative_to(s).as_posix())
 print(json.dumps({'app':app,'files':len(files),'zip':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
else:print(json.dumps({'app':app,'files':len(files),'valid':True}))
