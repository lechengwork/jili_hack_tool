#!/usr/bin/env python3
"""Offline 807 wire replay; never reads live login credentials or session keys."""
from collections import defaultdict
import copy
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
PORT = int(os.environ.get('MOCK_PORT', '8808'))
ROWS = json.loads((HERE / 'replay_samples.json').read_text())
# Override inherited capture/replay settings explicitly; no original 696 samples.
os.environ.update(STATIC=str(HERE / 'static'), HOST='127.0.0.1', PORT=str(PORT),
                  TLS='1', GAME_PATH='/fg1000/', CAPTURE='0', LIVE_DECODE='0',
                  INJECT_BUNDLE='1', REPLAY=str(HERE / 'unused-replay.jsonl'),
                  REPLAY_SPINS='', REPLAY_LOG='0', ASSET_FALLBACK='0',
                  VERBOSE=os.environ.get('MOCK_VERBOSE', '0'), HS_DELAY='0', SSO_DELAY='0',
                  SHARED_HEX_PATH=str(HERE / 'runtime/mock_shared.hex'))
sys.path.insert(0, str(ROOT / 'routex'))
import server
import fg5

server.WASM_SHIM = (HERE / 'wasm_patch_shim.js').read_text()
server.WASM_SHIM = (ROOT / 'routex/err_probe_shim.js').read_text() + '\n' + server.WASM_SHIM
server.SHARED_ROOT = str(HERE / 'static')
server.SAMPLES = {}
by_action = defaultdict(list)
spins = defaultdict(list)
for row in ROWS:
    row['raw'] = bytes.fromhex(row['raw_hex'])
    action = bytes.fromhex(row['action_hex'])
    server.SAMPLES.setdefault(row['type'], row['raw'])
    by_action[(row['type'], action)].append(row)
    if row['type'] == 0 and row['ret'] == 0:
        spins[action].append(row['raw'])
if not spins:
    raise ValueError('No successful 807 replay samples')
source = os.environ.get('REPLAY_SOURCE', 'wire')
if source == 'math':
    from math_adapter import math_to_wire
    from math_adapter import wire_to_math
    actions_by_input = {(wire_to_math(pool[0])['spinReq']['bet'], wire_to_math(pool[0])['data']['ante_mode']): action for action, pool in spins.items()}
    spins.clear()
    directory = Path(os.environ.get('MATH_DIR', str(HERE / 'math')))
    for file in sorted(directory.glob('*.json')):
        if not file.stem.isdigit():
            continue
        sample = json.loads(file.read_text())
        action = actions_by_input.get((sample['spinReq']['bet'], sample['data']['ante_mode']))
        if action is None:
            raise ValueError('Math sample uses an uncaptured bet/action: ' + file.name)
        spins[action].append(math_to_wire(sample))
    if not spins:
        raise ValueError('No math samples selected')
elif source != 'wire':
    raise ValueError('REPLAY_SOURCE must be wire or math')
selected = os.environ.get('REPLAY_ROUNDS', '')
if selected:
    lookup = {str(fg5.parse_fields(raw)[20]): (action, raw)
              for action, pool in spins.items() for raw in pool}
    wanted = selected.split(',')
    if any(rid not in lookup for rid in wanted):
        raise ValueError('Unknown round ID in REPLAY_ROUNDS')
    spins.clear()
    for rid in wanted:
        action, raw = lookup[rid]
        spins[action].append(raw)

# Each ephemeral public key has independent replay position and balance.
states = {}
lock = threading.Lock()


def replace_field(buf, number, wire, value):
    """Replace one envelope field, retaining all other wire bytes and ordering."""
    out = bytearray()
    pos = 0
    found = False
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
            size, pos = fg5.dec_varint(buf, pos)
            pos += size
        elif wt == 5:
            pos += 4
        else:
            raise ValueError('Unsupported protobuf wire type')
        if pos > len(buf):
            raise ValueError('Truncated protobuf')
        if tag >> 3 == number:
            out.extend(replacement)
            found = True
        else:
            out.extend(buf[start:pos])
    if not found:
        out.extend(replacement)
    return bytes(out)


def pick_response(req):
    typ, action = req['seq'], req['action']
    with lock:
        state = states.setdefault(bytes(req['client_pub']), {
            'indices': defaultdict(int), 'actions': defaultdict(int),
            'balance': None, 'last_rid': 0,
        })
        if typ == 0:
            pool = spins.get(action)
            if not pool:
                return 0, b'', 400, 'unsupported-bet-or-mode'
            index = state['indices'][action]
            raw = pool[index % len(pool)]
            state['indices'][action] += 1
            fields = fg5.parse_fields(raw)
            rid = fields[20]
            if rid <= state['last_rid']:
                rid = (state['last_rid'] // 1000 + 1) * 1000 + rid % 1000
                raw = replace_field(raw, 20, 0, fg5.enc_varint(rid))
            state['last_rid'] = rid
            state['balance'] = fields[6]
            print('[807 mock] spin=%s round=%s balance=%s' %
                  (index + 1, rid, struct.unpack('<d', fields[6])[0]), flush=True)
            return 0, raw, 0, 'spin[%s]' % index
        if typ == 2 and state['balance'] is not None:
            template = server.SAMPLES[2]
            core = replace_field(fg5.parse_fields(template)[1], 2, 1, state['balance'])
            return 2, replace_field(template, 1, 2, fg5.enc_varint(len(core)) + core), 0, 'balance'
        matches = by_action.get((typ, action))
        if not matches:
            matches = [row for row in ROWS if row['type'] == typ]
        if not matches:
            return typ, b'', 400, 'unsupported-type'
        key = (typ, action)
        index = state['actions'][key]
        state['actions'][key] += 1
        row = matches[min(index, len(matches) - 1)]
        return typ, row['raw'], row['ret'], 'captured-type[%s]' % typ


server.pick_response = pick_response
# Synthetic local login profile. No live SSO, JWT or real account is required.
server.SSO_JSON = copy.deepcopy(server.SSO_JSON)
server.SSO_JSON['token'] = '0' * 40
server.SSO_JSON['profile'].update(id='', aid=0, siteId=0, nickname='mock807',
                                account='mock807', meta={'agentAccount': 'mock807'})


class Handler(server.Handler):
    def _send(self, code, body=b'', ctype='application/octet-stream', extra=None):
        if body == b'{"code":0,"data":{},"message":""}':
            print('[807 unhandled] ' + urlsplit(self.path).path, flush=True)
        if (ctype.startswith('text/') or 'javascript' in ctype or 'json' in ctype) and 'charset=' not in ctype:
            ctype += '; charset=utf-8'
        super()._send(code, body, ctype, extra)

    def auxiliary(self):
        path = urlsplit(self.path).path
        # Explicit optional-service stubs; not captured 807 business responses.
        if path.startswith(('/vipservice/', '/favoriteservice/', '/rankingservice/',
                            '/subagentservice/', '/promotionservice/', '/longhu/', '/smartnotice/')):
            self._send(200, b'', 'application/x-protobuf')
            return True
        return False

    def do_GET(self):
        if self.auxiliary():
            return
        if urlsplit(self.path).path == '/fg1000/' and self.headers.get('Host', '').split(':')[0] == server.GS_HOST:
            self._send(204)
            return
        super().do_GET()

    def do_POST(self):
        path = urlsplit(self.path).path
        if path.startswith(('/vipservice/', '/favoriteservice/', '/rankingservice/',
                            '/subagentservice/', '/promotionservice/', '/longhu/', '/smartnotice/')):
            self._read_body()
            self.auxiliary()
            return
        super().do_POST()


if __name__ == '__main__':
    from http.server import ThreadingHTTPServer
    from runtime_support import local_certificate
    ThreadingHTTPServer.request_queue_size = 128
    ThreadingHTTPServer.daemon_threads = True
    httpd = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    cert, key = local_certificate(HERE / 'runtime')
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(cert), str(key))
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    print('[807 mock] offline https://127.0.0.1:%s; source=%s; samples=%s; action pools=%s' %
          (PORT, source, sum(map(len, spins.values())), len(spins)), flush=True)
    httpd.serve_forever()
