#!/usr/bin/env python3
"""Offline 518 replay using the established route-X transport and mock keys."""
from collections import defaultdict
import json
import os
from pathlib import Path
import ssl
import struct
import sys
import threading
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SESSION = Path(os.environ.get('REPLAY_SESSION') or (HERE / 'current_session.txt').read_text().strip())
if not SESSION.is_absolute():
    SESSION = HERE / SESSION
PORT = int(os.environ.get('MOCK_PORT', '8519'))
REPLAY = SESSION / 'export/exchanges_ordered.jsonl'
ROWS = [json.loads(line) for line in REPLAY.read_text().splitlines() if line]
REQUESTS = {r['seq']: r for r in map(json.loads, (SESSION / 'exchanges.jsonl').read_text().splitlines())}
os.environ.update(STATIC=str(HERE / 'static'), HOST='127.0.0.1', PORT=str(PORT), TLS='1',
                  GAME_PATH='/cj/', CAPTURE='0', INJECT_BUNDLE='1', REPLAY=str(REPLAY),
                  REPLAY_LOG='0', ASSET_FALLBACK='0',
                  VERBOSE=os.environ.get('MOCK_VERBOSE', '0'),
                  SHARED_HEX_PATH=str(HERE / 'mock_shared.hex'))
sys.path.insert(0, str(ROOT / 'routex'))
import server
import fg5

# Reuse only the crypto hook, excluding the 696-specific UI override.
server.WASM_SHIM = server.WASM_SHIM.split('// Replay-only UI override:')[0]
server.WASM_SHIM = (ROOT / 'routex/err_probe_shim.js').read_text() + '\n' + server.WASM_SHIM
server.SHARED_ROOT = str(HERE / 'static')
server.SAMPLES = {}
by_action = defaultdict(list)
spins = defaultdict(list)
for row in ROWS:
    req = fg5.parse_fields(bytes.fromhex(REQUESTS[row['idx']]['req_body_hex']))
    requested_type = req.get(1, 0)
    if requested_type != row['type']:
        raise ValueError('Request/response type mismatch in capture')
    server.SAMPLES.setdefault(row['type'], bytes(row['raw']))
    by_action[(row['type'], req.get(2, b''))].append(row)
    if row['type'] == 0 and row['ret'] == 0:
        raw = bytes(row['raw'])
        bet = struct.unpack('<d', fg5.parse_fields(fg5.parse_fields(raw)[23])[1])[0]
        spins[bet].append(raw)
if not spins:
    raise ValueError('Capture has no successful spins')
source = os.environ.get('REPLAY_SOURCE', 'wire')
if source == 'math':
    from math_adapter import math_to_wire
    math_dir = Path(os.environ.get('MATH_DIR', str(HERE / 'math')))
    spins.clear()
    for file in sorted(math_dir.glob('*.json')):
        if not file.stem.isdigit():
            continue
        env = json.loads(file.read_text())
        spins[env['spinReq']['bet']].append(math_to_wire(env))
elif source != 'wire':
    raise ValueError('REPLAY_SOURCE must be wire or math')
rounds = [x for x in os.environ.get('REPLAY_ROUNDS', '').split(',') if x]
if rounds:
    all_spins = {str(fg5.parse_fields(raw)[20]): (bet, raw) for bet, pool in spins.items() for raw in pool}
    missing = set(rounds) - set(all_spins)
    if missing:
        raise ValueError('Round IDs not found: %s' % sorted(missing))
    spins.clear()
    for rid in rounds:
        bet, raw = all_spins[rid]; spins[bet].append(raw)
if not spins:
    raise ValueError('No replay samples selected')
state = {'pub': b'', 'indices': defaultdict(int), 'actions': defaultdict(int), 'balance': None}
lock = threading.Lock()


def replace_field(buf, number, wire, value):
    out = bytearray(); pos = 0; found = False
    replacement = fg5.enc_tag(number, wire) + value
    while pos < len(buf):
        start = pos
        tag, pos = fg5.dec_varint(buf, pos)
        wt = tag & 7
        if wt == 0:
            _, pos = fg5.dec_varint(buf, pos)
        elif wt == 1:
            pos += 8
        elif wt == 2:
            size, pos = fg5.dec_varint(buf, pos); pos += size
        elif wt == 5:
            pos += 4
        else:
            raise ValueError('Unsupported protobuf wire type')
        if tag >> 3 == number:
            out.extend(replacement); found = True
        else:
            out.extend(buf[start:pos])
    if not found:
        out.extend(replacement)
    return bytes(out)


def pick_response(req):
    typ = req['seq']  # Verified in every captured exchange: f1 is the requested message type.
    action = req['action']
    with lock:
        if typ == 1 and req['client_pub'] != state['pub']:
            state.update(pub=req['client_pub'], indices=defaultdict(int), actions=defaultdict(int), balance=None)
            server._RID['last'] = 0
        if typ == 0:
            fields = fg5.parse_fields(action)
            bet = struct.unpack('<d', fields[1])[0]
            if bet not in spins:
                print('[518 mock] no captured samples for bet=%s' % bet, flush=True)
                return 0, b'', 400, 'unsupported-bet'
            index = state['indices'][bet]
            raw = spins[bet][index % len(spins[bet])]
            state['indices'][bet] += 1
            raw, rid = server._bump_rid(raw)
            state['balance'] = fg5.parse_fields(raw)[6]
            print('[518 mock] spin=%s bet=%s round=%s' % (index, bet, rid), flush=True)
            return 0, raw, 0, 'spin[%s]' % index
        if typ == 2 and state['balance'] is not None:
            template = server.SAMPLES[2]
            core = replace_field(fg5.parse_fields(template)[1], 2, 1, state['balance'])
            return 2, replace_field(template, 1, 2, fg5.enc_varint(len(core)) + core), 0, 'balance-after-spin'
        key = (typ, action)
        matches = by_action.get(key)
        if matches:
            index = state['actions'][key]
            state['actions'][key] += 1
            row = matches[min(index, len(matches) - 1)]
        else:
            row = next((r for r in ROWS if r['type'] == typ), None)
        if row is None:
            return typ, b'', 0, 'empty-ack'
        return typ, bytes(row['raw']), row['ret'], 'captured-type[%s]' % typ


server.pick_response = pick_response
AUX = json.loads((HERE / 'auxiliary_responses.json').read_text())
server.SSO_JSON = json.loads((HERE / 'mock_sso.json').read_text())


class Handler(server.Handler):
    def auxiliary(self):
        path = urlsplit(self.path).path
        item = AUX.get(path)
        # Optional referral/promotion services are absent from the captured
        # operator profile. Return an empty protobuf message, never generic JSON.
        if item is None and path.startswith(('/subagentservice/', '/promotionservice/')):
            self._send(200, b'', 'application/x-protobuf')
            return True
        if item is None:
            return False
        ctype = next((h.split(': ', 1)[1] for h in item['headers']
                      if h.startswith('content-type: ')), 'application/octet-stream')
        self._send(200, bytes.fromhex(item['body_hex']), ctype)
        return True

    def do_GET(self):
        if self.auxiliary():
            return
        if urlsplit(self.path).path == '/cj/' and self.headers.get('Host', '').split(':')[0] == server.GS_HOST:
            self._send(204)
            return
        super().do_GET()

    def do_POST(self):
        path = urlsplit(self.path).path
        if path in AUX or path.startswith(('/subagentservice/', '/promotionservice/')):
            self._read_body()
            self.auxiliary()
            return
        super().do_POST()

if __name__ == '__main__':
    from http.server import ThreadingHTTPServer
    # Every mock hostname shares this listener. Chrome opens connections to many
    # origins at once; the default backlog of five resets startup asset requests.
    ThreadingHTTPServer.request_queue_size = 128
    ThreadingHTTPServer.daemon_threads = True
    httpd = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    from runtime_support import local_certificate
    cert, key = local_certificate(HERE / 'runtime')
    ctx.load_cert_chain(str(cert), str(key))
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    print('[518 mock] offline server https://127.0.0.1:%s; source=%s; spins=%s' %
          (PORT, source, {bet:len(samples) for bet,samples in spins.items()}), flush=True)
    httpd.serve_forever()
