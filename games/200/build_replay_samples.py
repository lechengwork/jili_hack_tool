#!/usr/bin/env python3
"""Prepare sanitized, credential-free Pappu replay initialization from local capture."""
import importlib.util,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pappu_codec_build',HERE/'math_adapter.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

def replace(buf,number,wire,value):
    out=bytearray();found=False
    for n,w,v,raw in c.records(buf):
        if n==number:
            if not found:out.extend(c.field(number,wire,value));found=True
        else:out.extend(raw)
    if not found:out.extend(c.field(number,wire,value))
    return bytes(out)

def build():
    index=json.loads((HERE/'math_sources.json').read_text())['rounds']
    sessions={v['session']for v in index.values()}
    if len(sessions)!=1:raise ValueError('Select one source session; do not mix logins')
    session=HERE/'webcap'/next(iter(sessions))
    bycmd={}
    for line in (session/'frames.jsonl').read_text().splitlines():
        r=json.loads(line)
        if r['dir']!='RECV':continue
        try:d=c.decode_message(bytes.fromhex(r['hex']),'Command')
        except ValueError:continue
        bycmd.setdefault(d['type'],bytes.fromhex(r['hex']))
    welcome=c.decode_message(bycmd[0],'Command');payload=c.byte_array(welcome['data'])
    player=c.fields(payload)[3][1]
    player=replace(player,1,0,c.varint(200001))
    player=replace(player,2,2,b'Replay200')
    # Common framework additionally mirrors the uid in PlayerInfo.f6.
    player=replace(player,6,0,c.varint(200001))
    payload=replace(payload,3,2,player)
    welcome['data']=list(payload)
    # Keep the original shared-framework configuration; replace identity, never copy auth requests/URLs.
    welcome_bytes=c.encode_message(welcome,'Command')
    theme=c.clean(c.decode_message(c.byte_array(c.decode_message(bycmd[10],'Command')['data']),'JoinThemeAck'))
    room=c.clean(c.decode_message(c.byte_array(c.decode_message(bycmd[11],'Command')['data']),'JoinRoomAck'))
    wallet=c.clean(c.decode_message(welcome_bytes,'Command'))
    wallet=c.decode_message(c.byte_array(wallet['data']),'LoginDataAck')['player']['wallet']
    rows=[]
    for rid,info in index.items():
        public=json.loads((HERE/'math'/(rid+'.json')).read_text());c.validate_round(public)
        original=json.loads((HERE/'webcap'/info['session']/'math_wire'/(rid+'.json')).read_text())
        frame=original['data'];raw=c.byte_array(frame['_wire'])
        if c.math_to_wire(frame)!=raw:raise ValueError('Original round frame round-trip mismatch')
        rows.append({'round_id':rid,'original_math':c.round_to_math(original,currency=info['currency']),
                     'result_hex':raw.hex()})
    auxiliary={str(cmd):bycmd[cmd].hex()for cmd in(95,100,105,112,200)if cmd in bycmd}
    for raw in auxiliary.values():
        body=c.byte_array(c.decode_message(bytes.fromhex(raw),'Command')['data'])
        if len(body)>16:raise ValueError('Unexpected auxiliary data; review before including')
    out={'game_id':200,'uid':200001,'welcome_hex':welcome_bytes.hex(),'theme':theme,'room':room,
         'wallet_ratio':wallet['ratio'],'currency_code':wallet['currency'],'currency':'IDR',
         'auxiliary':auxiliary,'rounds':rows}
    text=json.dumps(out,ensure_ascii=False,indent=2)+'\n'
    if any(x in text for x in('ssoKey','bearer ','eyJ','req_body_hex','tryplayer')):raise ValueError('Private capture data in replay package')
    (HERE/'replay_samples.json').write_text(text)
    print('Prepared sanitized Pappu init and %d original result frames; no login credentials'%len(rows))

if __name__=='__main__':build()
