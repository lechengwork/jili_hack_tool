"""Export minimal application-only replay fixtures; never auth headers or netlogs."""
import hashlib,json,sys
from pathlib import Path
from urllib.parse import urlsplit,parse_qsl,urlencode
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));from watch_live_math import command

def frames(path):
 result=[]
 for line in path.read_text().splitlines():
  r=json.loads(line)
  if not r.get('hex'):continue
  c=command(r['hex'])
  if r['dir']=='SEND' and c==0:
   # Preserve initialization timing without exporting the authenticated login request.
   result.append({'kind':'ws_msg','dir':'SEND','hex':'0800','synthetic_login_boundary':True})
   continue
  if(r['dir']=='SEND'and c in(10,11))or(r['dir']=='RECV'and c in(0,4,10,11,12,13,14,16)):
   result.append({'kind':'ws_msg','dir':r['dir'],'hex':r['hex']})
 return result

def build():
 source=Path(json.loads((HERE/'replay_source.local.json').read_text())['session']);rank=HERE/'webcap/20261109-100032';out=HERE/'replay_data';out.mkdir(exist_ok=True)
 latest=frames(source/'frames.jsonl');prior=frames(rank/'frames.jsonl')
 for name,rows in [('frames.jsonl',latest),('rank_frames.jsonl',[r for r in prior if r['dir']=='RECV'and command(r['hex'])==14]),('proof_frames.jsonl',prior)]:
  (out/name).write_text(''.join(json.dumps(r)+'\n'for r in rows))
 manifest=[];dest=out/'history';(dest/'entities').mkdir(parents=True,exist_ok=True)
 for r in json.loads((source/'history_netlog/manifest.local.json').read_text()):
  u=urlsplit(r['url'])
  if u.path=='/v2/token':continue
  body=(source/'history_netlog'/r['body']).read_bytes();digest=hashlib.sha256(body).hexdigest()
  query=urlencode([(k,v)for k,v in parse_qsl(u.query)if k in ('GameId','ServerSeed','ClientSeed1','ClientSeed2','ClientSeed3')])
  relative=u.path+('?' + query if query else '')
  name='entities/'+digest+'.bin';(dest/name).write_bytes(body)
  manifest.append({'url':relative,'body':name,'sha256':digest,'is_history_api':'history-api.'in u.netloc})
 (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (out/'README.md').write_text('# Offline Go Rush fixtures\n\nOnly application messages required by replay and public UI/history response bodies. Login requests, tokens, cookies, headers, original URL origins and NetLogs are excluded. Fairness seeds belong to completed historical rounds and are included for verification. No capture directory is needed at runtime.\n')
 print(json.dumps({'application_frames':len(latest),'rank_frames':sum(r['dir']=='RECV'and command(r['hex'])==14 for r in prior),'history_entities':len(manifest),'transport_credentials_exported':False}))
if __name__=='__main__':build()
