#!/usr/bin/env python3
"""Open the existing 545 capture server using a fresh LoginGame JSON file."""
import argparse
import json
from pathlib import Path
import ssl
import subprocess
import tempfile
import urllib.parse
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument('--login-json', default=str(Path(__file__).resolve().parent / 'login_session.local.json'))
ap.add_argument('--seconds', type=int, default=3600)
ap.add_argument('--netlog', help='Optional local Chrome network diagnostic JSON (may contain private URLs)')
args = ap.parse_args()
r = json.loads(Path(args.login_json).read_text())
if isinstance(r, list):
    r = r[0]
url = r['game_url']
parts = urllib.parse.urlsplit(url)
if parts.scheme != 'https' or parts.hostname != 'uat-wbgame.jlfafafa3.com' or parts.path != '/cc3x3/':
    raise SystemExit('Expected a fresh 545 /cc3x3/ launch URL')
# A first-time fallback downloads the bundle; the following request serves the
# cached bytes with the capture hook. Verify before opening a browser.
for attempt in range(2):
    with urllib.request.urlopen(
        'https://127.0.0.1:8545/cc3x3/src/polyfills.bundle.5adbf.js',
        context=ssl._create_unverified_context(), timeout=30,
    ) as response:
        shim = response.read()
        if b'/cc3x3/req' in shim and b'getRandomValues hooked' in shim:
            break
else:
    raise SystemExit('545 capture shim is missing')
p = subprocess.Popen([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--user-data-dir=' + tempfile.mkdtemp(prefix='jili-545-capture-'),
    '--host-resolver-rules=MAP uat-wbgame.jlfafafa3.com 127.0.0.1:8545',
    '--ignore-certificate-errors', '--disable-quic', '--no-first-run',
    '--no-default-browser-check', '--disable-features=ChromeWhatsNewUI',
    *(['--log-net-log=' + str(Path(args.netlog).resolve())] if args.netlog else []), url,
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
Path('/tmp/jili545_capture_pid').write_text(str(p.pid))
print('545 capture Chrome pid=%s player_id=%s' % (p.pid, r.get('player_id', '?')), flush=True)
try:
    p.wait(timeout=args.seconds)
except (KeyboardInterrupt, subprocess.TimeoutExpired):
    p.terminate()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
