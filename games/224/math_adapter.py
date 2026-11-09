"""Original-codec adapter. Wire context remains session-private; public math contains no wire bytes."""
import json,subprocess
from copy import deepcopy
from pathlib import Path
HERE=Path(__file__).resolve().parent

def bridge(value):
    p=subprocess.run(['node',str(HERE/'math_adapter.cjs')],input=json.dumps(value),text=True,capture_output=True)
    v=json.loads(p.stdout)
    if p.returncode or not v.get('ok'):raise ValueError(v.get('error',p.stderr))
    return v['result']

def wire_to_math(records):return bridge({'records':records})
def math_to_wire(frame):return bytes.fromhex(bridge({'op':'encode','value':frame}))

def round_to_math(source,currency='IDR'):
    req,ack=source['request'],source['ack']
    if req['message']!='BetReq' or ack['message']!='BetResp' or ack['data'].get('betFailed',False):raise ValueError('No own accepted bet')
    if sum(b.get('bet',0) for b in req['data'].get('betData',[]))<=0:raise ValueError('No positive own bet')
    if req['data'].get('useFree',False) or ack['data'].get('useFree',False):raise ValueError('Free-bet semantics not yet validated; raw retained')
    rid=ack['data'].get('roundIndex')
    if not isinstance(rid,str) or not rid.isdigit() or int(rid)<=0:raise ValueError('Missing exact original roundIndex')
    end=source['end']
    if end['message']!='FlyEnd':raise ValueError('Missing settlement')
    frames=[req,ack,*source['cashout_requests'],*source['cashouts'],end]
    for f in frames:
        if math_to_wire(f).hex()!=f['_wire']:raise ValueError('Full application frame byte round-trip failed')
    # CashOut replies are own-wallet replies per original AviatorNetwork.onCommand.
    total=sum(f['data'].get('win',0) for f in source['cashouts'])
    if abs(total-end['data'].get('totalWin',0))>1e-7:raise ValueError('CashOut / FlyEnd totalWin mismatch')
    if len({f['data'].get('betType',0) for f in source['cashouts']})!=len(source['cashouts']):raise ValueError('Repeated cashout area requires review')
    return {'round_id':rid,'currency':currency,'spinReq':deepcopy(req['data']),'data':{'betResponse':deepcopy(ack['data']),'cashOutReqs':[deepcopy(f['data']) for f in source['cashout_requests']],'cashOuts':[deepcopy(f['data']) for f in source['cashouts']],'flyEnd':deepcopy(end['data'])}}

def math_to_round_wire(value,source):
    s=deepcopy(source)
    if value['round_id']!=value['data']['betResponse']['roundIndex']:raise ValueError('Round index mismatch')
    if len(value['data']['cashOuts'])!=len(s['cashouts']) or len(value['data']['cashOutReqs'])!=len(s['cashout_requests']):raise ValueError('Structural edit needs new wire context')
    s['request']['data']=value['spinReq'];s['ack']['data']=value['data']['betResponse'];s['end']['data']=value['data']['flyEnd']
    for f,d in zip(s['cashouts'],value['data']['cashOuts']):f['data']=d
    for f,d in zip(s['cashout_requests'],value['data']['cashOutReqs']):f['data']=d
    return [math_to_wire(f) for f in [s['request'],s['ack'],*s['cashout_requests'],*s['cashouts'],s['end']]]
