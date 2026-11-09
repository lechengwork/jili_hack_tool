#!/usr/bin/env python3
"""Verify, decrypt and sort a snapshot of one 807 capture session."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import subprocess

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'routex'))
import decrypt_capture as dc
import fg5
from live_math import export_spin
sys.path.insert(0, str(HERE))
from math_adapter import wire_to_math, math_to_wire

ap = argparse.ArgumentParser()
ap.add_argument('session', nargs='?', help='Defaults to current_session.txt')
args = ap.parse_args()
session = Path(args.session or (HERE / 'current_session.txt').read_text(encoding='utf-8').strip())
records = [json.loads(line) for line in (session / 'exchanges.jsonl').read_text(encoding='utf-8').splitlines() if line]
if not records:
    raise SystemExit('No completed exchanges in this session')
pubs = {fg5.parse_fields(bytes.fromhex(r['req_body_hex'])).get(4) for r in records}
if len(pubs) != 1 or not isinstance(next(iter(pubs)), bytes):
    raise SystemExit('Expected exactly one client public key; do not mix sessions')
private = dc.find_priv(dc.load_grv_outputs(str(session / 'grv.jsonl')), next(iter(pubs))) \
    if (session / 'grv.jsonl').exists() else None
key = dc.shared_key(private) if private else bytes.fromhex(json.loads((session / 'key.json').read_text(encoding='utf-8'))['key'])
rows = []
for rec in sorted(records, key=lambda r: int(r['seq'])):
    d = dc.decrypt_response(bytes.fromhex(rec['resp_body_hex']), key)
    if not d['_sig_ok']:
        raise SystemExit('Signature verification failed at seq=%s' % rec['seq'])
    req = fg5.parse_fields(bytes.fromhex(rec['req_body_hex']))
    d.update(idx=rec['seq'], kind=dc.kind_of(fg5.parse_fields(req.get(2, b''))))
    rows.append(d)
dest = session / 'export'
dest.mkdir(exist_ok=True)
(dest / 'exchanges_ordered.jsonl').write_text(
    ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
summary = {'exchanges': len(rows), 'types': dict(Counter(r['type'] for r in rows)),
           'spin_requests': sum(r['kind'] == 'spin' for r in rows), 'all_signatures_valid': True}
(dest / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
# Re-run the same writer to backfill replies missed before the key became known.
math_reports = [export_spin(row, HERE, session, wire_to_math, math_to_wire) for row in rows]
math_reports = [r for r in math_reports if r is not None]
summary.update(math_written=sum(r['ok'] for r in math_reports),
               math_errors=sum(not r['ok'] for r in math_reports))
(dest / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps(summary))
print('Export: ' + str(dest))
