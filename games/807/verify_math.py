#!/usr/bin/env python3
"""Verify an edited numeric math result through the actual encrypted HTTP endpoint."""
import copy,json,os,socket,ssl,struct,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519,ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));from math_adapter import validate,math_to_wire,wire_to_math
sys.path.insert(0,str(HERE.parent.parent/'routex'));import fg5
samples=[json.loads(x) for x in (HERE/'math/all.jsonl').read_text(encoding='utf-8').splitlines()]
original=next(x for x in samples if x['data']['win_type']==1 and x['data']['multiplier']==5 and x['data']['total_win']>0)
changed=copy.deepcopy(original);old=changed['data']['total_win'];changed['data']['multiplier']=2;changed['data']['multiplier_reel']['values'][2]=10
for a in changed['data']['line_wins']:a['win_cash']*=2/5
changed['data']['total_win']=sum(a['win_cash'] for a in changed['data']['line_wins'])
changed['postMoney']+=changed['data']['total_win']-old
validate(changed)
for mutate in [lambda x:x['data'].update(total_win=999),lambda x:x['data'].update(effect_context_f9=[{'unknown':1}]),lambda x:x['data'].update(reels=[])]:
 bad=copy.deepcopy(changed);mutate(bad)
 try:validate(bad)
 except ValueError:pass
 else:raise AssertionError('Invalid math result accepted')
keys=json.loads((HERE.parent.parent/'routex/mockkeys.json').read_text(encoding='utf-8'))
with tempfile.TemporaryDirectory(prefix='jili-807-math-') as directory:
 p=Path(directory);(p/(changed['roundIndexV2']+'.json')).write_text(json.dumps(changed), encoding='utf-8')
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 with (p/'server.log').open('w', encoding='utf-8') as log:
  env=dict(os.environ,MOCK_PORT=str(port),REPLAY_SOURCE='math',MATH_DIR=directory);env.pop('REPLAY_ROUNDS',None);env.pop('SCHEMA_PROBE',None)
  proc=subprocess.Popen([sys.executable,'-B','-u',str(HERE/'mock_server.py')],env=env,stdout=log,stderr=log)
  try:
   url='https://127.0.0.1:'+str(port);ctx=ssl._create_unverified_context()
   for _ in range(100):
    if proc.poll() is not None:raise RuntimeError((p/'server.log').read_text(encoding='utf-8'))
    try:
     with urllib.request.urlopen(url+'/fg1000/',context=ctx,timeout=1):break
    except OSError:time.sleep(.1)
   else:raise RuntimeError('Mock did not become ready')
   private=x25519.X25519PrivateKey.generate();pub=private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
   shared=private.exchange(x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(keys['x25519_pub'])))
   signer=ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(keys['ed25519_pub']))
   def request(typ,action=b''):
    body=fg5.field_varint(1,typ)+fg5.field_bytes(2,action)+fg5.field_bytes(3,bytes(20))+fg5.field_bytes(4,pub)
    with urllib.request.urlopen(urllib.request.Request(url+'/fg1000/req',data=body),context=ctx,timeout=10) as r:wire=r.read()
    signer.verify(wire[:64],wire[64:]);f=fg5.parse_fields(AESGCM(shared).decrypt(wire[64:76],wire[76:],b''));assert f.get(7,0)==0
    return f.get(5,b'')
   action=bytes.fromhex(next(r['action_hex'] for r in json.loads((HERE/'replay_samples.json').read_text(encoding='utf-8')) if r['type']==0 and r['ret']==0 and wire_to_math(bytes.fromhex(r['raw_hex']))['spinReq']==changed['spinReq']))
   request(1)
   result=request(0,action);assert result==math_to_wire(changed);assert wire_to_math(result)==changed
   balance=request(2);assert struct.unpack('<d',fg5.parse_fields(fg5.parse_fields(balance)[1])[2])[0]==changed['postMoney']
  finally:
   proc.terminate()
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:proc.kill();proc.wait()
report={'original_win':old,'edited_win':changed['data']['total_win'],'original_multiplier':5,'edited_multiplier':2,'encrypted_http_replay':'passed','balance_polling':'passed','invalid_totals_rejected':True,'unverified_nonempty_f9_rejected':True,'invalid_geometry_rejected':True}
(HERE/'math/EDIT_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n', encoding='utf-8');print(json.dumps(report))
