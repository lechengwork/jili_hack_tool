"""Reverify complete captured lines; use the same exporter as live capture."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'routex'))
import decrypt_capture as dc
sys.path.insert(0, str(HERE))
from math_adapter import wire_to_math, math_to_wire
from live_math_573 import export_spin

def scan(session, offset=0):
    key_path = session / 'key.json'
    source = session / 'exchanges.jsonl'
    stats = {'responses': 0, 'verified_success_spins': 0, 'published': 0, 'errors': 0, 'offset': offset}
    if not key_path.exists() or not source.exists():
        return stats
    key = bytes.fromhex(json.loads(key_path.read_text())['key'])
    with source.open('rb') as captured:
        captured.seek(offset)
        lines = captured.read().splitlines(keepends=True)
    for line in lines:
        if not line.endswith(b'\n'):
            break
        stats['offset'] += len(line)
        try:
            record = json.loads(line)
            decoded = dc.decrypt_response(bytes.fromhex(record['resp_body_hex']), key)
            decoded['idx'] = record.get('seq')
            stats['responses'] += 1
            if decoded.get('_sig_ok') is not True:
                raise ValueError('Response signature invalid')
            if decoded.get('type') == 0 and decoded.get('ret') == 0:
                stats['verified_success_spins'] += 1
                report = export_spin(decoded, HERE, session, wire_to_math, math_to_wire)
                stats['published' if report and report['ok'] else 'errors'] += 1
        except Exception as error:
            stats['errors'] += 1
            with (session / 'revalidation_errors.jsonl').open('a') as target:
                target.write(json.dumps({'error': str(error)}) + '\n')
    return stats

if __name__ == '__main__':
    session = Path((HERE / 'current_session.txt').read_text().strip())
    stats = scan(session)
    (session / 'validation.json').write_text(json.dumps(stats, indent=2) + '\n')
    print(json.dumps(stats))
