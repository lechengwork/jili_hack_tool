"""Independent original-codec fixture checks; never reported as live samples."""
import copy,json,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import math_adapter as a
from live_math_461 import export_spin

fixture={'RoundQueue':[{'ComboStageData':[{'ComboStageSymbol':[{'Col':[1,2,3]}], 'ComboStageWin':12.5,'ComboStageMults':[{'Col':[0,2,0]}], 'AwardDataVec':[{'Symbol':2,'Count':3,'Win':12.5,'PosVec':[0,1,2]}], 'FillSymbols':[{'Col':[4,5]}], 'FillMults':[{'Col':[1,3]}]}], 'RoundWin':12.5,'RoundMult':2,'AddMult':1,'AwardTypeFlag':3,'FreeRemainRound':2,'FreeNowRound':1,'FreeTotalRound':3,'MaxFlag':False}], 'FreeTotalWin':12.5,'TotalWin':12.5,'ShowIndex':'fixture','NowMoney':987.5,'AckType':0,'RTP':0.96}
js="const c=require('./games/461/analysis/load_codec.cjs');const fs=require('fs');const o=JSON.parse(fs.readFileSync(0));process.stdout.write(Buffer.from(c.SpinAck.encode(c.SpinAck.fromObject(o)).finish()).toString('hex'));"
payload=bytes.fromhex(subprocess.check_output(['node','-e',js],input=json.dumps(fixture).encode(),cwd=HERE.parents[1]).decode())
wire=a.field(1,2,payload)+a.field(20,0,a.varint(123456461))+a.field(23,2,b'\x09'+__import__('struct').pack('<d',10))+a.field(99,2,b'unknown')
math=a.wire_to_math(wire)
assert a.math_to_wire(math)==wire
changed=copy.deepcopy(math);changed['data']['TotalWin']=13.5
assert a.wire_to_math(a.math_to_wire(changed))['data']['TotalWin']==13.5
assert b'unknown' in a.math_to_wire(changed)
with tempfile.TemporaryDirectory() as td:
 game=Path(td)/'461';session=game/'webcap'/'fixture'
 decoded={'type':0,'ret':0,'_sig_ok':True,'raw':list(wire)}
 for bad in [{'type':1},{'ret':1},{'_sig_ok':False}]:
  assert export_spin(dict(decoded,**bad),game,session,a.wire_to_math,a.math_to_wire) is None
 assert export_spin(decoded,game,session,a.wire_to_math,a.math_to_wire)['ok']
 target=game/'math/123456461.json';target.write_text('{"edited":true}')
 assert not export_spin(decoded,game,session,a.wire_to_math,a.math_to_wire)['ok']
 assert json.loads(target.read_text())=={'edited':True}
 assert (session/'math/123456461.json').exists()
 assert (session/'math_conflicts.jsonl').exists()
 bad=dict(decoded,raw=[10,255]);assert not export_spin(bad,game,session,a.wire_to_math,a.math_to_wire)['ok']
 assert (session/'math_errors.jsonl').exists()
report={'fixture_only':True,'live_success_spins':0,'original_codec':'pirate2Proto','full_payload_byte_roundtrip':True,'edited_named_field_reencoded':True,'unknown_field_preserved':True,'atomic_publish_and_conflict_preservation':True,'nonspin_failed_unverified_filtered':True,'decode_failure_raw_retained':True,'envelope_semantics':'neutral pending live evidence'}
(HERE/'adapter_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
