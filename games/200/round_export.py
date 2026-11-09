"""Correlate original Pappu room events and publish editable math without credentials."""
from collections import Counter
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('pappu_200_public_codec',HERE/'math_adapter.py')
codec=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(codec)


def atomic_json(path,value):
    """Publish a complete file with exclusive link; a concurrent editor cannot be overwritten."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    name=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,delete=False,prefix='.'+path.name+'.') as f:
            name=Path(f.name);json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        try:os.link(name,path);return 'created'
        except FileExistsError:
            if json.loads(path.read_text())==value:return 'unchanged'
            raise FileExistsError('Edited/existing JSON preserved: '+str(path))
    finally:
        if name is not None:name.unlink(missing_ok=True)


class Collector:
    def __init__(self,game_dir,session,currency):
        self.game_dir,self.session=Path(game_dir),Path(session)
        self.currency=currency
        self.states={};self.stats=Counter();self.rounds=[]

    def log(self,name,obj):
        self.session.mkdir(parents=True,exist_ok=True)
        with (self.session/name).open('a') as f:f.write(json.dumps(obj,ensure_ascii=False)+'\n')

    def feed(self,rec):
        # The injected hook sees other framework sockets too. Never treat them as game rounds.
        if not urlsplit(rec.get('url','')).path.startswith('/pappu/ws/'):
            self.stats['other_socket_frames']+=1;return None
        try:return self._feed(rec)
        except Exception as error:
            self.stats['validation_errors']+=1
            self.log('math_errors.jsonl',{'seq':rec.get('seq'),'error':type(error).__name__+': '+str(error)})
            return '[200 math] ERROR '+str(error)+'; raw retained'

    def _feed(self,rec):
        if rec['dir']=='SEND' and self.states.get(rec['url'],{}).get('uid') is None:
            self.stats['framework_login_requests']+=1;return None
        raw=bytes.fromhex(rec['hex'])
        command=codec.decode_message(raw,'Command')['type']
        mapping=codec.RECV_TYPES if rec['dir']=='RECV' else codec.SEND_TYPES
        if command not in mapping:
            self.stats['unclassified_game_frames']+=1
            self.log('unclassified_frames.jsonl',{'seq':rec.get('seq'),'dir':rec['dir'],'command':command})
            return None
        # SEND login has its own framework payload, outside the math boundary.
        if rec['dir']=='SEND' and command==0:
            self.stats['framework_login_requests']+=1;return None
        decoded=codec.wire_to_math(raw,rec['dir'])
        if codec.math_to_wire(decoded)!=raw:raise ValueError('Complete game Command failed byte round-trip')
        decoded['capture_seq']=rec.get('seq')
        self.log('verified_decoded.jsonl',decoded)
        self.stats['verified_game_frames']+=1
        s=self.states.setdefault(rec['url'],{'uid':None,'currency':None,'room':None,'round':None,
            'pending':{},'accepted':[],'prior_balance':None,'context':None,'complete':False,'settled':False,'invalid':False})
        dr,c,d=rec['dir'],decoded['command'],decoded['data']
        if dr=='SEND':
            if c==22:
                if s['settled']:raise ValueError('Wager after room settlement')
                k=str(d['clientCheckNum'])
                if k in s['pending']:raise ValueError('Ambiguous duplicate pending clientCheckNum')
                s['pending'][k]=decoded
            return None
        if c==0:
            if d['result']!=0 or not d['player']['uid']:raise ValueError('Unsuccessful game login')
            s['uid']=str(d['player']['uid']);s['currency']=d['player']['wallet']['currency']
            s['prior_balance']=codec.money(d['player']['wallet']['coin'])
        elif c in (11,24):
            if s['room']!=d['roomId'] or s['round']!=d['wagers']:
                s.update(room=d['roomId'],round=d['wagers'],pending={},accepted=[],context=decoded,complete=True,settled=False,invalid=False)
            # The first JoinRoomAck can omit coin (=0); do not treat omission as an actual reset.
            if 9 in codec.fields(codec.byte_array(d['_wire'])):s['prior_balance']=codec.money(d['coin'])
        elif c==17:
            s.update(round=d['wagers'],pending={},accepted=[],context=decoded,complete=True,settled=False,invalid=False)
        elif c==22:
            if str(d['accountID'])!=s['uid']:
                self.stats['other_player_acks']+=1;return None
            k=str(d['clientCheckNum']);request=s['pending'].pop(k,None)
            if request is None:
                s['invalid']=True;raise ValueError('Own ack has no unique pending request')
            if codec.clean(request['data']['detail'])!=codec.clean(d['detail']):
                s['invalid']=True;raise ValueError('Own acknowledgment differs from request')
            s['accepted'].append({'request':request,'ack':decoded})
        elif c==18:
            balance=codec.money(d['postCoin'])
            if s['settled']:raise ValueError('Repeated RoomEnd without a new round')
            s['settled']=True
            if not s['accepted']:
                self.stats['spectator_results']+=1;s['prior_balance']=balance;return None
            if s['invalid'] or not s['complete'] or s['pending'] or not s['uid'] or s['currency'] is None or not s['room'] or not s['round']:
                raise ValueError('Incomplete/ambiguous own-wager round')
            source={'roundId':s['round'],'roomId':s['room'],'currency':s['currency'],
                    'spinReq':s['accepted'],'data':decoded,'round_context':s['context']}
            obj=codec.round_to_math(source,currency=self.currency)
            expected=s['prior_balance']-obj['bet_total']+obj['total_win'] if s['prior_balance'] is not None else None
            s['prior_balance']=balance
            if expected is None or expected!=balance:raise ValueError('Wallet movement does not match accepted bets and payout')
            if codec.math_round_to_wire(obj,source)!=raw:raise ValueError('Public math does not restore complete original RoomEnd Command')
            rid=obj['round_id']
            # Local originals are preserved first, including complete unknown representation.
            atomic_json(self.session/'math_wire'/(rid+'.json'),source)
            atomic_json(self.session/'math_export'/(rid+'.json'),obj)
            self.stats['validated_own_rounds']+=1;self.rounds.append(obj)
            try:status=atomic_json(self.game_dir/'math'/(rid+'.json'),obj)
            except FileExistsError as error:
                self.stats['publish_conflicts']+=1;self.log('math_conflicts.jsonl',{'round_id':rid,'error':str(error)})
                return '[200 math] CONFLICT round='+rid+'; edited file and local original preserved'
            self.stats['published_rounds']+=1
            return '[200 math] '+status+' round='+rid
        return None
