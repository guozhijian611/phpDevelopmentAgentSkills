#!/usr/bin/env python3
"""Offline iv8 smoke probe; no installs, site requests or business session reads."""
import argparse
import contextlib
import importlib.metadata
import json
import platform
import sys


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    report = {
        'python': sys.version.split()[0], 'executable': sys.executable,
        'os': platform.system(), 'machine': platform.machine(),
        'virtual_environment': sys.prefix != sys.base_prefix,
        'checks': {},
        'scope': 'Offline runtime probes only; no target-site or HTTP validation.',
    }
    try:
        # Redirect Python-level diagnostics; native releases may still print a banner.
        with contextlib.redirect_stdout(sys.stderr):
            import iv8
    except ModuleNotFoundError as exc:
        report['error'] = 'iv8_missing' if exc.name == 'iv8' else 'dependency_missing'
        report['next_step'] = 'Use references/environment.md to create or repair the project environment, then rerun with its interpreter.'
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2 if exc.name == 'iv8' else 1
    except Exception as exc:
        report['error'] = type(exc).__name__
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    try:
        report['iv8'] = importlib.metadata.version('iv8')
        expressions = {
            'javascript': '1 + 2 === 3',
            'window': 'window === globalThis',
            'dom_content': '''(() => {const el=document.createElement('div'); el.id='iv8-probe'; el.textContent='测试'; document.body.appendChild(el); const ok=document.getElementById('iv8-probe').textContent==='测试'; el.remove(); return ok;})()''',
            'navigator': 'typeof navigator.userAgent === "string" && navigator.userAgent.length > 0',
            'storage_roundtrip': '''(() => {localStorage.setItem('iv8-probe','ok'); const ok=localStorage.getItem('iv8-probe')==='ok'; localStorage.removeItem('iv8-probe'); return ok;})()''',
            'crypto_call': 'crypto.getRandomValues(new Uint8Array(16)).length === 16',
            'encoding_roundtrip': 'new TextDecoder().decode(new TextEncoder().encode("测试 abc")) === "测试 abc"',
            'form_encoding': 'new URLSearchParams({q:"a b+c"}).toString() === "q=a+b%2Bc"',
            'timer_execution': '''(() => {globalThis.__iv8_probe_timer=false; setTimeout(()=>{globalThis.__iv8_probe_timer=true;},10); window.__iv8__.eventLoop.advance(20); return globalThis.__iv8_probe_timer===true;})()''',
        }
        with contextlib.redirect_stdout(sys.stderr):
            with iv8.JSContext() as ctx:
                for name, source in expressions.items():
                    try:
                        report['checks'][name] = {'ok': ctx.eval(source) is True}
                    except Exception as exc:
                        report['checks'][name] = {'ok': False, 'error': type(exc).__name__}
    except Exception as exc:
        report['error'] = type(exc).__name__
    if any(not c['ok'] for c in report['checks'].values()):
        report['next_step'] = 'Investigate failed API semantics against the installed version and target script; do not blindly reinstall or send site requests.'
    report['ok'] = bool(report['checks']) and not report.get('error') and all(c['ok'] for c in report['checks'].values())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
