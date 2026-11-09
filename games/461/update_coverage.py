"""Revalidate current session and report observed request fields without guessing modes."""
import json,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'routex'))
import decrypt_capture as dc,fg5
sys.path.insert(0,str(HERE))
import math_adapter as a
from finish_capture import scan

def detail(buf):
    result={}
    for n,w,v in a.wire_fields(buf):
        if w==1:result['f'+str(n)]=struct.unpack('<d',v)[0]
        elif w==0:result['f'+str(n)]=str(v) if v>2**53 else v
        elif w==2:result['f'+str(n)]={'hex':v.hex()}
    return result

def main():
    session=Path((HERE/'current_session.txt').read_text().strip())
    stats=scan(session);(session/'validation.json').write_text(json.dumps(stats,indent=2)+'\n')
    key=bytes.fromhex(json.loads((session/'key.json').read_text())['key'])
    samples=[]
    for line in (session/'exchanges.jsonl').read_bytes().splitlines(keepends=True):
        if not line.endswith(b'\n'):continue
        r=json.loads(line);d=dc.decrypt_response(bytes.fromhex(r['resp_body_hex']),key)
        if d['_sig_ok'] is not True or d['type']!=0 or d['ret']!=0:continue
        payload=bytes(d['raw']);m=a.wire_to_math(payload)
        if a.math_to_wire(m)!=payload:raise ValueError('Roundtrip mismatch')
        request=fg5.parse_fields(bytes.fromhex(r['req_body_hex'])).get(2,b'')
        req=detail(request)
        for name,part in list(req.items()):
            if isinstance(part,dict):
                try:part['fields']=detail(bytes.fromhex(part['hex']))
                except ValueError:pass
        samples.append({'round_id':m['roundIndexV2'],'seq':r.get('seq'),'request':req,
                        'total_win':m['data']['TotalWin'],'post_money_f6':m['f6'],
                        'free_total_win':m['data']['FreeTotalWin'],
                        'free_rounds':[{'remaining':x['FreeRemainRound'],'now':x['FreeNowRound'],'total':x['FreeTotalRound']} for x in m['data']['RoundQueue']],
                        'full_payload_byte_roundtrip':True,'original_codec_check':True})
    report={'session':session.name,'currency':'IDR','verified_success_spins':len(samples),'validation':stats,'samples':samples,
            'mode_interpretation':'Request f25/context fields are neutral until paired mode evidence is established.'}
    (HERE/'live_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    normal=[];purchases=[];other=[];natural=[]
    ordered=sorted(samples,key=lambda x:x['seq'])
    for i,sample in enumerate(ordered):
        req=sample['request'];context=req.get('f25',{}).get('fields',{})
        has_free=any(x['remaining'] or x['total'] for x in sample['free_rounds'])
        if 'f23' in req:
            purchase=dict(sample)
            purchase['base_bet']=req.get('f1')
            purchase['purchase_fields']=req['f23'].get('fields',{})
            if i:
                purchase['paid_cost']=ordered[i-1]['post_money_f6']+sample['total_win']-sample['post_money_f6']
                purchase['paid_over_base_bet']=purchase['paid_cost']/req['f1']
            purchase['complete_free_ending']=has_free and sample['free_rounds'][-1]['remaining']==0
            purchases.append(purchase)
        elif context=={'f1':0,'f2':0,'f4':0}:normal.append(sample)
        else:other.append(sample)
        if has_free and 'f23' not in req:natural.append(sample['round_id'])
    coverage={'active_session':session.name,'currency_observed':'IDR','initialization_signature_verified':True,
              'successful_live_spins':len(samples),'validation_errors':stats['errors'],
              'modes':{
                  'normal':{'status':'observed','samples':len(normal)},
                  'extra_bet':{'status':'awaiting paired user mode evidence','candidate_samples':len(other),
                               'initial_game_info':{'ShowExtra':True,'Mul':[1,1.5]}},
                  'natural_bonus_free':{'status':'observed' if natural else 'not yet observed','round_ids':natural},
                  'purchase':{'status':'observed' if purchases else 'pending','samples':len(purchases),'results':purchases}},
              'scope_limits':['Purchase-triggered free games do not prove natural trigger coverage.',
                              'Current UI has no extra-bet control per user; shared ShowExtra flag is not mode-availability proof.',
                              'Current math spinReq preserves response echo bytes; original input/context is retained in live_validation.json.']}
    availability=HERE/'mode_availability.json'
    if availability.exists():
        coverage['modes']['extra_bet'].update(json.loads(availability.read_text())['extra_bet'])
    (HERE/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
    print(json.dumps({'successful_spins':len(samples),'errors':stats['errors'],'round_ids':[s['round_id'] for s in samples]}))
if __name__=='__main__':main()
