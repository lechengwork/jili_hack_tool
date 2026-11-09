"""Check live math edits/additions and invalid-input recovery over encrypted localhost."""
import copy,json,os,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import x25519,ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT/'routex'));import fg5
from math_adapter import fields,math_to_wire,decode_message,field,varint
from request_adapter import request_to_math,math_to_request
keys=json.loads((ROOT/'routex/mockkeys.json').read_text())
with tempfile.TemporaryDirectory()as td:
 directory=Path(td);rid='2490024636000020461';original=json.loads((HERE/'math'/(rid+'.json')).read_text());target=directory/(rid+'.json');target.write_text(json.dumps(original))
 with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 env=dict(os.environ,REPLAY_PORT=str(port),REPLAY_SOURCE='math',MATH_DIR=str(directory),SELECT_ROUNDS='',WATCH_MATH='1')
 with (HERE/'replay/reload-test.log').open('w')as log:
  proc=subprocess.Popen([sys.executable,'-B','-u',str(HERE/'replay_server.py')],env=env,stdout=log,stderr=log)
  try:
   base='http://127.0.0.1:%d'%port
   for _ in range(100):
    if proc.poll()is not None:raise RuntimeError('Replay failed to start')
    try:
     with urllib.request.urlopen(base+'/__replay_status',timeout=.5):break
    except OSError:time.sleep(.1)
   else:raise RuntimeError('Replay startup timeout')
   private=x25519.X25519PrivateKey.generate();pub=private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw);key=private.exchange(x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(keys['x25519_pub'])))
   signer=ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(keys['ed25519_pub']))
   action=bytes(original['spinReq'])
   def spin(request=action):
    body=fg5.field_varint(1,0)+fg5.field_bytes(2,request)+fg5.field_bytes(3,bytes(20))+fg5.field_bytes(4,pub)
    with urllib.request.urlopen(urllib.request.Request(base+'/pirate2/req',data=body),timeout=10)as response:wire=response.read()
    signer.verify(wire[:64],wire[64:]);p=fg5.parse_fields(AESGCM(key).decrypt(wire[64:76],wire[76:],b''));return p.get(7,0),p.get(5,b'')
   assert spin()==(0,math_to_wire(original))
   changed=copy.deepcopy(original);changed['data']['TotalWin']+=123;target.write_text(json.dumps(changed))
   ret,payload=spin();assert ret==0 and decode_message(fields(payload)[1][1])['TotalWin']==changed['data']['TotalWin']
   target.write_text('{bad json');assert spin()==(400,b'')
   target.write_text(json.dumps(original));assert spin()[0]==0
   added=copy.deepcopy(original);added['roundIndexV2']='9999999999999999461';(directory/(added['roundIndexV2']+'.json')).write_text(json.dumps(added))
   found=False
   for _ in range(3):
    ret,payload=spin();assert ret==0
    if str(fields(payload)[20][1])==added['roundIndexV2']:found=True
   assert found,'New math round did not enter replay pool'
   unsupported=request_to_math(action);unsupported['context']['f4']=1
   assert spin(math_to_request(unsupported))==(400,b''),'Unknown 461 context accepted'
   with urllib.request.urlopen(base+'/__replay_status')as response:status=json.load(response)
   report={'named_field_edit_reloaded':True,'invalid_json_rejected_and_recovery_verified':True,'new_numeric_round_loaded':True,'unknown_context_rejected':True,'encrypted_signature_verified':True,'original_math_unchanged':json.loads((HERE/'math'/(rid+'.json')).read_text())==original,'status_spins':status['spins']}
   (HERE/'replay_math_reload_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
  finally:proc.terminate();proc.wait(timeout=10)
