#!/usr/bin/env python3
"""One-command 545 offline wire replay."""
import argparse
import os
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
GAME = ROOT / 'games/545'
ap = argparse.ArgumentParser()
ap.add_argument('--source', choices=['wire', 'math'], default='math')
ap.add_argument('--math-dir', help='Directory of per-round math JSON; defaults to games/545/math')
ap.add_argument('--no-watch-math', action='store_true', help='Freeze math at startup instead of reloading before each SPIN')
ap.add_argument('--rounds', help='Comma-separated full round IDs, in replay order')
ap.add_argument('--port', type=int, default=8546)
ap.add_argument('--selftest', action='store_true')
ap.add_argument('--no-browser', action='store_true')
args = ap.parse_args()
if args.selftest:
    raise SystemExit(subprocess.call([sys.executable, '-B', str(GAME / 'verify_mock.py')]))
with socket.socket() as test:
    if test.connect_ex(('127.0.0.1', args.port)) == 0:
        raise SystemExit('Port %s is occupied; close the previous mock or use --port.' % args.port)
env = dict(os.environ, MOCK_PORT=str(args.port), REPLAY_SOURCE=args.source)
env['WATCH_MATH'] = '0' if args.no_watch_math else '1'
if args.math_dir:
    env['MATH_DIR'] = str(Path(args.math_dir).resolve())
if args.rounds:
    env['REPLAY_ROUNDS'] = args.rounds
else:
    env.pop('REPLAY_ROUNDS', None)
server = subprocess.Popen([sys.executable, '-B', '-u', str(GAME / 'mock_server.py')], env=env)
browser = None
try:
    for _ in range(80):
        if server.poll() is not None:
            raise RuntimeError('Mock server failed to start')
        try:
            with urllib.request.urlopen('https://127.0.0.1:%s/cc3x3/' % args.port,
                                        context=ssl._create_unverified_context(), timeout=1):
                break
        except OSError:
            time.sleep(0.1)
    else:
        raise RuntimeError('Mock server did not become ready')
    if args.no_browser:
        server.wait()
    else:
        browser = subprocess.Popen([sys.executable, '-B', '-u', str(GAME / 'open_mock.py')], env=env)
        browser.wait()
except KeyboardInterrupt:
    pass
finally:
    for process in (browser, server):
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
