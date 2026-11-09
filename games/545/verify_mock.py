#!/usr/bin/env python3
"""Exercise the real HTTPS mock, including encryption and a replay wraparound."""
import argparse
import json
import os
from pathlib import Path
import socket
import ssl
import struct
import subprocess
import sys
import time
import tempfile
import shutil
import urllib.request

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'routex'))
import fg5

ap = argparse.ArgumentParser()
ap.add_argument('--source', choices=['wire','math'], default='wire')
ap.add_argument('--port', type=int, help='Verify an already running mock')
args = ap.parse_args()
process = None
log = None
snapshot = None
if args.source == 'math' and not args.port:
    snapshot = tempfile.TemporaryDirectory(prefix='jili545-verify-')
    original = Path(os.environ.get('MATH_DIR', str(HERE / 'math')))
    for file in original.glob('*.json'):
        if file.stem.isdigit():shutil.copyfile(file, Path(snapshot.name) / file.name)
    os.environ['MATH_DIR'] = snapshot.name
    os.environ['WATCH_MATH'] = '0'
if args.port:
    port = args.port
else:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    (HERE / 'runtime').mkdir(exist_ok=True)
    log = (HERE / 'runtime/verification.log').open('w')
    process = subprocess.Popen([sys.executable, '-B', '-u', str(HERE / 'mock_server.py')],
                               env=dict(os.environ, MOCK_PORT=str(port), REPLAY_SOURCE=args.source), stdout=log, stderr=log)

url = 'https://127.0.0.1:%s' % port
ctx = ssl._create_unverified_context()
keys = json.loads((HERE.parent.parent / 'routex/mockkeys.json').read_text())
signer = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(keys['ed25519_pub']))
server_pub = x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(keys['x25519_pub']))
rows = json.loads((HERE / 'replay_samples.json').read_text())
spins = [r for r in rows if r['type'] == 0 and r['ret'] == 0]
if args.source == 'math':
    from math_adapter import math_to_wire
    spins = []
    directory = Path(os.environ.get('MATH_DIR', str(HERE / 'math')))
    for file in sorted(directory.glob('*.json')):
        if not file.stem.isdigit():continue
        sample = json.loads(file.read_text())
        raw = math_to_wire(sample)
        action = fg5.parse_fields(raw)[23]
        spins.append({'type':0, 'ret':0, 'raw_hex':raw.hex(), 'action_hex':action.hex()})



class Client:
    def __init__(self):
        private = x25519.X25519PrivateKey.generate()
        self.pub = private.public_key().public_bytes(serialization.Encoding.Raw,
                                                     serialization.PublicFormat.Raw)
        self.shared = private.exchange(server_pub)

    def request(self, typ, action=b''):
        body = (fg5.field_varint(1, typ) + fg5.field_bytes(2, action)
                + fg5.field_bytes(3, bytes(20)) + fg5.field_bytes(4, self.pub))
        req = urllib.request.Request(url + '/cc3x3/req', data=body,
                                     headers={'Content-Type': 'application/x-protobuf'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            wire = response.read()
        signer.verify(wire[:64], wire[64:])
        pt = AESGCM(self.shared).decrypt(wire[64:76], wire[76:], b'')
        f = fg5.parse_fields(pt)
        assert f.get(3, 0) == typ
        assert abs(f[1] - int(time.time() * 1000)) < 10000
        return f.get(7, 0), f.get(5, b'')


try:
    for _ in range(100):
        if process and process.poll() is not None:
            raise RuntimeError('Mock failed to start; inspect runtime/verification.log')
        try:
            with urllib.request.urlopen(url + '/cc3x3/', context=ctx, timeout=1) as r:
                assert r.headers.get_content_charset() == 'utf-8'
            break
        except OSError:
            time.sleep(0.1)
    else:
        raise RuntimeError('Mock did not become ready')
    with urllib.request.urlopen(url + '/cc3x3/src/polyfills.bundle.5adbf.js', context=ctx) as r:
        assert b'installed C2 compile-hook' in r.read()
    with urllib.request.urlopen(urllib.request.Request(url + '/sso-login.api', data=b'{}'), context=ctx) as r:
        sso = json.load(r)
        assert sso['token'] == '0' * 40
        assert sso['profile']['account'] == 'mock545'
    a, b = Client(), Client()
    # Interleaved init messages must resolve by type/action, not a global cursor.
    for client in (a, b):
        for row in [r for r in rows if r['type'] != 0][:15]:
            ret, raw = client.request(row['type'], bytes.fromhex(row['action_hex']))
            assert ret == row['ret'] and raw == bytes.fromhex(row['raw_hex'])
    last = 0
    pools = {}
    for row in spins:
        pools.setdefault(row['action_hex'], []).append(row)
    sequence = spins + [row for pool in pools.values() for row in (pool * 2)[:2]]
    count = len(sequence)
    for row in sequence:
        ret, raw = a.request(0, bytes.fromhex(row['action_hex']))
        assert ret == 0
        actual, expected = fg5.parse_fields(raw), fg5.parse_fields(bytes.fromhex(row['raw_hex']))
        rid = actual.pop(20)
        expected.pop(20)
        assert actual == expected, 'Replay changed payload outside round ID'
        assert rid > last and rid % 1000 == 545
        last = rid
        ret, balance = a.request(2)
        assert ret == 0
        assert fg5.parse_fields(fg5.parse_fields(balance)[1])[2] == actual[6]
    ret, first_b = b.request(0, bytes.fromhex(spins[0]['action_hex']))
    assert ret == 0 and first_b == bytes.fromhex(spins[0]['raw_hex']), 'Client state leaked'
    unsupported = fg5.field_bytes(1, struct.pack('<d', 99999.0))
    assert a.request(0, unsupported) == (400, b'')
    assert a.request(999) == (400, b'')
    for prefix in ('vipservice', 'favoriteservice', 'rankingservice', 'subagentservice', 'promotionservice', 'longhu', 'smartnotice'):
        with urllib.request.urlopen(urllib.request.Request(url + '/' + prefix + '/test', data=b''), context=ctx) as r:
            assert r.read() == b'' and r.headers.get_content_type() == 'application/x-protobuf'
    report = {'https_crypto_verified': True, 'captured_spins': len(spins), 'action_pools_tested': len(pools),
              'consecutive_replays_tested': count, 'replay_wraparound_verified': True,
              'balance_polling_verified': True, 'client_isolation_verified': True,
              'unsupported_actions_rejected': True, 'synthetic_sso_verified': True,
              'utf8_headers_verified': True, 'browser_visual_verification': 'pending'}
    (HERE / ('mock_validation_' + args.source + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
finally:
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    if log:
        log.close()

    if snapshot:
        snapshot.cleanup()
