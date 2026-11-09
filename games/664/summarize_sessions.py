#!/usr/bin/env python3
"""Combine verified session reports without merging login keys or replacing math."""
import json
from pathlib import Path
import math_adapter as a
HERE=Path(__file__).resolve().parent

def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def summarize():
 current=Path((HERE/'current_session.txt').read_text().strip())
 latest=json.loads((HERE/'final_capture_summary.json').read_text())
 if latest.get('session')==current.name:
  for name in ['final_capture_summary.json','live_validation.json','coverage.json']:
   write(current/name,json.loads((HERE/name).read_text()))
 sessions=[];rows=[];coverage={};by_id={};errors=[];conflicts=0;responses=0;verified_responses=0
 for path in sorted((HERE/'webcap').glob('*/validation.json')):
  session=path.parent;summary=json.loads(path.read_text());detail=session/'live_validation.json'
  if not detail.exists():continue
  data=json.loads(detail.read_text());samples=data['spins']
  if summary['errors']or summary['partial_raw_tail']or summary['conflicts']or data['errors']:raise ValueError('Session validation failed: '+session.name)
  if len(samples)!=summary['successful_spins']:raise ValueError('Session sample count mismatch: '+session.name)
  sessions.append({'session':session.name,'currency':summary['currency'],'responses':summary['responses'],'successful_spins':len(samples),'full_payload_roundtrip_verified':summary['full_payload_roundtrip_verified'],'request_roundtrip_verified':summary['request_roundtrip_verified'],'errors':[],'conflicts':0})
  responses+=summary['responses'];verified_responses+=summary['signature_verified_responses']
  for row in samples:
   rid=row['round_id'];shared=json.loads((HERE/'math'/(rid+'.json')).read_text());snapshot=json.loads((session/'math'/(rid+'.json')).read_text())
   if shared!=snapshot:raise ValueError('Shared math changed, preserved: '+rid)
   payload=a.math_to_wire(shared)
   import hashlib
   if hashlib.sha256(payload).hexdigest()!=row['payload_sha256']:raise ValueError('Shared payload mismatch: '+rid)
   if rid in by_id:
    if by_id[rid]['payload_sha256']!=row['payload_sha256']:raise ValueError('Conflicting round across sessions: '+rid)
    continue
   row=dict(row,session=session.name);by_id[rid]=row;rows.append(row)
   c=coverage.setdefault(row['mode'],{'spins':0,'bonus_spins':[],'debit_verified':0,'debit_mismatches':[]});c['spins']+=1
   if row['GetBonus']==2:c['bonus_spins'].append(rid)
   if row['debit_matches_ui']is True:c['debit_verified']+=1
   elif row['debit_matches_ui']is False:c['debit_mismatches'].append(rid)
 mathfiles={p.stem for p in(HERE/'math').glob('[0-9]*.json')}
 if mathfiles!=set(by_id):raise ValueError('Unaccounted shared math round IDs')
 summary={'game_id':664,'platform_id':1839,'state':'closed','currencies':sorted({x['currency']for x in sessions}),'sessions':sessions,'responses':responses,'signature_verified_responses':verified_responses,'successful_spins':len(rows),'shared_math_files':len(mathfiles),'full_payload_roundtrip_verified':sum(x['full_payload_roundtrip_verified']for x in sessions),'request_roundtrip_verified':sum(x['request_roundtrip_verified']for x in sessions),'errors':errors,'conflicts':conflicts,'partial_raw_tail':False,'coverage':coverage,'limitations':['Bonus internal stage semantics, retriggers and rare flags are not claimed exhaustive.','Sessions and cryptographic keys remain separate; counts are combined after independent validation.']}
 write(HERE/'final_capture_summary.json',summary);write(HERE/'coverage.json',coverage);write(HERE/'live_validation.json',{'verified_spins':len(rows),'errors':[],'spins':rows})
 print(json.dumps(summary,ensure_ascii=False));return summary
if __name__=='__main__':summarize()
