#!/usr/bin/env python3
"""Reverify one session; export credential-free wire vectors and math samples."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'routex'))
import decrypt_capture as dc
import fg5
from live_math import export_spin
from math_adapter import wire_to_math,math_to_wire


def finish(session):
    session=Path(session)
    path=session/'exchanges.jsonl'
    # Snapshot complete lines only; an in-flight final line is processed next run.
    lines=path.read_bytes().splitlines(keepends=True)
    records=[json.loads(l) for l in lines if l.endswith(b'\n') and l.strip()]
    if not records:raise ValueError('No completed exchanges')
    pubs={fg5.parse_fields(bytes.fromhex(r['req_body_hex'])).get(4) for r in records}
    if len(pubs)!=1 or not isinstance(next(iter(pubs)),bytes):raise ValueError('Mixed/missing client keys')
    private=dc.find_priv(dc.load_grv_outputs(str(session/'grv.jsonl')),next(iter(pubs))) if (session/'grv.jsonl').exists() else None
    key=dc.shared_key(private) if private else bytes.fromhex(json.loads((session/'key.json').read_text())['key'])
    rows=[];samples=[];reports=[];ids=set()
    for rec in sorted(records,key=lambda r:int(r['seq'])):
        d=dc.decrypt_response(bytes.fromhex(rec['resp_body_hex']),key)
        if not d['_sig_ok']:raise ValueError('Invalid signature seq=%s'%rec['seq'])
        req=fg5.parse_fields(bytes.fromhex(rec['req_body_hex']));action=req.get(2,b'')
        d.update(idx=rec['seq'],kind=dc.kind_of(fg5.parse_fields(action)))
        rows.append(d)
        # Omit SSO/request token/public key/GRV; only application-layer action survives.
        sample={'idx':d['idx'],'type':d['type'],'ret':d['ret'],
                'action_hex':action.hex(),'raw_hex':bytes(d['raw']).hex()}
        samples.append(sample)
        report=export_spin(d,HERE,session,wire_to_math,math_to_wire)
        if report:
            reports.append(report)
            if report['ok']:ids.add(report['round_id'])
    dest=session/'export';dest.mkdir(exist_ok=True)
    (dest/'exchanges_ordered.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    (dest/'replay_samples.json').write_text(json.dumps(samples,indent=2)+'\n')
    summary={'exchanges':len(rows),'types_ret':dict(Counter('%s/%s'%(r['type'],r['ret']) for r in rows)),
             'all_signatures_valid':True,'math_written':sum(r['ok'] for r in reports),
             'math_errors':sum(not r['ok'] for r in reports),'unique_rounds':len(ids)}
    (dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)
    if summary['math_errors']:raise ValueError('Math export errors; original capture retained')
    return samples,summary


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('session',nargs='?');ap.add_argument('--publish-replay',action='store_true')
    a=ap.parse_args();session=a.session or (HERE/'current_session.txt').read_text().strip()
    samples,_=finish(session)
    if a.publish_replay:
        if not any(r['type']==0 and r['ret']==0 for r in samples):raise ValueError('No successful SPIN')
        (HERE/'replay_samples.json').write_text(json.dumps(samples,indent=2)+'\n')
