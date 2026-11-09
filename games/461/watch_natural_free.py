"""Passive check of already-published session math. Does not place or stop wagers."""
import argparse,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));import math_adapter as a
sys.path.insert(0,str(HERE.parent.parent/'routex'));import decrypt_capture as dc,fg5

def check(session):
    candidates=[];paths=list((session/'math').glob('[0-9]*.json'))
    for path in paths:
        m=json.loads(path.read_text())
        free=m['data']['RoundQueue']
        if not any(x['FreeTotalRound']>0 or x['FreeRemainRound']>0 for x in free):continue
        if 23 in a.fields(bytes(m['spinReq'])):continue
        candidates.append((m,path))
    if not candidates:return {'successful_math':len(paths),'natural_free':False}
    key=bytes.fromhex(json.loads((session/'key.json').read_text())['key'])
    by_id={m['roundIndexV2']:(m,p)for m,p in candidates}
    for line in (session/'exchanges.jsonl').read_bytes().splitlines(keepends=True):
        if not line.endswith(b'\n'):continue
        rec=json.loads(line);d=dc.decrypt_response(bytes.fromhex(rec['resp_body_hex']),key)
        if d.get('_sig_ok') is not True or d['type']!=0 or d['ret']!=0:continue
        payload=bytes(d['raw']);rid=str(a.fields(payload).get(20,(0,0))[1])
        if rid not in by_id:continue
        req=fg5.parse_fields(bytes.fromhex(rec['req_body_hex'])).get(2,b'')
        if 23 in a.fields(req):continue
        m,path=by_id[rid];verified=a.wire_to_math(payload)
        if a.math_to_wire(verified)!=payload or a.math_to_wire(m)!=payload:raise ValueError('Math/wire roundtrip mismatch')
        rounds=m['data']['RoundQueue'];last=rounds[-1]
        report={'session':session.name,'round_id':rid,'seq':rec.get('seq'),'natural_free':True,
                'successful_math':len(paths),'purchase_parameter_absent_in_request':True,
                'signature_verified':True,'original_codec_verified':True,'complete_payload_byte_roundtrip':True,
                'free_total_win':m['data']['FreeTotalWin'],'total_win':m['data']['TotalWin'],
                'queue_length':len(rounds),'last_free_remaining':last['FreeRemainRound'],
                'last_free_now':last['FreeNowRound'],'last_free_total':last['FreeTotalRound'],
                'complete_free_ending':last['FreeRemainRound']==0,'math_file':str(path)}
        (HERE/'natural_free_detected.json').write_text(json.dumps(report,indent=2)+'\n')
        return report
    return {'successful_math':len(paths),'natural_free':False,'candidate_needs_request_check':True}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--seconds',type=int,default=45);args=ap.parse_args()
    session=Path((HERE/'current_session.txt').read_text().strip());deadline=time.monotonic()+args.seconds
    while True:
        result=check(session)
        if result['natural_free'] or time.monotonic()>=deadline:print(json.dumps(result));break
        time.sleep(3)
