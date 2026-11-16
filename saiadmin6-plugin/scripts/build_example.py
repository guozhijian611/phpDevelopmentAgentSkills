#!/usr/bin/env python3
"""Build fresh-install and upgrade example ZIPs using only this skill's assets."""
import argparse, shutil, subprocess, sys, tempfile
from pathlib import Path
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', required=True)
args = parser.parse_args()
skill = Path(__file__).resolve().parents[1]
out = Path(args.output_dir).resolve()
assets = skill / 'assets' / 'phinx-fixture'
if out == assets or assets in out.parents:
    parser.error('Output must be outside the example assets')
out.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='sai6-example-') as temp:
    stage = Path(temp) / 'stage'
    shutil.copytree(assets, stage)
    upgrade = stage / 'plugin/labphinx/db/migrations/20261115000001_add_labphinx_note.php'
    upgrade_text = upgrade.read_bytes()
    info = (stage / 'info.ini').read_text()
    vue = stage / 'saiadmin-artd/src/views/plugin/labphinx/index.vue'
    vue_text = vue.read_text()
    for version in ('1.0.0', '1.0.1'):
        (stage / 'info.ini').write_text(info.replace('version = 1.0.1', 'version = ' + version))
        vue.write_text(vue_text.replace("'1.0.1'", repr(version)))
        if version == '1.0.0':
            upgrade.unlink()
        else:
            upgrade.write_bytes(upgrade_text)
        subprocess.run([sys.executable, str(skill / 'scripts/package.py'), str(stage), '--zip', str(out / ('labphinx-' + version + '.zip'))], check=True)
