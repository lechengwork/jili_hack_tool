#!/usr/bin/env python3
"""Exercise encrypted localhost replay, all 438 payloads and every mode."""
import argparse,copy,json,os,socket,struct,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519,ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT/'routex'));import fg5
from math_adapter import fields,math_to_wire,decode_message
from replay_pool import action_key
ap=argparse.ArgumentParser();ap.add_argument('--source',choices=['wire','math'],default='math');args=ap.parse_args()
with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
env=dict(os.environ,REPLAY_PORT=str(port),REPLAY_SOURCE=args.source,SELECT_ROUNDS='',WATCH_MATH='1');log=(HERE/'replay/verify.log').open('w');proc=subprocess.Popen([sys.executable,'-B','-u',str(HERE/'replay_server.py')],env=env,stdout=log,stderr=log)
base='http://127.0.0.1:%d'%port;keys=json.loads((ROOT/'routex/mockkeys.json').read_text());signer=ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(keys['ed25519_pub']));server_pub=x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(keys['x25519_pub']))
rows=json.loads((HERE/'replay_samples.json').read_text());lookup={r['round_id']:r for r in rows if r['type']==0 and r['ret']==0};groups={}
for rid in sorted(lookup):
 r=lookup[rid];raw=bytes.fromhex(r['raw_hex'])if args.source=='wire'else math_to_wire(json.loads((HERE/'math'/(rid+'.json')).read_text()));key=action_key(fields(raw)[23][1]);groups.setdefault(key,[]).append((raw,bytes.fromhex(r['action_hex'])))
class Client:
 def __init__(self):
  p=x25519.X25519PrivateKey.generate();self.pub=p.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw);self.shared=p.exchange(server_pub)
 def request(self,typ,action=b''):
  body=fg5.field_varint(1,typ)+fg5.field_bytes(2,action)+fg5.field_bytes(3,bytes(20))+fg5.field_bytes(4,self.pub)
  req=urllib.request.Request(base+'/lj500/req',data=body,headers={'Content-Type':'application/x-protobuf'})
  with urllib.request.urlopen(req,timeout=10)as r:wire=r.read()
  signer.verify(wire[:64],wire[64:]);p=fg5.parse_fields(AESGCM(self.shared).decrypt(wire[64:76],wire[76:],b''));assert p.get(3,0)==typ;return p.get(7,0),p.get(5,b'')
try:
 for _ in range(100):
  if proc.poll()is not None:raise RuntimeError('Replay startup failed')
  try:
   with urllib.request.urlopen(base+'/__replay_status',timeout=.5)as r:json.load(r)
   break
  except OSError:time.sleep(.1)
 else:raise RuntimeError('Startup timeout')
 with urllib.request.urlopen(urllib.request.Request(base+'/sso-login.api',data=b'{}'))as r:sso=json.load(r);assert sso['profile']['account']=='local-replay-664'and sso['token']=='0'*40
 with urllib.request.urlopen(base+'/lj500/src/polyfills.bundle.5adbf.js')as r:assert b'installed C2 compile-hook'in r.read()
 a,b=Client(),Client();init=next(r for r in rows if r['type']==1);assert a.request(1,bytes.fromhex(init['action_hex']))==(init['ret'],bytes.fromhex(init['raw_hex']))
 count=0;last=0;bonus_modes=set()
 for key,pool in groups.items():
  for expected,action in pool+[pool[0]]:
   ret,actual=a.request(0,action);assert ret==0
   af,ef=fields(actual),fields(expected);rid=af.pop(20)[1];ef.pop(20);assert af==ef,'Payload changed outside round ID';assert rid>last and rid%1000==664;last=rid;count+=1
   data=decode_message(fields(actual)[1][1]);
   if data['GetBonus']==2:bonus_modes.add(data['Extra'])
   ret,balance=a.request(2);assert ret==0 and fields(fields(balance)[1][1])[2]==fields(actual)[6]
  assert b.request(0,pool[0][1])==(0,pool[0][0]),'Client state leaked'
 first=next(iter(groups.values()))[0];bad=fg5.enc_tag(1,1)+struct.pack('<d',99999.);assert a.request(0,bad)==(400,b'');assert a.request(999)==(400,b'')
 # The exact same canonical pool accepts missing versus explicit selector zeros.
 assert all(action_key(action)==key for key,pool in groups.items()for raw,action in pool)
 report={'source':args.source,'verified_spins':len(lookup),'action_pools':len(groups),'encrypted_spin_responses_tested':count,'all_payloads_preserved_except_monotonic_round_id':True,'signature_and_aes_gcm_verified':True,'wraparound_verified':True,'balance_poll_verified':True,'client_isolation_verified':True,'unsupported_bet_mode_rejected':True,'synthetic_sso':True,'bonus_extra_values_verified':sorted(bonus_modes),'browser_visual_verification':'pending'}
 (HERE/('replay_validation_'+args.source+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
finally:
 proc.terminate();proc.wait(timeout=10);log.close()
