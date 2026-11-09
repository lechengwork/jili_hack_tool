#!/usr/bin/env python3
"""Audit captured rank frames and the user's revealed fairness screenshot.

Raw identifiers and revealed seed text remain in the ignored session. The public
report distinguishes confirmed checks from a numerical formula inferred from one sample.
"""
import hashlib,hmac,json,math,shutil,sys
from pathlib import Path
from collections import Counter
from urllib.parse import urlsplit
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from math_adapter import wire_to_math,math_to_wire
from watch_live_math import command

def varint(b,p):
    value=0
    for shift in range(0,70,7):
        x=b[p];p+=1;value|=(x&127)<<shift
        if x<128:return value,p
    raise ValueError('Oversized initialization varint')

def raw_fields(b):
    out={};p=0
    while p<len(b):
        tag,p=varint(b,p);n,w=tag>>3,tag&7
        if w==0:value,p=varint(b,p)
        elif w==2:
            size,p=varint(b,p);value=b[p:p+size];p+=size
        elif w in (1,5):
            size=8 if w==1 else 4;value=b[p:p+size];p+=size
        else:raise ValueError('Unsupported initialization field')
        if p>len(b):raise ValueError('Truncated initialization field')
        out[n]=value
    return out

def load_math(session):
    return [json.loads(p.read_text()) for p in sorted((session/'math').glob('*.json'))]

def verify():
    session=HERE/'webcap/20261109-100032'
    rows=[json.loads(l) for l in (session/'frames.jsonl').read_text().splitlines()]
    welcome=next(r for r in rows if r['dir']=='RECV' and command(r['hex'])==0)
    login=raw_fields(raw_fields(bytes.fromhex(welcome['hex']))[2]);user=raw_fields(login[3]);uid=str(user[1]);wallet=raw_fields(user[4])
    assert wallet[7].decode()=='IDR'
    rank_raw=[r for r in rows if r['dir']=='RECV' and command(r['hex'])==14]
    ranks=wire_to_math(rank_raw)
    saved=[json.loads(l) for l in (session/'rank_verified.jsonl').read_text().splitlines()]
    assert ranks==saved,'Stored rank decode differs from a fresh original-codec decode'
    for raw,decoded in zip(rank_raw,ranks):assert math_to_wire(decoded).hex()==raw['hex']
    prior=HERE/'webcap/20261106-162808'
    old_math=load_math(prior);new_math=load_math(session)
    def matching_rounds(row,values):
        return [v['round_id'] for v in values if math.isclose(sum(b.get('bet',0) for b in v['spinReq']['betData']),row.get('bet',0),abs_tol=1e-9) and math.isclose(v['data']['flyEnd'].get('totalWin',0),row.get('win',0),abs_tol=1e-9)]
    snapshots=[];own_rows=0;foreign_rows=0
    for raw,rank in zip(rank_raw,ranks):
        snap={'seq':raw['seq'],'sections':{}}
        for period,block in rank['data'].items():
            for category,items in block.items():
                own=sum(str(x.get('accountIDV2',x.get('accountID',0)))==uid for x in items)
                own_rows+=own;foreign_rows+=len(items)-own
                assert all(math.isclose(x.get('rate',0),x.get('win',0)/x['bet'],abs_tol=1e-12) for x in items),'Rank rate differs from gross win / total bet'
                old_matches=[matching_rounds(x,old_math) for x in items];new_matches=[matching_rounds(x,new_math) for x in items]
                metric='rate' if category=='BetRank' else 'win'
                descending=all(a.get(metric,0)>=b.get(metric,0) for a,b in zip(items,items[1:]))
                snap['sections'][period+'.'+category]={'rows':len(items),'own_account_rows':own,'sort_metric_observed':metric,'descending':descending,'matched_previous_capture_rows':sum(bool(x) for x in old_matches),'matched_current_capture_rows':sum(bool(x) for x in new_matches)}
        snapshots.append(snap)
    assert ranks[0]['data'].get('Daily',{})=={}
    last=ranks[-1]['data'];daily=last['Daily']['BetRank'][0]
    assert daily['bet']==200000 and daily['win']==328000 and daily['rate']==1.64
    assert matching_rounds(daily,new_math)==['645352646659592416']
    assert all(matching_rounds(x,old_math) for x in last['Monthly']['BetRank'])
    assert len({matching_rounds(x,old_math)[0] for x in last['Monthly']['BetRank']})==11

    revealed='0f85595a6819c162ac5d9cf28f32537ab1165e42fe2943dc'
    observed_prefix='19b6efa7';observed_integer=431419303
    assert int(observed_prefix,16)==observed_integer
    app=[r for r in rows if r['dir']=='RECV' and command(r['hex']) in (10,13,16) or r['dir']=='SEND' and command(r['hex'])==10]
    decoded=wire_to_math(app);info=None;matched=None;ack=None;end=None
    for r in decoded:
        if r['message']=='Info':info=r
        elif r['message']=='BetReq' and info and hashlib.sha256(revealed.encode()).hexdigest()==info['data']['serverHash']:
            assert info['ts']<r['ts'] and info['seq']<r['seq'];matched={'request':r,'commitment':info}
        elif matched and ack is None and r['message']=='BetResp' and r['seq']>matched['request']['seq']:ack=r
        elif ack and r['message']=='FlyEnd':end=r;break
    assert matched and ack and end
    assert ack['data']['roundIndex']=='645352646659592416'
    source=json.loads((session/'math/645352646659592416.json').read_text())
    assert any(c.get('betType',0)==1 and c['myRate']==1.6 and c['win']==160000 for c in source['data']['cashOuts'])
    predicted=.97*(2**32-1)/(observed_integer+1);actual=end['data']['endRate']
    assert math.isclose(predicted,actual,rel_tol=0,abs_tol=1e-12)
    client=matched['request']['data']['seed'];hash_matches=[]
    for algorithm in ['sha256','sha512']:
        for separator in ['',':','-',',','|',' ']:
            for first in [False,True]:
                a,b=(client,revealed) if first else (revealed,client)
                digest=hashlib.new(algorithm,(a+separator+b).encode()).hexdigest()
                if digest.startswith(observed_prefix):hash_matches.append({'algorithm':algorithm,'separator':separator,'client_first':first})
        for key,msg in [(revealed,client),(client,revealed)]:
            if hmac.new(key.encode(),msg.encode(),algorithm).hexdigest().startswith(observed_prefix):hash_matches.append({'algorithm':'hmac-'+algorithm})
    http=[json.loads(l) for l in (session/'http_exchanges.jsonl').read_text().splitlines()]
    routes=Counter((urlsplit(r.get('url','')).hostname,urlsplit(r.get('url','')).path,r.get('status')) for r in http)
    assert not any('fair' in path.lower() or 'get-detail-info' in path.lower() for _,path,_ in routes)
    auxiliary=[]
    for r in http:
        if 'GetRankingListV2' in r.get('url',''):
            data=json.loads(bytes.fromhex(r['response']['hex']));auxiliary.append({'status':r.get('status'),'Data_is_null':data.get('Data') is None,'error':data.get('Error')})
    fairness={'round_id':ack['data']['roundIndex'],'revealed_seed_source':'User screenshot; copied into ignored session evidence/','server_seed_sha256_matches_prebet_commitment':True,'commitment_received_before_bet':True,'commitment_seq':matched['commitment']['seq'],'bet_seq':matched['request']['seq'],'screenshot_bet2_cashout_matches_capture':True,'screenshot_hex_to_decimal_verified':True,'screenshot_hex':observed_prefix,'screenshot_integer':observed_integer,'observed_end_rate':actual,'one_sample_formula_inference':{'formula':'0.97 * (2^32 - 1) / (N + 1)','computed':predicted,'absolute_error':abs(predicted-actual),'status':'Single-sample numerical match; formula, range clamps, rounding and RTP NOT established as the general original algorithm'},'simple_one_client_hash_candidates_matching_prefix':hash_matches,'complete_seed_to_combined_hash_to_multiplier_verification':False,'missing':['Raw full fairness/history response with every participating client seed in order','Full combined hash and original combination/hash algorithm or complete calculation page','At least another disclosed round, including a low/crash-near-1x case, to cross-check the algorithm','Cross-account simultaneous evidence remains required for shared-outcome multiplayer claims']}
    report={'session':session.name,'closed':(session/'capture_closed.json').exists(),'currency':'IDR','rank':{'verified_responses':len(ranks),'original_codec_full_frame_byte_roundtrip':True,'all_observed_rows_are_current_account':foreign_rows==0,'row_occurrences':own_rows+foreign_rows,'foreign_account_rows':foreign_rows,'snapshots':snapshots,'daily_new_round_matches_own_settlement':{'bet':200000,'gross_return':328000,'rank_rate':1.64,'cashout_rates':[1.6,1.68]},'monthly_11_rows_match_11_prior_winning_rounds':True,'monthly_not_updated_with_current_win_in_observed_snapshots':True,'auxiliary_promotional_ranking':auxiliary,'limits':['Cannot determine global / agent / personal leaderboard scope from one account','Monthly refresh / retention policy is unconfirmed','Cannot infer humans or shared rounds from these rank rows']},'fairness':fairness,'current_successful_math':len(new_math),'previous_successful_math':len(old_math),'combined_successful_math':len(old_math)+len(new_math),'next_capture_priority':['Targeted fairness/history page network capture, including child iframe/new-window traffic; no extra wagering needed merely to inspect an existing round','Second authorized account with simultaneous comparison to establish whether outcomes are shared','If leaderboard scope matters, second-account comparison and a later monthly refresh snapshot']}
    evidence=session/'evidence';evidence.mkdir(exist_ok=True)
    for name in ['codex-clipboard-60abb6f0-d49c-41fd-879a-aa7bbc1423ac.png','codex-clipboard-2a5dbba1-b6c8-48f2-9d2e-fda04008c990.png']:
        p=Path('/var/folders/z5/r666s9jd7xqgvttw5vvfdf380000gn/T')/name
        if p.exists():shutil.copy2(p,evidence/name)
    (evidence/'fairness_transcription.local.json').write_text(json.dumps({'revealed_server_seed':revealed,'client_seed_from_wire':client,'screenshot_hex':observed_prefix,'source_round':ack['data']['roundIndex']},indent=2)+'\n')
    for path in [session/'rank_fairness_validation.json',HERE/'analysis/rank_fairness_validation.json']:
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'rank_responses_verified':len(ranks),'rank_foreign_account_rows':foreign_rows,'daily_round_matches':True,'monthly_previous_wins_matched':11,'server_seed_commitment_verified':True,'formula_single_sample_absolute_error':abs(predicted-actual),'full_fairness_chain_verified':False,'simple_hash_candidates_matching':len(hash_matches),'combined_math':len(old_math)+len(new_math)},ensure_ascii=False))
if __name__=='__main__':verify()
