#!/usr/bin/env python3
"""Build backend-only permission fixture ZIPs without a host, database or prior session files."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    skill=Path(__file__).resolve().parents[1];assets=skill/'assets/permission-fixture';out=a.output_dir.resolve()
    if out==assets or assets in out.parents:p.error('Output must be outside assets')
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sai6-permissions-example-') as temp:
        for version in ['1.0.0','1.1.0']:
            stage=Path(temp)/version;shutil.copytree(assets,stage)
            info=stage/'info.ini';info.write_text(info.read_text().replace('version = 1.1.0','version = '+version))
            if version=='1.0.0':
                (stage/'plugin/labpermit/db/migrations/20261116010001_split_labpermit_permissions.php').unlink()
                controller=stage/'plugin/labpermit/app/controller/ItemsController.php';text=controller.read_text()
                for action in ['index','read','stats','children','save','update','destroy']:
                    legacy='read' if action in ['index','read','stats','children'] else 'write'
                    text=text.replace('labpermit:items:'+action,"labpermit:legacy:"+legacy)
                controller.write_text(text)
            subprocess.run([sys.executable,str(skill/'scripts/package.py'),str(stage),'--zip',str(out/('labpermit-'+version+'.zip'))],check=True)
if __name__=='__main__':main()
