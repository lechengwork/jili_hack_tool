#!/usr/bin/env python3
"""518 capture adapter for the existing route-X collector (no 696 math mapping)."""
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
resume = os.environ.get('RESUME_SESSION')
resume_key = json.loads((Path(resume) / 'key.json').read_text()) if resume else None
os.environ.update({
    'STATIC': str(HERE / 'static'), 'HOST': '127.0.0.1',
    'PORT': '8518', 'TLS': '1', 'GAME_PATH': '/cj/',
    'CAPTURE': '1', 'INJECT_BUNDLE': '1', 'LIVE_DECODE': '1',
    'CAP_OUT': str(SESSION / 'exchanges.jsonl'),
    'GRV_OUT': str(SESSION / 'grv.jsonl'),
    'GRAB': str(SESSION / 'key.json'),
    'REPLAY': str(SESSION / 'unused-replay.jsonl'),
    'ASSET_FALLBACK': '1',
    'ASSET_ORIGIN': 'uat-wbgame.jlfafafa3.com',
})
sys.path.insert(0, str(ROOT / 'routex'))
import server
import decrypt_capture as dc
import fg5
from live_math import export_spin, format_status
sys.path.insert(0, str(HERE))
from math_adapter import wire_to_math, math_to_wire

# Keep the existing wasm/grv hooks; capture the new game's endpoint.
server.WASM_SHIM = server.WASM_SHIM.replace('/fg5/req', '/cj/req')
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
    if not rel.startswith(('cj/', 'astarte2/', 'smallicon/')):
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
        print('[518 asset] %s %sB' % (path, len(data)), flush=True)
        return data, ctype or 'application/octet-stream'
    except Exception as error:
        print('[518 asset failed] %s: %s' % (path, error), flush=True)
        return None


server.origin_fetch_and_cache = asset_fallback


def live_decode(rec):
    with lock:
        req = fg5.parse_fields(bytes.fromhex(rec.get('req_body_hex') or ''))
        if server._cap_key is None:
            pub = req.get(4)
            if isinstance(pub, bytes):
                private = dc.find_priv(server._cap_grv, pub)
                if private:
                    server._cap_key = dc.shared_key(private)
        if server._cap_key is None:
            return None
        d = dc.decrypt_response(bytes.fromhex(rec['resp_body_hex']), server._cap_key)
        if not d['_sig_ok']:
            raise ValueError('518 response signature verification failed')
        # Raw capture is durable before game-specific math export; never use the 696 codec.
        d['idx'] = rec.get('seq')
        d['kind'] = dc.kind_of(fg5.parse_fields(req.get(2, b'')))
        with (SESSION / 'exchanges_ordered.jsonl').open('a') as f:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')
        math_status = format_status(export_spin(d, HERE, SESSION, wire_to_math, math_to_wire))
        return '[518 decode] seq=%s type=%s ret=%s payload=%sB signature=OK' % (
            d['idx'], d['type'], d['ret'], d['len']) + math_status


server._live_decode = live_decode

if __name__ == '__main__':
    from http.server import ThreadingHTTPServer
    httpd = ThreadingHTTPServer(('127.0.0.1', 8518), server.Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(ROOT / 'dist124/cert.pem'), str(ROOT / 'dist124/key.pem'))
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    (HERE / 'current_session.txt').write_text(str(SESSION) + '\n')
    print('[518 capture] session=%s; listen=https://127.0.0.1:8518' % SESSION, flush=True)
    httpd.serve_forever()
