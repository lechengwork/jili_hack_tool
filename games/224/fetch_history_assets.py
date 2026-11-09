#!/usr/bin/env python3
"""Fetch only original public history-entry dependencies into this game's asset tree."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,re,requests,hashlib
HERE=Path(__file__).resolve().parent
SOURCE=Path(json.loads((HERE/'history_source.local.json').read_text())['session'])
ROOT=HERE/'history/static';ROOT.mkdir(parents=True,exist_ok=True)
entry=(SOURCE/'history_capture/entry.response.html').read_bytes()
target=ROOT/'zh-CN/ingame/index.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(entry)
paths=sorted(set(re.findall(r'(?:src|href)="(/_nuxt/[^"#?]+)',entry.decode())))
def fetch(path):
 r=requests.get('https://uat-history.jlfafafa3.com'+path,timeout=30,headers={'User-Agent':'Mozilla/5.0','Accept-Encoding':'gzip, deflate'});r.raise_for_status();p=ROOT/path.lstrip('/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(r.content);return{'path':path,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest()}
with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(fetch,paths))
(HERE/'history/asset_manifest.json').write_text(json.dumps({'origin':'https://uat-history.jlfafafa3.com','files':results},indent=2)+'\n')
print('Original public history dependencies fetched:',len(results))
for p in (ROOT/'_nuxt').glob('*.js'):
 s=p.read_text(errors='replace')
 for marker in ['tokenLogin=function','getGoHistoryRecord=function','getFairnessData=function']:
  i=s.find(marker)
  if i>=0:print(p.name,marker,s[i:i+700])
