#!/usr/bin/env python3
"""Generate the observed 807 math contract and samples; verify independent protoc encoding."""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory, text_format

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from math_adapter import SCHEMA, fields, wire_to_math, math_to_wire

wire=['syntax = "proto3";','package jili.wire.v807;','// Observed wire structure, not a complete specification of unseen features.','message Empty {}', 'message Ante { int32 level=1; } message BetInfo { double bet=1; Empty reserved25=25; Ante ante=26; }']
math=['syntax = "proto3";','package jili.math.v807;', '// Numeric math interface; field names ending fN intentionally retain uncertain semantics.', 'message PackedValues { repeated int32 values=1; }']
for name,fs in SCHEMA.items():
 for lines,is_wire in [(wire,True),(math,False)]:
  lines.append('message '+name+' {')
  for f in fs:
   typ=f['type'];prefix='repeated ' if f['repeated'] else ''
   if typ=='packed_presence':typ='bytes' if is_wire else 'PackedValues';prefix='optional ' if is_wire else ''
   lines.append('  '+prefix+typ+' '+f['name']+' = '+str(f['number'])+';')
  lines.append('}')
wire+=['message SpinResult { SpinAck data=1; Empty service=2; double total_win=3; double postMoney=6; uint64 roundIndexV2=20; BetInfo spinReq=23; }']
math+=['message Ante { int32 level=1; }','message Special { Ante ante=1; }','message SpinRequest { double bet=1; Special special=2; }', 'message Service {}', 'message SpinResult { SpinAck data=1; Service service=2; double postMoney=3; string roundIndexV2=4; SpinRequest spinReq=5; }']
(HERE/'wire_807.proto').write_text('\n'.join(wire)+'\n', encoding='utf-8')
(HERE/'math_807.proto').write_text('\n'.join(math)+'\n', encoding='utf-8')
for name in ['wire_807','math_807']:
 subprocess.run([sys.executable,'-m','grpc_tools.protoc','-I'+str(HERE),'--descriptor_set_out='+str(HERE/(name+'.desc')),str(HERE/(name+'.proto'))],check=True)

pool=descriptor_pool.DescriptorPool()
compiled_set=descriptor_pb2.FileDescriptorSet.FromString((HERE/'wire_807.desc').read_bytes())
for file in compiled_set.file:pool.Add(file)
CompiledSpin=message_factory.GetMessageClass(pool.FindMessageTypeByName('jili.wire.v807.SpinResult'))

def text_message(obj,name):
 result=[]
 for f in SCHEMA[name]:
  key=f['name'];typ=f['type'];v=obj[key]
  if typ=='packed_presence':
   if v is not None:result.append(key+': ""')
  elif typ in SCHEMA:
   for x in v if f['repeated'] else [v]:result.append(key+' { '+text_message(x,typ)+' }')
  elif f['repeated']:
   for x in v:result.append(key+': '+str(x))
  else:result.append(key+': '+str(v).lower())
 return ' '.join(result)

rows=[r for r in json.loads((HERE/'replay_samples.json').read_text(encoding='utf-8')) if r['type']==0 and r['ret']==0]
math_dir=HERE/'math';math_dir.mkdir(exist_ok=True)
vectors=[];all_samples=[];wins=0;special=[];types=Counter();totals=[]
for row in rows:
 raw=bytes.fromhex(row['raw_hex']);env=wire_to_math(raw);rid=env['roundIndexV2'];data=env['data'];assert math_to_wire(env)==raw
 text='data { '+text_message(data,'SpinAck')+' } service {} total_win: '+str(data['total_win'])+' postMoney: '+str(env['postMoney'])+' roundIndexV2: '+rid+' spinReq { bet: '+str(env['spinReq']['bet'])+' reserved25 {} '+ ('ante { level: '+str(env['spinReq']['special']['ante']['level'])+' }' if 'ante' in env['spinReq']['special'] else '')+' }'
 compiled=text_format.Parse(text,CompiledSpin()).SerializeToString()
 assert compiled==raw,'Independent compiled codec mismatch '+rid
 (math_dir/(rid+'.json')).write_text(json.dumps(env,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
 vectors.append({'round_id':rid,'payload_hex':fields(raw)[1][1].hex(),'response_payload_hex':raw.hex()})
 all_samples.append(env);types[data['win_type']]+=1;totals.append(data['total_win'])
 if data['total_win']>0:wins+=1
 if data['extra_steps'] or data['effect_symbols_f6'] or data['effect_symbols_f7']:special.append(rid)
(math_dir/'all.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in all_samples), encoding='utf-8')
(math_dir/'roundtrip_vectors.jsonl').write_text(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in vectors), encoding='utf-8')
coverage={'samples':len(rows),'winning_rounds':wins,'losing_rounds':len(rows)-wins,'bets':sorted({x['spinReq']['bet'] for x in all_samples}),'ante_modes':dict(Counter(x['data']['ante_mode'] for x in all_samples)),'win_types':dict(types),'special_rounds':special,'max_observed_win':max(totals),'wire_roundtrips':len(rows),'independent_compiled_protobuf_roundtrips':len(rows),'rtp_field_f21_values':sorted({x['data']['config_value_f21'] for x in all_samples}),'line_payrate_observations':{'0':1,'1':2,'2':3.5,'3':5,'4':6,'5':7.5,'6':10},'uncertain_semantics':['effect_symbols_f6','effect_symbols_f7','effect_indices_f8','effect_context_f9','effect_slots_f13','effect_slots_f17','config_value_f21'],'f9_coverage':'Repeated empty contexts: zero, one or two occurrences observed. Nonempty bodies rejected until defined.','limitations':'Two base bets and ordinary/1.5x/8x modes observed; this is sample coverage, not a probability distribution or a full rules specification.'}
(math_dir/'COVERAGE.json').write_text(json.dumps(coverage,indent=2)+'\n', encoding='utf-8')
print(json.dumps(coverage))
