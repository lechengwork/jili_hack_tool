"""Encrypted integration test on a temporary math copy; never edits shared math."""
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'routex'))
import fg5
sys.path.insert(0, str(HERE))
from math_adapter import fields, field, records, wire_to_math, math_to_wire
from replay_pool import action_key

def run():
    rows = json.loads((HERE / 'replay_samples.json').read_text())
    sample = next(r for r in rows if r['type'] == 0 and r['ret'] == 0
                  and 23 not in fields(bytes.fromhex(r['action_hex']))
                  and 26 not in fields(bytes.fromhex(r['action_hex'])))
    original = json.loads((HERE / 'math' / (sample['round_id'] + '.json')).read_text())
    action = bytes.fromhex(sample['action_hex'])
    keys = json.loads((HERE.parent.parent / 'routex/mockkeys.json').read_text())
    signer = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(keys['ed25519_pub']))
    private = x25519.X25519PrivateKey.generate()
    pub = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    shared = private.exchange(x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(keys['x25519_pub'])))
    with tempfile.TemporaryDirectory(prefix='jili573-reload-') as directory:
        path = Path(directory) / (sample['round_id'] + '.json')
        path.write_text(json.dumps(original))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        base = 'http://127.0.0.1:%d' % port
        log = (HERE / 'replay/verify-reload.log').open('w')
        env = dict(os.environ, REPLAY_PORT=str(port), REPLAY_SOURCE='math',
                   MATH_DIR=directory, WATCH_MATH='1', SELECT_ROUNDS='', BONUS_FIRST='0')
        process = subprocess.Popen([sys.executable, '-B', '-u', str(HERE / 'replay_server.py')],
                                   env=env, stdout=log, stderr=log)
        def request(payload):
            body = (fg5.field_varint(1, 0) + fg5.field_bytes(2, payload)
                    + fg5.field_bytes(3, bytes(20)) + fg5.field_bytes(4, pub))
            with urllib.request.urlopen(urllib.request.Request(base + '/rc2/req', data=body), timeout=5) as response:
                wire = response.read()
            signer.verify(wire[:64], wire[64:])
            out = fields(AESGCM(shared).decrypt(wire[64:76], wire[76:], b''))
            return out.get(7, (0, 0))[1], out.get(5, (2, b''))[1]
        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('Replay server exited')
                try:
                    urllib.request.urlopen(base + '/__replay_status', timeout=.5).close()
                    break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Replay startup timed out')
            assert request(action)[0] == 0
            edited = json.loads(json.dumps(original))
            edited['data']['TotalWin'] += 7.25
            edited['postMoney'] += 7.25
            # Verify a board edit too, not only metadata.
            symbol = 2 if original['data']['RoundQueue'][0]['Symbol'][0]['Col'][0] == 1 else 1
            edited['data']['RoundQueue'][0]['Symbol'][0]['Col'][0] = symbol
            path.write_text(json.dumps(edited))
            ret, raw = request(action)
            actual = wire_to_math(raw)
            assert ret == 0 and actual['data']['TotalWin'] == edited['data']['TotalWin']
            assert actual['totalWin'] == edited['data']['TotalWin']
            assert actual['postMoney'] == edited['postMoney']
            assert actual['data']['RoundQueue'][0]['Symbol'][0]['Col'][0] == symbol
            # Invalid content must not fall back to stale results, and recovery is live.
            path.write_text('{invalid')
            assert request(action) == (400, b'')
            path.write_text(json.dumps(edited))
            assert request(action)[0] == 0
            # Editing named input moves the sample into the new bet's pool.
            edited['spinReq']['bet'] = 6000.0
            path.write_text(json.dumps(edited))
            assert request(action) == (400, b'')
            changed_action = b''.join(field(1, 1, struct.pack('<d', 6000.0)) if n == 1 else raw
                                      for n, w, v, raw in records(action))
            assert request(changed_action)[0] == 0
            # Missing and explicit selector-zero normalize within a present option only.
            assert action_key(changed_action + field(26, 2, b'')) != action_key(changed_action)
            assert request(changed_action + field(26, 2, b'\x08\x01')) == (400, b'')
            assert request(changed_action + field(99, 0, b'\x01')) == (400, b'')
            report = {'encrypted_hot_reload': True, 'edited_board_win_and_balance_applied': True,
                      'duplicate_total_win_synchronized': True, 'invalid_json_fails_closed': True,
                      'recovery_without_restart': True, 'edited_bet_rekeys_pool': True,
                      'unknown_mode_and_fields_rejected': True, 'shared_math_modified': False}
            (HERE / 'replay_math_reload_validation.json').write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps(report))
        finally:
            process.terminate()
            process.wait(timeout=10)
            log.close()

if __name__ == '__main__':
    run()
