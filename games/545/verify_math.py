"""Real-vector, mutation, unknown-field and malformed-wire regression checks."""
import copy,json,subprocess,sys
from pathlib import Path
from math_adapter import *

files=sorted(p for p in (HERE/'math').glob('*.json') if p.stem.isdigit())
if not files:raise ValueError('No real samples')
for p in files:
    obj=json.loads(p.read_text());raw=bytes(obj['_wire'])
    assert math_to_wire(obj)==raw,p
    assert math_to_wire(wire_to_math(raw))==raw,p
    env=fields(raw)
    if 3 in env:assert struct.unpack('<d',env[3][1])[0]==obj['data']['TotalWin']
# Preserve a genuinely unknown envelope field and an unknown nested field on edits.
raw=bytes(json.loads(files[0].read_text())['_wire'])
unknown=field(111,0,varint(987))+field(112,5,b'\x01\x02\x03\x04')
obj=wire_to_math(raw+unknown);assert math_to_wire(obj)==raw+unknown
obj['postMoney']+=1;changed=math_to_wire(obj);assert changed.endswith(unknown)
assert wire_to_math(changed)['postMoney']==obj['postMoney']
first=next(records(raw));nested=first[2]+field(109,2,b'future-field')
nraw=field(1,2,nested)+raw[len(first[3]):]
obj=wire_to_math(nraw);assert math_to_wire(obj)==nraw
obj['data']['TotalWin']=42.5;changed=math_to_wire(obj)
assert b'future-field' in changed
assert wire_to_math(changed)['data']['TotalWin']==42.5
for malformed in (b'\x0a\x05x',b'\x09\x01',b'\x80',b'\x00'):
    try:list(records(malformed))
    except ValueError:pass
    else:raise AssertionError('Accepted malformed wire')
report={'real_payload_roundtrips':len(files),'unknown_envelope_retained':True,
        'unknown_nested_retained_after_edit':True,'named_edit_applied':True,
        'malformed_wire_rejected':True}
(HERE/'math_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
subprocess.run(['node',str(HERE/'analysis/verify_frontend.cjs')],check=True)
