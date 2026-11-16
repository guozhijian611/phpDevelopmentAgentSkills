#!/usr/bin/env python3
"""Patch the verified saipackage 6.1.0 immediate-reload block in an explicit lab copy."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('lab');a=p.parse_args()
root=Path(a.lab).resolve()
if not (root/'lab.json').is_file() or not root.name.startswith('sai6lab-'):
 raise SystemExit('Expected a lab.py temporary environment, not a production project')
import json
meta=json.loads((root/'lab.json').read_text())
if root.name!=meta['project']:raise SystemExit('Lab identity mismatch')
import re
if not re.fullmatch(r'[A-Za-z0-9_-]+', meta.get('backend', '')):raise SystemExit('Invalid backend directory')
f=root/'app'/meta['backend']/'plugin/saipackage/app/logic/InstallLogic.php'
old='''            self::monitorResume();
            return Server::restart();'''
new='''            // Return the HTTP response before signaling worker reload.
            Timer::add(0.5, function () {
                self::monitorResume();
                Server::restart();
            }, [], false);
            return true;'''
s=f.read_text()
if new in s: print('Already patched');raise SystemExit(0)
if s.count(old)!=1:raise SystemExit('Source differs; inspect before patching')
f.write_text(s.replace(old,new));print('Patched lab copy; restart backend and retest HTTP response')
