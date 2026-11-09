#!/usr/bin/env python3
"""Verify exact captures, clean proto, edited reverse adapter, and conflict protection."""
import json,subprocess,tempfile
from pathlib import Path
from copy import deepcopy
from math_adapter import round_to_math,math_to_round_wire,wire_to_math
from atomic_math import _write_json
HERE=Path(__file__).resolve().parent

def verify(session):
    n=0;vectors=[]
    for p in sorted((session/'math_wire').glob('*.json')):
        source=json.loads(p.read_text());value=round_to_math(source)
        original=[source['request'],source['ack'],*source['cashout_requests'],*source['cashouts'],source['end']]
        assert [b.hex() for b in math_to_round_wire(value,source)]==[f['_wire'] for f in original]
        assert json.loads((session/'math'/(p.stem+'.json')).read_text())==value
        assert json.loads((HERE/'math'/(p.stem+'.json')).read_text())==value,'Shared math modified: review conflict'
        edited=deepcopy(value);edited['data']['flyEnd']['endRate']=1.125
        out=math_to_round_wire(edited,source)[-1]
        decoded=wire_to_math([{'dir':'RECV','hex':out.hex()}])[0]
        assert decoded['data']['endRate']==1.125
        vectors.append(value);n+=1
    js="""const fs=require('fs'),pb=require('./games/545/runtime/node_modules/protobufjs');const T=pb.parse(fs.readFileSync('./games/224/math_224.proto','utf8'),{keepCase:true}).root.lookupType('gorush_224.Round');let input='';process.stdin.on('data',x=>input+=x);process.stdin.on('end',()=>{for(const v of JSON.parse(input)){const m=T.fromObject(v),err=T.verify(m);if(err)throw Error(err);const r=T.toObject(T.decode(T.encode(m).finish()),{longs:String});if(r.round_id!==v.round_id||r.data.betResponse.roundIndex!==v.round_id)throw Error('int64 precision loss')}console.log('clean math proto verified')});"""
    subprocess.run(['node','-e',js],cwd=HERE.parent.parent,input=json.dumps(vectors),text=True,check=True,capture_output=True)
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'round.json';_write_json(p,{'team':'edited'})
        try:_write_json(p,{'capture':'original'})
        except FileExistsError:pass
        else:raise AssertionError('Conflict overwritten')
        assert json.loads(p.read_text())=={'team':'edited'}
    report={'verified_rounds':n,'original_codec':True,'full_request_response_frame_byte_roundtrip':True,'clean_proto_int64_precision':True,'edited_reverse_adapter':True,'atomic_conflict_protection':True,'signature':'No independent application signature in observed plaintext protobuf/TLS frames','currency':'IDR'}
    (session/'math_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return report
if __name__=='__main__':verify(Path((HERE/'current_session.txt').read_text().strip()))
