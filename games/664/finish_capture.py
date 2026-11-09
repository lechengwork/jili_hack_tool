#!/usr/bin/env python3
"""Re-decrypt this session, verify every signature and full payload, publish safely."""
import json,sys,hashlib,os
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'routex'))
import decrypt_capture as dc,fg5
sys.path.insert(0,str(HERE))
import math_adapter as a
from request_adapter import request_to_math,math_to_request
from live_math_664 import export_spin

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def finish(session):
 blob=(session/'exchanges.jsonl').read_bytes();lines=blob.splitlines(keepends=True)
 if any(not l.endswith(b'\n')for l in lines):raise ValueError('Incomplete raw capture tail; retained')
 records=[json.loads(l)for l in lines]
 if len({r['seq']for r in records})!=len(records):raise ValueError('Duplicate capture sequence')
 keyfile=session/'key.json'
 if keyfile.exists():key=bytes.fromhex(json.loads(keyfile.read_text())['key'])
 else:
  candidates=dc.load_grv_outputs(str(session/'grv.jsonl'));private=None
  for r in records:
   pub=fg5.parse_fields(bytes.fromhex(r['req_body_hex'])).get(4)
   if isinstance(pub,bytes):private=dc.find_priv(candidates,pub)
   if private:break
  if not private:raise ValueError('No matching private random value in this session')
  key=dc.shared_key(private);keyfile.touch(mode=0o600);keyfile.chmod(0o600);write(keyfile,{'key':key.hex(),'source':'recovered only from this session handshake and GRV'})
 errors=[];details=[];decoded=[];currency=False;previous_balance=None;types={};bad_replies=[]
 for r in sorted(records,key=lambda x:x['seq']):
  try:
   d=dc.decrypt_response(bytes.fromhex(r['resp_body_hex']),key);d['idx']=r['seq']
   if d.get('_sig_ok') is not True:raise ValueError('Signature invalid')
   decoded.append(d);types[str(d['type'])]=types.get(str(d['type']),0)+1
   if d['ret']!=0:bad_replies.append({'idx':d['idx'],'type':d['type'],'ret':d['ret']})
   if d['type']==1 and d['ret']==0:currency=b'IDR' in bytes(d['raw'])
   if d['type']==2 and d['ret']==0:
    b=a.fields(bytes(d['raw'])).get(1,(None,b''))[1]
    if isinstance(b,bytes):
     fields=a.fields(b)
     if 2 in fields and fields[2][0]==1:
      import struct
      previous_balance=struct.unpack('<d',fields[2][1])[0]
   if d['type']!=0 or d['ret']!=0:continue
   payload=bytes(d['raw']);m=a.wire_to_math(payload)
   if a.math_to_wire(m)!=payload:raise ValueError('Complete response payload byte mismatch')
   action=fg5.parse_fields(bytes.fromhex(r['req_body_hex'])).get(2,b'');inp=request_to_math(action)
   if math_to_request(inp)!=action:raise ValueError('Complete request byte mismatch')
   report=export_spin(d,HERE,session,a.wire_to_math,a.math_to_wire)
   if not report or not report['ok']:raise ValueError('Publish failed: '+str(report))
   rid=m['roundIndexV2'];stored=json.loads((HERE/'math'/(rid+'.json')).read_text());snapshot=json.loads((session/'math'/(rid+'.json')).read_text())
   if stored!=snapshot or stored!=m:raise ValueError('Published/session math mismatch')
   if a.math_to_wire(stored)!=payload:raise ValueError('Published math payload mismatch')
   purchase=inp.get('purchase');extra=m['data']['Extra'];mode='purchase'if purchase else {0:'normal',1:'extra_1_5',2:'extra_8'}.get(extra,'unknown_'+str(extra))
   total=m['data']['TotalWin'];balance=m['f6'];paid=previous_balance+total-balance if previous_balance is not None else None
   expected=purchase['amount']if purchase else inp['bet']*{0:1,1:1.5,2:8}.get(extra,float('nan'))
   row={'idx':d['idx'],'round_id':rid,'mode':mode,'base_bet':inp['bet'],'paid_from_consecutive_balances':paid,'expected_from_ui':expected,'debit_matches_ui':paid==expected if paid is not None else None,'balance_before':previous_balance,'balance_after':balance,'total_win':total,'GetBonus':m['data']['GetBonus'],'BonusSymbol':m['data']['BonusSymbol'],'Extra':extra,'PlateSymbol_count':len(m['data']['PlateSymbol']),'AwardDataVec_count':len(m['data']['AwardDataVec']),'payload_bytes':len(payload),'payload_sha256':hashlib.sha256(payload).hexdigest(),'signature_verified':True,'original_codec_verified':True,'full_payload_byte_roundtrip':True,'request_byte_roundtrip':True,'shared_session_math_equal':True,'input':inp}
   details.append(row);previous_balance=balance
  except Exception as e:errors.append({'idx':r['seq'],'error':type(e).__name__+': '+str(e)})
 coverage={}
 for row in details:
  c=coverage.setdefault(row['mode'],{'spins':0,'bonus_spins':[],'debit_verified':0,'debit_mismatches':[]})
  c['spins']+=1
  if row['GetBonus']:c['bonus_spins'].append(row['round_id'])
  if row['debit_matches_ui']is True:c['debit_verified']+=1
  elif row['debit_matches_ui']is False:c['debit_mismatches'].append(row['round_id'])
 summary={'session':session.name,'game_id':664,'platform_id':1839,'currency':'IDR'if currency else 'UNCONFIRMED','responses':len(records),'signature_verified_responses':len(decoded),'successful_spins':len(details),'shared_math_files':len(list((HERE/'math').glob('[0-9]*.json'))),'full_payload_roundtrip_verified':len(details),'request_roundtrip_verified':len(details),'errors':errors,'conflicts':sum(1 for _ in (session/'math_conflicts.jsonl').open())if(session/'math_conflicts.jsonl').exists()else 0,'partial_raw_tail':False,'coverage':coverage,'non_success_responses_not_math':bad_replies,'historical_pending_math_errors_recovered':len((session/'math_errors.jsonl').read_text().splitlines())if(session/'math_errors.jsonl').exists()else 0,'limitations':['GetBonus and BonusSymbol keep original numeric meaning; no inferred free-round counter or enum.','Bonus internal stage semantics and retrigger/max-win flags are not claimed exhaustive.']}
 write(session/'validation.json',summary);write(session/'live_validation.json',{'verified_spins':len(details),'errors':errors,'spins':details});write(session/'coverage.json',coverage);write(HERE/'final_capture_summary.json',summary);write(HERE/'live_validation.json',{'verified_spins':len(details),'errors':errors,'spins':details});write(HERE/'coverage.json',coverage)
 # Sanitized decrypted records exclude all transport keys/tokens, retained privately for replay.
 (session/'exchanges_ordered_verified.jsonl').write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n'for d in decoded))
 print(json.dumps({k:v for k,v in summary.items()if k not in ['non_success_responses_not_math','coverage']},ensure_ascii=False));print(json.dumps(coverage,ensure_ascii=False))
 return summary
if __name__=='__main__':
 result=finish(Path((HERE/'current_session.txt').read_text().strip()))
 if not result['errors'] and result['conflicts']==0:
  from summarize_sessions import summarize
  summarize()
