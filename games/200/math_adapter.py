"""Pappu schema adapter. Generic lossless protobuf routines reused; no 545 schema loaded."""
from collections import defaultdict
import json, math, struct
from pathlib import Path
from copy import deepcopy
HERE=Path(__file__).resolve().parent
SCHEMA=json.loads((HERE/'math_schema.json').read_text())

def varint(value):
    if type(value) is not int or not -(1<<63) <= value < (1<<64):
        raise ValueError('Invalid integer')
    value &= (1<<64)-1
    out=bytearray()
    while value > 127:
        out.append((value&127)|128);value >>= 7
    return bytes(out)+bytes([value])


def read_varint(buf,pos):
    value=0
    for shift in range(0,70,7):
        if pos >= len(buf):raise ValueError('Truncated varint')
        b=buf[pos];pos+=1
        if shift==63 and b>1:raise ValueError('Varint overflow')
        value|=(b&127)<<shift
        if b<128:return value,pos
    raise ValueError('Oversized varint')


def records(buf):
    pos=0
    while pos<len(buf):
        start=pos;tag,pos=read_varint(buf,pos);n,w=tag>>3,tag&7
        if not 0<n<(1<<29):raise ValueError('Invalid field number')
        if w==0:v,pos=read_varint(buf,pos)
        elif w in (1,5):
            end=pos+(8 if w==1 else 4);v=buf[pos:end];pos=end
        elif w==2:
            size,pos=read_varint(buf,pos);end=pos+size;v=buf[pos:end];pos=end
        else:raise ValueError('Unsupported wire type %s; original capture retained' % w)
        if pos>len(buf):raise ValueError('Truncated field')
        yield n,w,v,buf[start:pos]


def wire_fields(buf):
    for n,w,v,_ in records(buf):yield n,w,v


def fields(buf):
    out={}
    for n,w,v in wire_fields(buf):
        if n in out:raise ValueError('Duplicate field %s' % n)
        out[n]=(w,v)
    return out


def field(n,w,v):
    return varint(n*8+w)+(varint(len(v))+v if w==2 else v)


def default(f):
    if f['repeated']:return []
    t=f['type']
    return {} if t in SCHEMA else [] if t=='opaque' else '' if t=='string' else '0' if t=='uint64' else False if t=='bool' else 0


def decode_scalar(v,w,t):
    expected=2 if t in SCHEMA or t in ('string','opaque') else 1 if t=='double' else 0
    if w!=expected:raise ValueError('Unexpected wire type for '+t)
    if t in SCHEMA:return decode_message(v,t)
    if t=='opaque':return list(v)
    if t=='string':return v.decode('utf-8')
    if t=='double':
        value=struct.unpack('<d',v)[0]
        if not math.isfinite(value):raise ValueError('Non-finite double')
        return value
    if t=='uint64':return str(v)
    if t=='uint32':return v
    if t=='bool':return bool(v)
    return (v&0xffffffff)-(1<<32) if v&(1<<31) else v&0xffffffff


def decode_message(buf,name='Command',sidecar=True):
    table={f['number']:f for f in SCHEMA[name]}
    out={f['name']:default(f) for f in table.values()};seen=set()
    for n,w,v,_ in records(buf):
        if n not in table:continue
        f=table[n];t=f['type'];k=f['name']
        if n in seen and not f['repeated']:raise ValueError('Duplicate scalar '+name+'.'+k)
        seen.add(n)
        if f['repeated'] and t in ('double','int32','uint32','uint64','bool') and w==2:
            pos=0
            while pos<len(v):
                if t=='double':val=v[pos:pos+8];pos+=8;wt=1
                else:val,pos=read_varint(v,pos);wt=0
                out[k].append(decode_scalar(val,wt,t))
        else:
            val=decode_scalar(v,w,t)
            if f['repeated']:out[k].append(val)
            else:out[k]=val
    if sidecar:out['_wire']=list(buf)
    return out


def clean(obj):
    if isinstance(obj,dict):return {k:clean(v) for k,v in obj.items() if k!='_wire'}
    if isinstance(obj,list):return [clean(v) for v in obj]
    return obj


def scalar(v,t):
    if t in SCHEMA:return 2,encode_message(v,t)
    if t=='string':
        if not isinstance(v,str):raise ValueError('Expected string')
        return 2,v.encode('utf-8')
    if t=='opaque':return 2,byte_array(v)
    if t=='double':
        if type(v) not in (int,float) or not math.isfinite(v):raise ValueError('Expected finite number')
        return 1,struct.pack('<d',v)
    if t=='uint64':
        if not isinstance(v,str) or not v.isdigit() or int(v)>=1<<64:raise ValueError('Expected uint64 string')
        return 0,varint(int(v))
    if t=='bool':
        if type(v) is not bool:raise ValueError('Expected boolean')
        return 0,varint(int(v))
    if t=='uint32':
        if type(v) is not int or not 0<=v<(1<<32):raise ValueError('Expected uint32')
        return 0,varint(v)
    if type(v) is not int or not -(1<<31)<=v<(1<<31):raise ValueError('Expected int32')
    return 0,varint(v)


def byte_array(v):
    if not isinstance(v,list) or any(type(x) is not int or not 0<=x<=255 for x in v):
        raise ValueError('Expected integer array in range 0..255')
    return bytes(v)


def encode_message(obj,name='Command'):
    if not isinstance(obj,dict):raise ValueError('Expected message '+name)
    schema=SCHEMA[name];table={f['number']:f for f in schema}
    if set(obj)-{f['name'] for f in schema}-{'_wire'}:raise ValueError('Unknown named field in '+name)
    original=byte_array(obj.get('_wire',[]))
    baseline=decode_message(original,name) if original else {}
    encoded={};unchanged=set()
    for f in schema:
        n,k,t=f['number'],f['name'],f['type']
        if k not in obj:continue
        v=obj[k]
        if k in baseline and clean(v)==clean(baseline[k]):unchanged.add(n)
        if f['repeated']:
            if not isinstance(v,list):raise ValueError('Expected repeated '+k)
            vals=[scalar(x,t) for x in v]
            if t in ('int32','uint32','uint64','bool','double'):
                encoded[n]=field(n,2,b''.join(x[1] for x in vals)) if vals else b''
            else:encoded[n]=b''.join(field(n,w,value) for w,value in vals)
        elif clean(v)!=default(f):
            w,value=scalar(v,t);encoded[n]=field(n,w,value)
    result=bytearray();emitted=set()
    for n,w,v,raw in records(original):
        if n not in table or n in unchanged:result.extend(raw)
        elif n not in emitted:result.extend(encoded.get(n,b''))
        emitted.add(n)
    for n in sorted(encoded):
        if n not in emitted and n not in unchanged:result.extend(encoded[n])
    return bytes(result)



RECV_TYPES={0:'LoginDataAck',1:'LogoutAck',10:'JoinThemeAck',11:'JoinRoomAck',13:'RoomHistory',17:'RoomStart',18:'RoomEnd',22:'SpinReq',24:'JoinRoomAck'}
SEND_TYPES={0:'LoginDataReq',10:'JoinThemeReq',11:'JoinRoomReq',13:'RoomAliveReq',22:'SpinReq'}

def wire_to_math(buf,direction):
    frame=decode_message(bytes(buf),'Command')
    types=RECV_TYPES if direction=='RECV' else SEND_TYPES if direction=='SEND' else None
    if types is None:raise ValueError('Invalid direction')
    name=types.get(frame['type'])
    if name is None:raise ValueError('Unconfirmed command '+str(frame['type']))
    payload=byte_array(frame['data'])
    return {'direction':direction,'command':frame['type'],'message':name,'data':decode_message(payload,name),'_wire':list(buf)}

def math_to_wire(obj):
    frame=decode_message(byte_array(obj['_wire']),'Command')
    mapping=RECV_TYPES if obj['direction']=='RECV' else SEND_TYPES
    if mapping.get(obj['command'])!=obj['message']:raise ValueError('Command/message mismatch')
    frame['type']=obj['command'];frame['data']=list(encode_message(obj['data'],obj['message']))
    return encode_message(frame,'Command')


AREA_NAMES = ('Umbrella','Soccer','Sun','Diya','Bull','Bucket',
              'Kite','WhippingTop','Rose','Butterfly','Pigeon','Rabbit')
MAX_MONEY = (1 << 63) - 1


def money(value, *, signed=False):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or int(value)!=value:
        raise ValueError('Money must be an exact integer in the chosen server unit')
    value=int(value)
    if not (-MAX_MONEY if signed else 0)<=value<=MAX_MONEY:
        raise ValueError('Money outside int64 domain')
    return value


def wire_money(value):
    value=money(value)
    if int(float(value))!=value:raise ValueError('Amount/odds cannot be represented exactly by the original double wire field')
    return value


def assert_known_fields(buf, name):
    """A new field stays raw-only until named; never silently omit it from public math."""
    table={f['number']:f for f in SCHEMA[name]}
    for n,w,v,_ in records(buf):
        if n not in table:raise ValueError('Unconfirmed field %s.f%d' % (name,n))
        f=table[n]
        if f['type'] in SCHEMA:
            if w!=2:raise ValueError('Invalid nested wire type')
            assert_known_fields(v,f['type'])


def recalculate_round(obj):
    """Normalize the public DTO, recompute derived amounts; source balance stays a snapshot."""
    out=deepcopy(obj)
    allowed={'round_id','room_id','currency','currency_code','bets','winner','pic',
             'return_odds','is_bonus','bet_total','total_win','net_win','balance_after'}
    if set(out)-allowed:raise ValueError('Unknown public math field')
    rid=out.get('round_id')
    if not isinstance(rid,str) or not rid.isdigit() or not 0<int(rid)<1<<64:raise ValueError('Invalid original wagers ID')
    if type(out.get('room_id')) is not int or out['room_id']<=0:raise ValueError('Invalid room ID')
    if not isinstance(out.get('currency'),str) or not out['currency']:raise ValueError('Missing source currency')
    if type(out.get('currency_code')) is not int or out['currency_code']<0:raise ValueError('Invalid original currency code')
    for key in ('bets','return_odds'):
        if not isinstance(out.get(key),list) or len(out[key])!=12:raise ValueError(key+' must have 12 screen-order entries')
        out[key]=[money(x) for x in out[key]]
    if any(0<x<10 for x in out['return_odds']):raise ValueError('Gross return odds must be 0 (base) or >=10')
    out['return_odds']=[10 if x==0 else x for x in out['return_odds']]
    w=out.get('winner')
    if type(w) is not int or not 1<=w<=12:raise ValueError('Invalid winning area')
    if type(out.get('pic')) is not int or out['pic']!=w:raise ValueError('Unconfirmed special picture/result')
    if out.get('is_bonus') is not False:raise ValueError('Special isBonus mode not established')
    out['bet_total']=money(sum(out['bets']))
    if out['bet_total']==0:raise ValueError('No own accepted wager')
    out['total_win']=money(out['bets'][w-1]*out['return_odds'][w-1])
    out['net_win']=money(out['total_win']-out['bet_total'],signed=True)
    out['balance_after']=money(out['balance_after'])
    return out


def validate_round(obj):
    normalized=recalculate_round(obj)
    for key in ('bet_total','total_win','net_win'):
        if key not in obj or money(obj[key],signed=key=='net_win')!=normalized[key]:
            raise ValueError('Inconsistent '+key+'; use recalculate_round after editing bets/odds/winner')
    return normalized


def round_to_math(source, *, currency):
    """Convert a correlated own-wager round, with engineering bytes kept outside the DTO."""
    frame=source['data']
    if frame['direction']!='RECV' or frame['command']!=18:raise ValueError('Expected RoomEnd')
    frames=[frame]
    bets=[0]*12
    for pair in source['spinReq']:
        req,ack=pair['request'],pair['ack'];frames.extend((req,ack))
        if req['direction']!='SEND' or ack['direction']!='RECV' or req['command']!=22 or ack['command']!=22:
            raise ValueError('Invalid own wager request/ack pair')
        if req['data']['clientCheckNum']!=ack['data']['clientCheckNum'] or clean(req['data']['detail'])!=clean(ack['data']['detail']):
            raise ValueError('Wager acknowledgment differs from request')
        for bet in ack['data']['detail']:
            t=bet['type']
            if type(t) is not int or not 1<=t<=12:raise ValueError('Unknown bet area')
            bets[t-1]=money(bets[t-1]+money(bet['bet'],signed=True))
    for f in frames:
        raw=byte_array(f['_wire'])
        if math_to_wire(f)!=raw:raise ValueError('Full frame round-trip failed')
        assert_known_fields(raw,'Command')
        assert_known_fields(byte_array(decode_message(raw,'Command')['data']),f['message'])
    d=frame['data']
    reward=d['reward']
    if len(reward)!=1 or reward[0]['value'] is not True:raise ValueError('Unconfirmed multi/empty/false reward')
    if len(d['bonus'])!=13 or d['bonus'][0]!=0:raise ValueError('Unconfirmed wire bonus table')
    obj={'round_id':source['roundId'],'room_id':source['roomId'],'currency':currency,
         'currency_code':source['currency'],'bets':bets,'winner':reward[0]['key'],
         'pic':d['pic'],'return_odds':[money(x) for x in d['bonus'][1:]],'is_bonus':d['isBonus'],
         'balance_after':money(d['postCoin'])}
    out=recalculate_round(obj)
    if out['total_win']!=money(d['win']):raise ValueError('Gross-return formula does not match original RoomEnd.win')
    return out


def math_round_to_wire(obj, source=None, *, post_coin=None):
    """Return the COMPLETE Command frame, preserving original bytes via a local sidecar.

    New/payout-edited responses require the server to supply the resulting wallet balance.
    No signature is fabricated: this Pappu Command is plaintext protobuf over TLS.
    """
    r=validate_round(obj)
    if source is not None:
        baseline=round_to_math(source,currency=r['currency'])
        for key in ('round_id','room_id','currency','currency_code','balance_after'):
            if r[key]!=baseline[key]:raise ValueError('Source context is immutable: '+key)
        if r['bets']!=baseline['bets']:raise ValueError('Frozen accepted bets are not an editable outcome')
        frame=deepcopy(source['data']);d=frame['data']
        if post_coin is None and r['total_win']!=baseline['total_win']:
            raise ValueError('Edited payout requires server-supplied post_coin')
    else:
        if post_coin is None:raise ValueError('New response requires server-supplied post_coin')
        frame={'direction':'RECV','command':18,'message':'RoomEnd','data':{},'_wire':[]};d=frame['data']
    entry=deepcopy(d['reward'][0]) if d.get('reward') else {}
    entry.update(key=r['winner'],value=True)
    d.update(win=wire_money(r['total_win']),reward=[entry],pic=r['pic'],bonus=[0]+[wire_money(v) for v in r['return_odds']],isBonus=False)
    if post_coin is not None:d['postCoin']=wire_money(post_coin)
    return math_to_wire(frame)
