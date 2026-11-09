"""Verify each private session separately; export only application payloads."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'routex'))
import decrypt_capture as dc
import fg5
sys.path.insert(0, str(HERE))
from math_adapter import wire_to_math, math_to_wire
from request_adapter import request_to_math, math_to_request

def build():
    rows, sessions, seen = [], [], set()
    for session in sorted((HERE / 'webcap').iterdir()):
        capture, key_path = session / 'exchanges.jsonl', session / 'key.json'
        if not capture.exists() or not key_path.exists():
            continue
        key = bytes.fromhex(json.loads(key_path.read_text())['key'])
        data = capture.read_bytes()
        records = [json.loads(line) for line in data.splitlines(keepends=True)
                   if line.endswith(b'\n') and line.strip()]
        pubs = {fg5.parse_fields(bytes.fromhex(r['req_body_hex'])).get(4) for r in records}
        if len(pubs) != 1 or not isinstance(next(iter(pubs)), bytes):
            raise ValueError('Mixed client public keys in ' + session.name)
        count = 0
        for rec in sorted(records, key=lambda r: r['seq']):
            decoded = dc.decrypt_response(bytes.fromhex(rec['resp_body_hex']), key)
            if decoded.get('_sig_ok') is not True:
                raise ValueError('Unverified response in ' + session.name)
            request = fg5.parse_fields(bytes.fromhex(rec['req_body_hex']))
            action = request.get(2, b'')
            raw = bytes(decoded['raw'])
            # Exclude transport auth f3, ephemeral public f4, key, GRV and URLs.
            row = {'type': decoded['type'], 'ret': decoded['ret'],
                   'action_hex': action.hex(), 'raw_hex': raw.hex()}
            if decoded['type'] == 0:
                if decoded['ret'] != 0:
                    continue
                value = wire_to_math(raw)
                if math_to_wire(value) != raw or math_to_request(request_to_math(action)) != action:
                    raise ValueError('Request/response round-trip mismatch')
                rid = value['roundIndexV2']
                if rid in seen:
                    raise ValueError('Duplicate successful round: ' + rid)
                seen.add(rid)
                row['round_id'] = rid
                count += 1
            if key in raw or key in action:
                raise ValueError('Capture key detected in exported application data')
            rows.append(row)
        sessions.append({'session': session.name, 'capture_sha256': hashlib.sha256(data).hexdigest(),
                         'successful_spins': count, 'all_signatures_valid': True})
    math_ids = {p.stem for p in (HERE / 'math').glob('[0-9]*.json') if p.stem.isdigit()}
    if not seen or seen != math_ids:
        raise ValueError('Captured and published math round sets differ')
    (HERE / 'replay_samples.json').write_text(json.dumps(rows, separators=(',', ':')) + '\n')
    report = {'verified_spins': len(seen), 'responses': len(rows), 'sessions': sessions,
              'full_request_response_byte_roundtrip': True, 'transport_credentials_exported': False}
    (HERE / 'replay_sources.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))

if __name__ == '__main__':
    build()
