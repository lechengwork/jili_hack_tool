"""461 exact bet/purchase pools with byte-preserving edits and live math reload."""
import json
from pathlib import Path
from math_adapter import records,math_to_wire,fields,decode_message
from request_adapter import request_to_math

def action_key(action):
 request_to_math(action)
 def nested(buf,defaults):
  values=dict(defaults);unknown=[]
  for n,w,v,raw in records(buf):
   if n in defaults:values[n]=(w,v.hex()if isinstance(v,bytes)else v)
   else:unknown.append(raw.hex())
  return [sorted(values.items()),unknown]
 # Only this game's observed explicit context zeros normalize to omitted defaults.
 context=nested(b'',{1:(0,0),2:(0,0),4:(0,0)})
 top=[]
 for n,w,v,raw in records(action):
  if n==25 and w==2:context=nested(v,{1:(0,0),2:(0,0),4:(0,0)})
  elif n==23 and w==2:top.append((n,nested(v,{1:(0,0),2:(0,0),3:(1,'0000000000000000')})))
  else:top.append((n,raw.hex()))
 top.append((25,context))
 return json.dumps(sorted(top),separators=(',',':'))

class ReplayPool:
 def __init__(self,rows,source='math',directory=None,rounds='',watch=True):
  self.rows={r['round_id']:r for r in rows if r['type']==0 and r['ret']==0};self.source=source
  self.directory=Path(directory or Path(__file__).parent/'math');self.selected=rounds.split(',')if rounds else []
  self.watch=watch;self.signature=None;self.pools={};self.metadata={};self.refresh()
 def refresh(self):
  if self.pools and not self.watch:return self.pools
  paths=[self.directory/(rid+'.json')for rid in self.selected]if self.selected else sorted(p for p in self.directory.glob('[0-9]*.json')if p.stem.isdigit())
  signature=tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size)for p in paths)if self.source=='math'else ('wire',tuple(self.selected))
  if self.pools and signature==self.signature:return self.pools
  ids=[p.stem for p in paths]if self.source=='math'else self.selected or sorted(self.rows)
  pools={};meta={}
  for rid in ids:
   if self.source=='wire':raw=bytes.fromhex(self.rows[rid]['raw_hex'])
   else:
    value=json.loads((self.directory/(rid+'.json')).read_text());raw=math_to_wire(value)
    if value['roundIndexV2']!=rid:raise ValueError('Math filename/roundIndexV2 mismatch: '+rid)
   f=fields(raw);decode_message(f[1][1]);echo=f[23][1]
   key=action_key(echo);pools.setdefault(key,[]).append(raw)
   meta[key]={'sample_count':len(pools[key]),'request':request_to_math(echo)}
  if not pools:raise ValueError('No valid 461 replay samples')
  self.pools,self.metadata,self.signature=pools,meta,signature;return pools
