"""664 replay pools: exact bet/mode, preserving unknown request fields."""
import json
from pathlib import Path
from math_adapter import records,math_to_wire,fields
from request_adapter import request_to_math

def action_key(action):
 obj=request_to_math(action)
 # UI context f25 is intentionally excluded. Business fields retain presence,
 # unknown fields and selector values; missing and explicit zero mean the same.
 def node(buf,known):
  values={n:default for n,default in known.items()};unknown=[]
  for n,w,v,raw in records(buf):
   if n in known:values[n]=(w,v.hex()if isinstance(v,bytes)else v)
   else:unknown.append(raw.hex())
  return [sorted(values.items()),unknown]
 top=[]
 for n,w,v,raw in records(action):
  if n==25:continue
  if n==23 and w==2:top.append((n,node(v,{1:(0,0),2:(0,0),3:(1,'0000000000000000')})))
  elif n==26 and w==2:top.append((n,node(v,{1:(0,0)})))
  else:top.append((n,raw.hex()))
 return json.dumps(sorted(top),separators=(',',':'))

class ReplayPool:
 def __init__(self,rows,source='math',directory=None,rounds='',watch=True):
  self.rows=rows;self.source=source;self.directory=Path(directory or Path(__file__).parent/'math');self.selected=rounds.split(',')if rounds else [];self.watch=watch;self.signature=None;self.pools={};self.metadata={};self.refresh()
 def refresh(self):
  paths=[self.directory/(rid+'.json')for rid in self.selected]if self.selected else sorted(p for p in self.directory.glob('[0-9]*.json')if p.stem.isdigit())
  signature=tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size)for p in paths)if self.source=='math'else ('wire',tuple(self.selected))
  if self.pools and (not self.watch or signature==self.signature):return self.pools
  rows={r['round_id']:r for r in self.rows if r['type']==0 and r['ret']==0};pools={};meta={}
  ids=self.selected or sorted(rows)
  for rid in ids:
   if rid not in rows:raise ValueError('Unknown captured round: '+rid)
   original=rows[rid];raw=bytes.fromhex(original['raw_hex'])if self.source=='wire'else math_to_wire(json.loads((self.directory/(rid+'.json')).read_text()))
   # Match by the response echo so intentional math edits to inputs are reflected.
   key=action_key(fields(raw)[23][1]);pools.setdefault(key,[]).append(raw);meta[key]={'sample_count':len(pools[key]),'request':request_to_math(fields(raw)[23][1])}
  if not pools:raise ValueError('No valid replay samples')
  self.pools,self.metadata,self.signature=pools,meta,signature;return pools
