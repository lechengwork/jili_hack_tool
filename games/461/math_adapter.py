"""461 codec derived from pirate2Proto; preserves unknown fields and wire presence.

_wire is an optional integer-array engineering sidecar. Named fields are authoritative:
editing them changes the encoding; unchanged fields retain their exact original bytes.
"""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
SCHEMA = json.loads((HERE / 'math_schema.json').read_text())
SCHEMA['Envelope'] = [
    {'number':n, 'name':k, 'type':t, 'repeated':False} for n,k,t in
    [(1,'data','SpinAck'), (2,'f2','opaque'), (3,'f3','double'),
     (6,'f6','double'), (20,'roundIndexV2','uint64'), (23,'spinReq','opaque')]]



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
    if t=='bool':return bool(v)
    return (v&0xffffffff)-(1<<32) if v&(1<<31) else v&0xffffffff


def decode_message(buf,name='SpinAck',sidecar=True):
    table={f['number']:f for f in SCHEMA[name]}
    out={f['name']:default(f) for f in table.values()};seen=set()
    for n,w,v,_ in records(buf):
        if n not in table:continue
        f=table[n];t=f['type'];k=f['name']
        if n in seen and not f['repeated']:raise ValueError('Duplicate scalar '+name+'.'+k)
        seen.add(n)
        if f['repeated'] and t in ('double','int32','bool') and w==2:
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
    if type(v) is not int or not -(1<<31)<=v<(1<<31):raise ValueError('Expected int32')
    return 0,varint(v)


def byte_array(v):
    if not isinstance(v,list) or any(type(x) is not int or not 0<=x<=255 for x in v):
        raise ValueError('Expected integer array in range 0..255')
    return bytes(v)


def encode_message(obj,name='SpinAck'):
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
            if t in ('int32','bool','double'):
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


def wire_to_math(buf):
    out=decode_message(bytes(buf),'Envelope')
    if not out['roundIndexV2'].endswith('461'):
        raise ValueError('Not a 461 round')
    # Independent original frontend codec check on every successful SPIN.
    import subprocess
    check=subprocess.run(['node',str(HERE/'analysis/check_payload.cjs')],
                         input=json.dumps(out),text=True,capture_output=True,timeout=10)
    if check.returncode:
        raise ValueError('Original pirate2Proto verification failed: '+check.stderr[:400])
    return out


def math_to_wire(obj):
    if not isinstance(obj.get('roundIndexV2'),str) or not obj['roundIndexV2'].endswith('461'):
        raise ValueError('Expected 461 round ID string')
    return encode_message(obj,'Envelope')
