#!/usr/bin/env python3
"""Offline repository checks; no panel/production connection or installer execution."""
import argparse, ast, hashlib, json, os, re, subprocess, sys
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--skip-docker',action='store_true');a=p.parse_args()
def run(args):
    r=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    if r.returncode:raise RuntimeError('Command failed: '+str(args)+'\n'+r.stdout+r.stderr)
    return r.stdout

def main():
    if (ROOT/'.git').exists():
        entries=run(['git','ls-files','--stage','-z']).split('\0')
        links={item.split('\t',1)[1] for item in entries if item.startswith('160000 ')}
        configured=run(['git','config','-f','.gitmodules','--get-regexp',r'^submodule\..*\.path$'])
        paths={line.split(maxsplit=1)[1] for line in configured.splitlines()}
        assert links==paths,'Gitlinks and .gitmodules paths must match'
    skills=sorted(ROOT.glob('*/SKILL.md'))+sorted((ROOT/'btpanel/assets').rglob('SKILL.md'))
    allowed={'name','description','metadata','license','allowed-tools'}
    for f in skills:
        value=f.read_text();match=re.match(r'^---\n(.*?)\n---\n',value,re.S);assert match,f
        data=yaml.safe_load(match[1]);assert isinstance(data,dict) and set(data)<=allowed,f
        assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',data['name']) and len(data['name'])<=64,f
        assert data['name']==f.parent.name and isinstance(data.get('description'),str) and data['description'],f
    for directory in [f.parent for f in ROOT.glob('*/SKILL.md')]:
        for f in directory.rglob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)',f.read_text()):
                if '://' not in target and not target.startswith('#'):
                    assert (f.parent/target.split('#')[0]).exists(),(f,target)
        metadata=directory/'agents/openai.yaml'
        if metadata.exists():
            ui=yaml.safe_load(metadata.read_text())['interface'];assert '$'+directory.name in ui['default_prompt'],metadata
            assert 25<=len(ui['short_description'])<=64,metadata
    for target in re.findall(r'\]\(([^)]+)\)',(ROOT/'readme.md').read_text()):
        if '://' not in target and not target.startswith('#'):assert (ROOT/target).exists(),target
    lock=json.loads((ROOT/'upstream-lock.json').read_text())['btpanel'];vendor=ROOT/'btpanel'
    actual={str(f.relative_to(vendor)):hashlib.sha256(f.read_bytes()).hexdigest() for f in vendor.rglob('*') if f.is_file()}
    assert actual==lock['files'],'Official btpanel snapshot drifted'
    for folder in [f.parent for f in ROOT.glob('*/SKILL.md')]+[ROOT/'tools']:
        for f in folder.rglob('*.py'):ast.parse(f.read_text(),filename=str(f))
        for f in folder.rglob('*.php'):run(['php','-l',f])
    run(['php',ROOT/'saicode/scripts/saicode_generate.php','--help'])
    run([sys.executable,ROOT/'btpanel/scripts/bt_mcp_setup.py','--help'])
    run([sys.executable,ROOT/'saicode/tests/test_cli.py'])
    run([sys.executable,ROOT/'saiadmin6-plugin/tests/test_saistore.py'])
    run([sys.executable,ROOT/'saiadmin6-plugin/scripts/self_test.py',*(['--skip-docker'] if a.skip_docker else [])])
    print('PASS '+str(len(skills))+' skill manifests, local links, exact official btpanel snapshot, Python/PHP syntax, CLI help, SaiCode ownership/recovery, SaiStore local protocol tests and portable plugin examples')
if __name__=='__main__':main()
