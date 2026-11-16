#!/usr/bin/env python3
"""Verify a relocated skill without any prior session files. Requires Python3.9+; Compose optional."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-docker', action='store_true')
    args = parser.parse_args()
    original = Path(__file__).resolve().parents[1]
    labs = []
    with tempfile.TemporaryDirectory(prefix='sai6-portability-') as temp:
        root = Path(temp)
        skill = root / 'relocated skill'
        shutil.copytree(original, skill, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        def run(script, *argv, ok=True):
            result = subprocess.run([sys.executable, str(skill/'scripts'/script), *map(str,argv)], cwd=root, capture_output=True, text=True)
            if ok and result.returncode:
                raise RuntimeError(result.stderr or result.stdout)
            if not ok and result.returncode == 0:
                raise AssertionError('Invalid input accepted: '+script)
            return result
        run('build_example.py', '--output-dir', root/'output')
        for name in ('lab.py', 'package.py', 'fix_reload.py', 'build_example.py'):
            run(name, '--help')
        for version, count in [('1.0.0', 1), ('1.0.1', 2)]:
            with zipfile.ZipFile(root/'output'/('labphinx-'+version+'.zip')) as archive:
                assert 'info.ini' in archive.namelist()
                assert 'support = 6.x' in archive.read('info.ini').decode()
                assert ('version = '+version) in archive.read('info.ini').decode()
                assert len([n for n in archive.namelist() if '/migrations/' in n]) == count
                assert version in archive.read('saiadmin-artd/src/views/plugin/labphinx/index.vue').decode()
        stage = root/'stage'
        shutil.copytree(skill/'assets/phinx-fixture', stage)
        info = stage/'info.ini'
        valid_info = info.read_text()
        info.write_text(valid_info.replace('support = 6.x', 'support = 5.x'))
        run('package.py', stage, ok=False)
        info.write_text(valid_info)
        extra = stage/'plugin/labphinx/.env'
        extra.write_text('test only')
        run('package.py', stage, ok=False)
        extra.unlink()
        run('package.py', stage, '--frontend', '../escape', ok=False)
        link = stage/'plugin/labphinx/unsafe-link'
        link.symlink_to(info)
        run('package.py', stage, ok=False)
        link.unlink()
        source = root/'baseline'
        (source/'server/vendor').mkdir(parents=True)
        (source/'saiadmin-artd').mkdir()
        (source/'server/composer.json').write_text(json.dumps({'require':{'saithink/saiadmin':'^6.0'}}))
        (source/'server/composer.lock').write_text(json.dumps({'packages':[{'name':'saithink/saiadmin','version':'6.1.5'},{'name':'saithink/saipackage','version':'6.1.0'}]}))
        (source/'server/vendor/autoload.php').write_text('<?php')
        (source/'server/.env').write_text('MUST_NOT_COPY=1')
        (source/'server/runtime').mkdir()
        (source/'server/runtime/probe').write_text('MUST_NOT_COPY')
        (source/'saiadmin-artd/package.json').write_text('{}')
        try:
            for db in ('mysql','pgsql'):
                lab = Path(run('lab.py','create','--source',source,'--db',db).stdout.strip())
                labs.append(lab)
                assert not (lab/'app/server/.env').exists()
                assert not (lab/'app/server/runtime').exists()
                assert not (lab/'app/server/vendor').exists()
                config = json.loads((lab/'compose.json').read_text())
                assert config['services']['backend']['environment']['DB_TYPE'] == db
                assert 'build' in config['services']['backend']
                if not args.skip_docker:
                    run('lab.py','compose',lab,'config','--quiet')
                target = lab/'app/server/plugin/saipackage/app/logic/InstallLogic.php'
                target.parent.mkdir(parents=True)
                target.write_text('<?php\n            self::monitorResume();\n            return Server::restart();\n')
                run('fix_reload.py',lab)
                once = target.read_text()
                run('fix_reload.py',lab)
                assert target.read_text() == once
                target.write_text('<?php // unsupported source')
                run('fix_reload.py',lab,ok=False)
            assert labs[0] != labs[1]
            copied = Path(run('lab.py','create','--source',source,'--copy-vendor').stdout.strip())
            labs.append(copied)
            assert (copied/'app/server/vendor/autoload.php').is_file()
            assert not (copied/'app/server/.env').exists()
            run('lab.py','create','--source',source,'--backend','server','--frontend','server',ok=False)
        finally:
            for lab in labs:
                shutil.rmtree(lab)
        print('PASS: relocated scripts, two example versions, invalid packages, isolated MySQL/PostgreSQL config, copy exclusions, idempotent patch')

if __name__ == '__main__':
    main()
