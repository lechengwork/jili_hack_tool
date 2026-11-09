#!/usr/bin/env python3
"""Read-only verification of normal-mode Bonus. Never places or stops wagers."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));import math_adapter as a
from request_adapter import request_to_math,math_to_request
sys.path.insert(0,str(HERE.parent.parent/'routex'));import decrypt_capture as dc,fg5

def complete_lines(path):
 if not path.exists():return []
 return [json.loads(l)for l in path.read_bytes().splitlines(keepends=True)if l.endswith(b'\n')]

def check():
 session=Path((HERE/'current_session.txt').read_text().strip())
 decoded=complete_lines(session/'exchanges_ordered.jsonl');spins=[d for d in decoded if d.get('type')==0 and d.get('ret')==0 and d.get('_sig_ok')is True]
 report={'session':session.name,'signed_successful_spins':len(spins),'published_math':len(list((session/'math').glob('[0-9]*.json'))),'normal_spins':0,'normal_bonus':False,'errors':[]}
 candidates=[]
 for d in spins:
  obj=a.decode_message(bytes(d['raw']),'Envelope')
  if obj['data']['Extra']==0:
   report['normal_spins']+=1
   if obj['data']['GetBonus']==2:candidates.append((d,obj))
 if candidates:
  raw={r['seq']:r for r in complete_lines(session/'exchanges.jsonl')};key=bytes.fromhex(json.loads((session/'key.json').read_text())['key'])
  for d,obj in candidates:
   r=raw[d['idx']];action=fg5.parse_fields(bytes.fromhex(r['req_body_hex'])).get(2,b'');fields=a.fields(action)
   if 23 in fields or 26 in fields:continue
   fresh=dc.decrypt_response(bytes.fromhex(r['resp_body_hex']),key)
   if fresh['_sig_ok']is not True or fresh['raw']!=d['raw']:raise ValueError('Candidate signature/raw mismatch')
   m=a.wire_to_math(bytes(fresh['raw']));rid=m['roundIndexV2'];req=request_to_math(action)
   if math_to_request(req)!=action:raise ValueError('Request roundtrip mismatch')
   if a.math_to_wire(m)!=bytes(fresh['raw']):raise ValueError('Payload roundtrip mismatch')
   for path in [HERE/'math'/(rid+'.json'),session/'math'/(rid+'.json')]:
    if json.loads(path.read_text())!=m:raise ValueError('Candidate math mismatch')
   report.update(normal_bonus=True,round_id=rid,idx=d['idx'],signature_verified=True,original_codec_verified=True,complete_payload_roundtrip=True,request_roundtrip=True,extra_and_purchase_absent_in_original_request=True,GetBonus=m['data']['GetBonus'],PlateSymbol_count=len(m['data']['PlateSymbol']))
   (session/'normal_bonus_detected.json').write_text(json.dumps(report,indent=2)+'\n');(HERE/'normal_bonus_detected.json').write_text(json.dumps(report,indent=2)+'\n');break
 for name in ['math_errors.jsonl','math_conflicts.jsonl','decode_errors.jsonl']:
  rows=complete_lines(session/name)
  if rows:report['errors'].append({'log':name,'count':len(rows)})
 (session/'normal_bonus_check.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report));return report
if __name__=='__main__':check()
