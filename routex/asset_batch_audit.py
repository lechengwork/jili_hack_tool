#!/usr/bin/env python3
"""Audit a batch against each real local replay handler, without a browser/fetch."""
import argparse
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import time
import urllib.request

from asset_audit import audit
from texture_variants import audit as texture_audit

ROOT = Path(__file__).resolve().parents[1]
BATCH = ['545', '573', '200', '224', '461', '664']


def check_game(gid):
    here = ROOT / 'games' / gid
    script = here / ('mock_server.py' if gid == '545' else 'replay_server.py')
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
    logdir = here / 'runtime'; logdir.mkdir(exist_ok=True)
    certificate = str(here / 'runtime/local.crt') if gid == '545' else None
    url = '%s://%s:%d' % ('https' if gid == '545' else 'http', 'localhost' if gid == '545' else '127.0.0.1', port)
    env = dict(os.environ, REPLAY_PORT=str(port), MOCK_PORT=str(port), REPLAY_SOURCE='wire')
    with (logdir / 'asset-audit-server.log').open('w') as log:
        process = subprocess.Popen([sys.executable, '-B', '-u', str(script)], cwd=ROOT,
                                   env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('Replay startup failed; see runtime/asset-audit-server.log')
                try:
                    ctx = ssl.create_default_context(cafile=certificate) if certificate else None
                    with urllib.request.urlopen(url + '/__replay_status', context=ctx, timeout=1):
                        break
                except (OSError, ValueError):
                    time.sleep(.1)
            else:
                raise RuntimeError('Replay readiness timed out; see runtime/asset-audit-server.log')
            report = audit(here / 'static', True, url, certificate)
            textures = texture_audit(here / 'static', fetch=False)
            served = {f['path']: f for f in report['http']['files']}
            report['texture_check'] = {
                'tool': 'texture_variants.audit(fetch=False)',
                'required_webp': textures['required_webp'], 'valid_webp': textures['valid_webp'],
                'http_verified': sum(served.get(r['path'], {}).get('status') == 'valid' for r in textures['assets']),
                'errors': [r for r in textures['assets'] if r['status'] != 'ok'],
                'unavailable_import_packs': textures['unavailable_import_packs'],
                'binary_import_packs': textures['binary_import_packs'],
                'scope': textures['scope']}
            report['batch_date'] = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
            (here / 'asset_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            return report
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game_ids', nargs='*', default=BATCH)
    args = parser.parse_args()
    failed = False
    for gid in args.game_ids:
        if gid not in BATCH:
            parser.error('Only these configured replay handlers are supported: ' + ', '.join(BATCH))
        try:
            r = check_game(gid)
            print(json.dumps({'game_id': gid, 'counts': r['counts'], 'random_native_9926e': r['random_native_9926e'],
                              'uncovered': len(r['uncovered']), 'replay_http': {k:r['http'][k] for k in ('valid', 'invalid')},
                              'webp': {k:r['texture_check'][k] for k in ('required_webp', 'valid_webp', 'http_verified')}}, ensure_ascii=False), flush=True)
            failed |= (not r['inventory_no_known_missing_or_invalid'] or bool(r['uncovered'])
                       or bool(r['http']['invalid']) or bool(r['texture_check']['errors']))
        except Exception as error:
            failed = True
            print(json.dumps({'game_id': gid, 'audit_error': str(error)}, ensure_ascii=False), flush=True)
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
