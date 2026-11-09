"""Prove edited math is picked up by the next local encrypted SPIN."""
import json,os,socket,ssl,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519,ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from math_adapter import *
sys.path.insert(0,str(HERE.parent.parent/'routex'));import fg5
keys=json.loads((HERE.parent.parent/'routex/mockkeys.json').read_text())
signer=ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(keys['ed25519_pub']))
private=x25519.X25519PrivateKey.generate()
pub=private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
shared=private.exchange(x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(keys['x25519_pub'])))
ctx=ssl._create_unverified_context()
with tempfile.TemporaryDirectory(prefix='jili545-hot-') as tmp:
    original=json.loads(next(p for p in sorted((HERE/'math').glob('*.json')) if p.stem.isdigit()).read_text())
    path=Path(tmp)/(original['roundIndexV2']+'.json');path.write_text(json.dumps(original))
    action=fg5.parse_fields(math_to_wire(original))[23]
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    log=(HERE/'runtime/hot_reload.log').open('w')
    process=subprocess.Popen([sys.executable,'-B','-u',str(HERE/'mock_server.py')],env=dict(os.environ,MOCK_PORT=str(port),REPLAY_SOURCE='math',MATH_DIR=tmp,WATCH_MATH='1'),stdout=log,stderr=log)
    def request():
        body=fg5.field_varint(1,0)+fg5.field_bytes(2,action)+fg5.field_bytes(3,bytes(20))+fg5.field_bytes(4,pub)
        with urllib.request.urlopen(urllib.request.Request('https://127.0.0.1:%s/cc3x3/req'%port,data=body),context=ctx,timeout=5) as r:wire=r.read()
        signer.verify(wire[:64],wire[64:]);pt=AESGCM(shared).decrypt(wire[64:76],wire[76:],b'');f=fg5.parse_fields(pt)
        return f.get(7,0),f.get(5,b'')
    try:
        for _ in range(100):
            if process.poll() is not None:raise RuntimeError('Mock exited')
            try:
                with urllib.request.urlopen('https://127.0.0.1:%s/cc3x3/'%port,context=ctx,timeout=1):break
            except OSError:time.sleep(.1)
        ret,raw=request();assert ret==0
        original_win=wire_to_math(raw)['data']['TotalWin']
        changed=json.loads(json.dumps(original));changed['data']['TotalWin']=original_win+7.25;changed['postMoney']+=7.25
        path.write_text(json.dumps(changed))
        ret,raw=request();assert ret==0
        result=wire_to_math(raw);assert result['data']['TotalWin']==original_win+7.25
        assert result['postMoney']==changed['postMoney']
        path.write_text('{broken');assert request()==(400,b'')
        path.write_text(json.dumps(changed));assert request()[0]==0
        report={'encrypted_hot_reload':True,'edited_win_applied':True,'edited_balance_applied':True,'invalid_json_rejected':True,'recovery_without_restart':True}
        (HERE/'hot_reload_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        log.close()
