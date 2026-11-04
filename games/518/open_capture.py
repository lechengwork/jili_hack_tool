#!/usr/bin/env python3
"""Open the existing 518 capture server using a fresh LoginGame JSON file."""
import argparse
import json
from pathlib import Path
import ssl
import subprocess
import tempfile
import urllib.parse
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument('--login-json', default='/tmp/jili518_login.json')
ap.add_argument('--seconds', type=int, default=3600)
args = ap.parse_args()
r = json.loads(Path(args.login_json).read_text())
if isinstance(r, list):
    r = r[0]
url = r['game_url']
parts = urllib.parse.urlsplit(url)
if parts.scheme != 'https' or parts.hostname != 'uat-wbgame.jlfafafa3.com' or parts.path != '/cj/':
    raise SystemExit('Expected a fresh 518 /cj/ launch URL')
with urllib.request.urlopen(
    'https://127.0.0.1:8518/cj/src/polyfills.bundle.5adbf.js',
    context=ssl._create_unverified_context(), timeout=5,
) as response:
    if b'/cj/req' not in response.read():
        raise SystemExit('518 capture shim is missing')
p = subprocess.Popen([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--user-data-dir=' + tempfile.mkdtemp(prefix='jili-518-capture-'),
    '--host-resolver-rules=MAP uat-wbgame.jlfafafa3.com 127.0.0.1:8518',
    '--ignore-certificate-errors', '--disable-quic', '--no-first-run',
    '--no-default-browser-check', '--disable-features=ChromeWhatsNewUI', url,
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
Path('/tmp/jili518_capture_pid').write_text(str(p.pid))
print('518 capture Chrome pid=%s player_id=%s' % (p.pid, r.get('player_id', '?')), flush=True)
try:
    p.wait(timeout=args.seconds)
except (KeyboardInterrupt, subprocess.TimeoutExpired):
    p.terminate()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
