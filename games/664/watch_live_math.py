#!/usr/bin/env python3
"""Passive live export for the collector started before the 664 codec was ready."""
import json,os,time,sys,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from math_adapter import wire_to_math,math_to_wire
from live_math_664 import export_spin,_write_json
SESSION=Path((HERE/'current_session.txt').read_text().strip())

def run():
    (SESSION/'math_watcher.pid').write_text(str(os.getpid())+'\n')
    cursor=0;verified={};errors=[];counts={}
    while True:
        path=SESSION/'exchanges_ordered.jsonl'
        if path.exists():
            with path.open('rb') as stream:
                stream.seek(cursor)
                while True:
                    start=stream.tell();line=stream.readline()
                    if not line or not line.endswith(b'\n'):cursor=start;break
                    cursor=stream.tell();d=json.loads(line)
                    if d.get('type')!=0 or d.get('ret')!=0 or d.get('_sig_ok') is not True:continue
                    checked={}
                    def decode(b):
                        m=wire_to_math(b);checked['math']=m;return m
                    report=export_spin(d,HERE,SESSION,decode,math_to_wire)
                    if report and report.get('ok'):
                        m=checked['math'];data=m['data'];rid=m['roundIndexV2'];verified[rid]={'idx':d['idx'],'round_id':rid,'payload_bytes':len(d['raw']),'sha256':hashlib.sha256(bytes(d['raw'])).hexdigest(),'extra':data['Extra'],'getBonus':data['GetBonus'],'plate_count':len(data['PlateSymbol']),'signature_verified':True,'original_codec_verified':True,'full_payload_byte_roundtrip':True}
                        print('math OK',rid,'extra',data['Extra'],'bonus',data['GetBonus'],flush=True)
                    elif report:errors.append(report);print('math ERROR',report['error'],flush=True)
            counts={}
            for v in verified.values():
                k=str(v['extra']);counts[k]=counts.get(k,0)+1
            status={'session':SESSION.name,'pid':os.getpid(),'verified_spins':len(verified),'published_math':len(list((SESSION/'math').glob('[0-9]*.json'))),'errors':errors,'extra_wire_values':counts,'bonus_candidates':[v for v in verified.values() if v['getBonus']],'spins':list(verified.values()),'note':'Old collector math_errors marked codec pending are historical; watcher revalidates every recovered SPIN.'}
            tmp=SESSION/'watcher_status.tmp';tmp.write_text(json.dumps(status,indent=2)+'\n');tmp.replace(SESSION/'watcher_status.json')
        time.sleep(1)
if __name__=='__main__':run()
