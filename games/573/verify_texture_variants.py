"""Verify every declared texture through the real offline HTTP replay server."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent

def verify():
    manifest = json.loads((HERE / 'texture_variants.json').read_text())
    if not manifest['complete']:
        raise ValueError('Incomplete texture download; inspect texture_variants.json')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    base = 'http://127.0.0.1:%d' % port
    (HERE / 'replay').mkdir(exist_ok=True)
    log = (HERE / 'replay/verify-textures.log').open('w')
    process = subprocess.Popen([sys.executable, '-B', '-u', str(HERE / 'replay_server.py')],
                  env=dict(os.environ, REPLAY_PORT=str(port), REPLAY_SOURCE='wire',
                           SELECT_ROUNDS='', REPLAY_TEXTURE_FORMAT='webp'), stdout=log, stderr=log)
    def fetch(path):
        with urllib.request.urlopen(base + '/' + path.lstrip('/'), timeout=15) as response:
            return response.read(), response.headers.get_content_type()
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError('Offline replay failed to start')
            try:
                fetch('/__replay_status')
                break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('Replay startup timed out')
        engine = next((HERE / 'static/rc2/cocos-js').glob('_virtual_cc-*.js'))
        original_sha = hashlib.sha256(engine.read_bytes()).hexdigest()
        served, _ = fetch(engine.relative_to(HERE / 'static').as_posix())
        expected = b'SUPPORT_TEXTURE_FORMATS:[".webp",".jpg",".jpeg",".bmp",".png"]'
        if expected not in served:
            raise ValueError('No-ASTC WebP preference was not applied')
        if hashlib.sha256(engine.read_bytes()).hexdigest() != original_sha:
            raise ValueError('Original Cocos engine file changed')
        def asset(row):
            body, ctype = fetch(row['path'])
            if hashlib.sha256(body).hexdigest() != row['sha256']:
                raise ValueError('HTTP content differs: ' + row['path'])
            mime = {'.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg', '.bmp': 'image/bmp'}.get(row['extension'])
            if mime and ctype != mime:
                raise ValueError('Unexpected Content-Type for ' + row['path'] + ': ' + ctype)
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(asset, manifest['variants']))
        report = {'all_versioned_variants_http_200': len(manifest['variants']),
                  'counts': manifest['counts'], 'all_http_sha256_match_originals': True,
                  'image_mime_types_verified': True, 'no_astc_webp_preference_verified': True,
                  'original_engine_unchanged': True, 'upstream_fallback': False,
                  'physical_windows_visual_verification': 'not performed'}
        (HERE / 'texture_validation.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))
    finally:
        process.terminate()
        process.wait(timeout=10)
        log.close()

if __name__ == '__main__':
    verify()
