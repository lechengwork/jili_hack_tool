#!/usr/bin/env python3
"""Export application payloads only; no login tokens, GRV or capture keys."""
import json,sys,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'routex'));import fg5
from math_adapter import wire_to_math,math_to_wire

def build():
 summary=json.loads((HERE/'final_capture_summary.json').read_text());rows=[];spins=0
 for info in summary['sessions']:
  session=HERE/'webcap'/info['session'];raw={r['seq']:r for r in map(json.loads,(session/'exchanges.jsonl').read_text().splitlines())}
  decoded=list(map(json.loads,(session/'exchanges_ordered_verified.jsonl').read_text().splitlines()))
  for d in decoded:
   if d.get('_sig_ok')is not True:raise ValueError('Unverified capture row')
   action=fg5.parse_fields(bytes.fromhex(raw[d['idx']]['req_body_hex'])).get(2,b'')
   # f3 token and f4 ephemeral key from transport are deliberately never exported.
   row={'type':d['type'],'ret':d['ret'],'action_hex':action.hex(),'raw_hex':bytes(d['raw']).hex()}
   if d['type']==0 and d['ret']==0:
    value=wire_to_math(bytes(d['raw']));assert math_to_wire(value)==bytes(d['raw']);row['round_id']=value['roundIndexV2'];spins+=1
   rows.append(row)
 if spins!=438:raise ValueError('Unexpected source sample count')
 (HERE/'replay_samples.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
 print(json.dumps({'responses':len(rows),'verified_spins':spins,'transport_credentials_exported':False}))
if __name__=='__main__':build()
