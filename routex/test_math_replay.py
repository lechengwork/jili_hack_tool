"""Encrypted HTTP tests: 518/807 replay follows live math without finish/restart."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import socket
import ssl
import struct
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from math_replay import MathReplay, input_key
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import fg5
ROOT = Path(__file__).resolve().parent.parent


def load_codec(gid):
    spec = importlib.util.spec_from_file_location('codec_' + gid, ROOT / 'games' / gid / 'math_adapter.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class MathReplayTests(unittest.TestCase):
    def test_explicit_round_order_snapshot_and_invalid_start(self):
        codec = load_codec('807')
        samples = [json.loads(x) for x in (ROOT / 'games/807/math/all.jsonl').read_text().splitlines()]
        first = samples[0]
        second = next(x for x in samples[1:] if x['spinReq'] == first['spinReq'])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for sample in [first, second]:(path / (sample['roundIndexV2'] + '.json')).write_text(json.dumps(sample))
            rounds = second['roundIndexV2'] + ',' + first['roundIndexV2']
            pool = MathReplay(path, codec.math_to_wire, rounds, watch=False)
            key = input_key(first['spinReq'])
            self.assertEqual([codec.wire_to_math(x)['roundIndexV2'] for x in pool.pools[key]], rounds.split(','))
            frozen = pool.pools[key][0]
            (path / (second['roundIndexV2'] + '.json')).write_text('{bad json')
            self.assertEqual(pool.refresh()[key][0], frozen)
            with self.assertRaises(ValueError):MathReplay(path, codec.math_to_wire, rounds)

    def test_both_games_reload_edits_additions_and_modes_over_encrypted_http(self):
        for gid, route in [('518', '/cj/'), ('807', '/fg1000/')]:
            with self.subTest(game=gid), tempfile.TemporaryDirectory(prefix='math-replay-') as directory:
                path = Path(directory); codec = load_codec(gid)
                samples = [json.loads(x) for x in (ROOT / 'games' / gid / 'math/all.jsonl').read_text().splitlines()]
                chosen = {}
                for sample in samples:
                    key = (sample['spinReq']['bet'], json.dumps(sample['spinReq']['special'], sort_keys=True))
                    chosen.setdefault(key, sample)
                selected = list(chosen.values())
                for sample in selected:(path / (sample['roundIndexV2'] + '.json')).write_text(json.dumps(sample))
                with socket.socket() as sock:sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
                env = dict(os.environ, MOCK_PORT=str(port), REPLAY_SOURCE='math', MATH_DIR=directory, WATCH_MATH='1')
                for k in ['REPLAY_ROUNDS', 'REPLAY_SESSION', 'SCHEMA_PROBE']:env.pop(k, None)
                with (path / 'server.log').open('w') as log:
                    process = subprocess.Popen([sys.executable, '-B', '-u', str(ROOT / 'games' / gid / 'mock_server.py')], env=env, stdout=log, stderr=log)
                    try:
                        ctx = ssl._create_unverified_context(); base = 'https://127.0.0.1:' + str(port)
                        for _ in range(100):
                            if process.poll() is not None:self.fail((path / 'server.log').read_text())
                            try:
                                with urllib.request.urlopen(base + route, context=ctx, timeout=1):break
                            except OSError:time.sleep(.1)
                        else:self.fail('Server did not start')
                        keys = json.loads((ROOT / 'routex/mockkeys.json').read_text())
                        private = x25519.X25519PrivateKey.generate()
                        pub = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
                        shared = private.exchange(x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(keys['x25519_pub'])))
                        signer = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(keys['ed25519_pub']))

                        def request(typ, action=b''):
                            body = fg5.field_varint(1, typ) + fg5.field_bytes(2, action) + fg5.field_bytes(3, bytes(20)) + fg5.field_bytes(4, pub)
                            with urllib.request.urlopen(urllib.request.Request(base + route + 'req', data=body), context=ctx, timeout=10) as response:wire = response.read()
                            signer.verify(wire[:64], wire[64:])
                            fields = fg5.parse_fields(AESGCM(shared).decrypt(wire[64:76], wire[76:], b''))
                            return fields.get(7, 0), fields.get(5, b'')

                        def action(sample):
                            info = fg5.parse_fields(fg5.parse_fields(codec.math_to_wire(sample))[23])
                            out = fg5.enc_tag(1, 1) + info[1]
                            if 23 in info:out += fg5.field_bytes(23, info[23])
                            out += fg5.field_bytes(25, b'\x08\0\x10\0\x20\0')
                            if 26 in info:out += fg5.field_bytes(26, info[26])
                            return out

                        def spin(sample):
                            ret, raw = request(0, action(sample)); self.assertEqual(ret, 0)
                            actual = codec.wire_to_math(raw)
                            for k in ['data', 'spinReq', 'postMoney']:self.assertEqual(actual[k], sample[k])
                            ret, balance = request(2); self.assertEqual(ret, 0)
                            cash = struct.unpack('<d', fg5.parse_fields(fg5.parse_fields(balance)[1])[2])[0]
                            self.assertEqual(cash, sample['postMoney'])
                            return actual

                        self.assertEqual(request(1)[0], 0)
                        for sample in selected:spin(sample)
                        edited = copy.deepcopy(selected[0]); edited['postMoney'] += 7
                        file = path / (edited['roundIndexV2'] + '.json'); file.write_text(json.dumps(edited))
                        spin(edited)  # Same running server/client, no finish or restart.
                        file.write_text('{invalid json')
                        self.assertEqual(request(0, action(edited))[0], 400)  # No stale/wire fallback.
                        file.write_text(json.dumps(edited)); spin(edited)
                        added = copy.deepcopy(edited)
                        added['roundIndexV2'] = str(int(edited['roundIndexV2']) + 1000)
                        added['postMoney'] += 9
                        (path / (added['roundIndexV2'] + '.json')).write_text(json.dumps(added))
                        observed = []
                        for _ in range(2):
                            ret, raw = request(0, action(added)); self.assertEqual(ret, 0)
                            observed.append(codec.wire_to_math(raw)['postMoney'])
                        self.assertIn(added['postMoney'], observed)
                        # A new valid bet does not depend on a pre-captured action mapping.
                        novel = copy.deepcopy(edited); novel['spinReq']['bet'] = 123.0
                        novel['roundIndexV2'] = str(int(edited['roundIndexV2']) + 2000)
                        (path / (novel['roundIndexV2'] + '.json')).write_text(json.dumps(novel)); spin(novel)
                        if gid == '518':
                            ordinary = copy.deepcopy(edited)
                            ordinary['spinReq'] = {'bet': 0.1, 'special': {}}
                            ordinary['roundIndexV2'] = str(int(edited['roundIndexV2']) + 3000)
                            ordinary['postMoney'] += 19
                            (path / (ordinary['roundIndexV2'] + '.json')).write_text(json.dumps(ordinary))
                            spin(ordinary)
                            special = next(x for x in selected if x['spinReq']['special'])
                            self.assertEqual(special['spinReq']['bet'], 0.1)
                            spin(special)
                        if gid == '807':
                            invalid = action(selected[0]) + fg5.field_varint(99, 1)
                            self.assertEqual(request(0, invalid)[0], 400)
                        print('PASS', gid, ': modes', len(selected), '; edit/add/repair/new bet reload; encrypted signature and balance verified')
                    finally:
                        process.terminate()
                        try:process.wait(timeout=10)
                        except subprocess.TimeoutExpired:process.kill(); process.wait()


if __name__ == '__main__':unittest.main()
