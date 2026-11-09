#!/usr/bin/env python3
"""Open the existing 807 capture server using a fresh LoginGame JSON file."""
import argparse
import json
import codecs
from pathlib import Path
import ssl
import subprocess
import tempfile
import urllib.parse
import urllib.request

from runtime_support import chrome_path

ap = argparse.ArgumentParser()
ap.add_argument('--login-json', default=str(Path(__file__).resolve().parent / 'login_session.local.json'))
ap.add_argument('--seconds', type=int, default=3600)
ap.add_argument('--netlog', help='Optional local Chrome network diagnostic JSON (may contain private URLs)')
args = ap.parse_args()
# Windows PowerShell 5.1 `>` redirection writes UTF-16 with a BOM.
raw = Path(args.login_json).read_bytes()
r = json.loads(raw.decode('utf-16') if raw[:2] in (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE) else raw.decode('utf-8-sig'))
if isinstance(r, list):
    r = r[0]
url = r['game_url']
parts = urllib.parse.urlsplit(url)
if parts.scheme != 'https' or parts.hostname != 'uat-wbgame.jlfafafa3.com' or parts.path != '/fg1000/':
    raise SystemExit('Expected a fresh 807 /fg1000/ launch URL')
# A first-time fallback downloads the bundle; the following request serves the
# cached bytes with the capture hook. Verify before opening a browser.
for attempt in range(2):
    with urllib.request.urlopen(
        'https://127.0.0.1:8807/fg1000/src/polyfills.bundle.5adbf.js',
        context=ssl._create_unverified_context(), timeout=30,
    ) as response:
        shim = response.read()
        if b'/fg1000/req' in shim and b'getRandomValues hooked' in shim:
            break
else:
    raise SystemExit('807 capture shim is missing')
p = subprocess.Popen([
    chrome_path(),
    '--user-data-dir=' + tempfile.mkdtemp(prefix='jili-807-capture-'),
    '--host-resolver-rules=MAP uat-wbgame.jlfafafa3.com 127.0.0.1:8807',
    '--ignore-certificate-errors', '--disable-quic', '--no-first-run',
    '--no-default-browser-check', '--disable-features=ChromeWhatsNewUI',
    *(['--log-net-log=' + str(Path(args.netlog).resolve())] if args.netlog else []), url,
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
Path(tempfile.gettempdir(), 'jili807_capture_pid').write_text(str(p.pid), encoding='utf-8')
print('807 capture Chrome pid=%s player_id=%s' % (p.pid, r.get('player_id', '?')), flush=True)
try:
    p.wait(timeout=args.seconds)
except (KeyboardInterrupt, subprocess.TimeoutExpired):
    p.terminate()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
