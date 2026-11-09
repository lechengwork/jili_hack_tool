#!/usr/bin/env python3
"""Export verified 461 application payloads, never authentication/key envelopes."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'routex'))
import fg5,decrypt_capture as dc
from math_adapter import wire_to_math,math_to_wire
from request_adapter import request_to_math,math_to_request

def build():
 summary=json.loads((HERE/'final_capture_summary.json').read_text())
 session=HERE/'webcap'/summary['session'];key=bytes.fromhex(json.loads((session/'key.json').read_text())['key'])
 source=(session/'exchanges.jsonl').read_bytes()
 if hashlib.sha256(source).hexdigest()!=summary['raw_capture_sha256']:raise ValueError('Final capture digest changed')
 rows=[];spins=0
 for line in source.splitlines(keepends=True):
  if not line.endswith(b'\n'):raise ValueError('Incomplete capture line')
  rec=json.loads(line);d=dc.decrypt_response(bytes.fromhex(rec['resp_body_hex']),key)
  if d.get('_sig_ok')is not True:raise ValueError('Unverified response')
  action=fg5.parse_fields(bytes.fromhex(rec['req_body_hex'])).get(2,b'')
  # Only application f2 is exported. Transport f3 auth and f4 key remain private.
  row={'type':d['type'],'ret':d['ret'],'action_hex':action.hex(),'raw_hex':bytes(d['raw']).hex()}
  if d['type']==0 and d['ret']==0:
   obj=wire_to_math(bytes(d['raw']));assert math_to_wire(obj)==bytes(d['raw'])
   req=request_to_math(action);assert math_to_request(req)==action
   row['round_id']=obj['roundIndexV2'];spins+=1
  if key in action or key in bytes(d['raw']):raise ValueError('Key material detected in application payload')
  rows.append(row)
 if spins!=summary['final_validation']['verified_success_spins']:raise ValueError('Sample count mismatch')
 (HERE/'replay_samples.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
 print(json.dumps({'responses':len(rows),'verified_spins':spins,'transport_credentials_exported':False}))
if __name__=='__main__':build()
