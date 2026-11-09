#!/usr/bin/env python3
"""664 capture adapter for the existing route-X collector (no 696 math mapping)."""
import json
import os
from pathlib import Path
import ssl
import sys
import threading
import mimetypes
import urllib.request
from datetime import datetime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SESSION = HERE / 'webcap' / datetime.now().strftime('%Y%m%d-%H%M%S')
SESSION.mkdir(parents=True, exist_ok=False)
SESSION.chmod(0o700)
login_file = HERE / 'login_session.local.json'
if login_file.exists():
    launch = json.loads(login_file.read_text())
    (SESSION / 'source.json').write_text(json.dumps({'player_id': launch.get('player_id'), 'game_id': launch.get('game_id'), 'currency': 'IDR', 'provider_game_id': 664}))
if login_file.exists():
    (SESSION / 'login_session.local.json').write_bytes(login_file.read_bytes())
    (SESSION / 'login_session.local.json').chmod(0o600)
resume = None  # Every login gets independent random values and keys
resume_key = json.loads((Path(resume) / 'key.json').read_text()) if resume else None
os.environ.update({
    'STATIC': str(HERE / 'static'), 'HOST': '127.0.0.1',
    'PORT': '8664', 'TLS': '1', 'GAME_PATH': '/lj500/',
    'VERBOSE': '1', 'CAPTURE': '1', 'INJECT_BUNDLE': '1', 'LIVE_DECODE': '1',
    'CAP_OUT': str(SESSION / 'exchanges.jsonl'),
    'GRV_OUT': str(SESSION / 'grv.jsonl'),
    'GRAB': str(SESSION / 'key.json'),
    'REPLAY': str(SESSION / 'unused-replay.jsonl'),
    'RESPONSES': str(SESSION / 'unused-responses.jsonl'),
    'INIT_SEQ': str(SESSION / 'unused-init.jsonl'),
    'ASSET_FALLBACK': '1',
    'ASSET_ORIGIN': 'uat-wbgame.jlfafafa3.com',
})
sys.path.insert(0, str(ROOT / 'routex'))
import server
# Version manifests are mutable; never use another game's cached shared tree.
server.SHARED_ROOT = server.STATIC_ROOT
import decrypt_capture as dc
import fg5
sys.path.insert(0, str(HERE))
from live_math_664 import export_spin, format_status
sys.path.insert(0, str(HERE))
def wire_to_math(payload):
    from math_adapter import wire_to_math as decode
    return decode(payload)

def math_to_wire(value):
    from math_adapter import math_to_wire as encode
    return encode(value)



# Keep the existing wasm/grv hooks; capture the new game's endpoint.
# server has already selected capture_shim (real keys), not the offline mock shim.
server.WASM_SHIM = server.WASM_SHIM.replace('/fg5/req', '/lj500/req')
if 'getRandomValues hooked' not in server.WASM_SHIM or 'patchBytes' in server.WASM_SHIM:
    raise RuntimeError('664 requires passive capture shim; refusing a mock key patch')
lock = threading.Lock()
if resume_key:
    server._cap_key = bytes.fromhex(resume_key['key'])
    (SESSION / 'key.json').write_text(json.dumps(resume_key))
    (SESSION / 'resumed_from.txt').write_text(resume + '\n')


def asset_fallback(path):
    # The original fallback only permits fg5/. Also, its backend-host fallback
    # can return an empty JSON response for a missing asset. Use the document CDN only.
    rel = path.lstrip('/')
    dest = (HERE / 'static' / rel).resolve()
    if not rel.startswith(('lj500/', 'astarte2/', 'smallicon/', 'aeon/', 'astarte-aeon/', 'lang/', 'logo/')):
        return None
    if HERE / 'static' not in dest.parents:
        return None
    try:
        req = urllib.request.Request('https://uat-wbgame.jlfafafa3.com/' + rel,
                                     headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as response:
            if response.status != 200:
                return None
            data = response.read()
            ctype = response.headers.get('Content-Type') or mimetypes.guess_type(rel)[0]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        print('[664 asset] %s %sB' % (path, len(data)), flush=True)
        if path.endswith('.js') and server.BUNDLE_TARGET in path:
            data = (server.WASM_SHIM + '\n;\n').encode('utf-8') + data
        return data, ctype or 'application/octet-stream'
    except Exception as error:
        print('[664 asset failed] %s: %s' % (path, error), flush=True)
        return None


server.origin_fetch_and_cache = asset_fallback

# The upstream HTML declares its charset after a >12 KB inline script. Browsers
# can default to a legacy encoding before that declaration and misread Unicode
# identifiers in shared bundles. Declare UTF-8 in the HTTP response as well.
_original_send = server.Handler._send

def send_utf8(self, status, data=b'', ctype='application/octet-stream', extra=None):
    if (ctype.startswith('text/') or 'javascript' in ctype or 'json' in ctype) and 'charset=' not in ctype:
        ctype += '; charset=utf-8'
    return _original_send(self, status, data, ctype, extra)

server.Handler._send = send_utf8


def live_decode(rec):
    with lock:
        req = fg5.parse_fields(bytes.fromhex(rec.get('req_body_hex') or ''))
        if server._cap_key is None:
            pub = req.get(4)
            if isinstance(pub, bytes):
                private = dc.find_priv(server._cap_grv, pub)
                if private:
                    server._cap_key = dc.shared_key(private)
                    key_path = SESSION / 'key.json'
                    key_path.touch(mode=0o600, exist_ok=True)
                    key_path.chmod(0o600)
                    key_path.write_text(json.dumps({'key': server._cap_key.hex(),
                                                     'source': 'this session handshake and GRV'}) + '\n')
        if server._cap_key is None:
            return None
        d = dc.decrypt_response(bytes.fromhex(rec['resp_body_hex']), server._cap_key)
        if not d['_sig_ok']:
            raise ValueError('664 response signature verification failed')
        # Raw capture is durable before game-specific math export; never use the 696 codec.
        d['idx'] = rec.get('seq')
        d['kind'] = dc.kind_of(fg5.parse_fields(req.get(2, b'')))
        with (SESSION / 'exchanges_ordered.jsonl').open('a') as f:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')
        math_status = format_status(export_spin(d, HERE, SESSION, wire_to_math, math_to_wire))
        return '[664 decode] seq=%s type=%s ret=%s payload=%sB signature=OK' % (
            d['idx'], d['type'], d['ret'], d['len']) + math_status


def safe_live_decode(rec):
    try:
        return live_decode(rec)
    except Exception as error:
        with (SESSION / 'decode_errors.jsonl').open('a') as f:
            f.write(json.dumps({'idx': rec.get('seq'), 'error': type(error).__name__ + ': ' + str(error),
                                'raw_exchange_preserved': True}) + '\n')
        raise

server._live_decode = safe_live_decode

if __name__ == '__main__':
    from http.server import ThreadingHTTPServer
    ThreadingHTTPServer.request_queue_size = 128
    httpd = ThreadingHTTPServer(('127.0.0.1', 8664), server.Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(ROOT / 'dist124/cert.pem'), str(ROOT / 'dist124/key.pem'))
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    (HERE / 'current_session.txt').write_text(str(SESSION) + '\n')
    (SESSION / 'server.pid').write_text(str(os.getpid()) + '\n')
    print('[664 capture] session=%s; listen=https://127.0.0.1:8664' % SESSION, flush=True)
    httpd.serve_forever()
