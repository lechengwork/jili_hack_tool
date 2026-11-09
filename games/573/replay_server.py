#!/usr/bin/env python3
"""573 offline encrypted wire replay. No capture key/login config/upstream reads."""
import copy,json,os,sys,struct,threading,time,re
from pathlib import Path
from urllib.parse import urlsplit,unquote
from http.server import ThreadingHTTPServer
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
PORT=int(os.environ.get('REPLAY_PORT','8574'));SOURCE=os.environ.get('REPLAY_SOURCE','math')
TEXTURE_FORMAT=os.environ.get('REPLAY_TEXTURE_FORMAT','auto')
if TEXTURE_FORMAT not in ('auto','webp','png'):raise ValueError('Unsupported texture preference')
os.environ.update(STATIC=str(HERE/'static'),HOST='127.0.0.1',PORT=str(PORT),TLS='0',GAME_PATH='/rc2/',CAPTURE='0',LIVE_DECODE='0',INJECT_BUNDLE='1',ASSET_FALLBACK='0',REPLAY=str(HERE/'replay/unused.jsonl'),RESPONSES=str(HERE/'replay/unused-responses.jsonl'),INIT_SEQ=str(HERE/'replay/unused-init.jsonl'),REPLAY_SPINS='',REPLAY_ROUNDS='',REPLAY_LOG='0',VERBOSE='0',HS_DELAY='0',SSO_DELAY='0',SHARED_HEX_PATH=str(HERE/'replay/mock_shared.hex'))
sys.path.insert(0,str(ROOT/'routex'));import server,fg5
sys.path.insert(0,str(HERE));from math_adapter import records,fields,field,varint,decode_message
from replay_pool import ReplayPool,action_key
ROWS=json.loads((HERE/'replay_samples.json').read_text());server.SAMPLES={}
for r in ROWS:server.SAMPLES.setdefault(r['type'],bytes.fromhex(r['raw_hex']))
server.SHARED_ROOT=server.STATIC_ROOT
server.origin_fetch_and_cache=lambda path:None
server.WASM_SHIM=(HERE/'replay_transport.js').read_text()+'\n'+(ROOT/'routex/err_probe_shim.js').read_text()+'\n'+(HERE/'replay_crypto.js').read_text()
POOL=ReplayPool(ROWS,SOURCE,os.environ.get('MATH_DIR'),os.environ.get('SELECT_ROUNDS',''),os.environ.get('WATCH_MATH','1')!='0',os.environ.get('BONUS_FIRST','0')=='1')
STATE={'source':SOURCE,'network':'local-only; no upstream fallback','spins':0,'unsupported':0,'missing':[],'frontend_errors':[],'recent_spins':[], 'texture_format':TEXTURE_FORMAT,'texture_policy_applied':False,'texture_requests':{}}
clients={};lock=threading.Lock()

def replace(buf,n,w,value):
 replacement=field(n,w,value);out=bytearray();found=False
 for number,wire,v,raw in records(buf):
  if number==n:
   if not found:out.extend(replacement);found=True
  else:out.extend(raw)
 if not found:out.extend(replacement)
 return bytes(out)

def pick(req):
 typ,action=req['seq'],req['action']
 with lock:
  client=clients.setdefault(bytes(req['client_pub']),{'indices':{},'balance':None,'last_rid':0})
  if typ==0:
   try:
    pools=POOL.refresh();key=action_key(action);pool=pools.get(key)
    if not pool:STATE['unsupported']+=1;return 0,b'',400,'unsupported-bet-or-mode'
    i=client['indices'].get(key,0);raw=pool[i%len(pool)];client['indices'][key]=i+1
    f=fields(raw);source_rid=f[20][1];rid=source_rid
    if rid<=client['last_rid']:rid=(client['last_rid']//1000+1)*1000+573;raw=replace(raw,20,0,varint(rid))
    client['last_rid']=rid;client['balance']=f[6][1]
    data=decode_message(f[1][1]);record={'source_round':str(source_rid),'served_round':str(rid),'Extra':data['Extra'],'GetBonus':any(r['GetBonus'] for r in data['RoundQueue']),'TotalWin':data['TotalWin'],'stage_count':len(data['RoundQueue'])}
    STATE['spins']+=1;STATE['recent_spins']=(STATE['recent_spins']+[record])[-20:]
    print('[573 replay spin] '+json.dumps(record),flush=True);return 0,raw,0,'captured-result'
   except Exception as e:
    STATE['frontend_errors'].append('math/input: '+str(e));print('[573 replay error] '+str(e),flush=True);return 0,b'',400,'invalid-math-or-input'
  if typ==2 and client['balance']is not None:
   template=server.SAMPLES[2];core=replace(fields(template)[1][1],2,1,client['balance']);return 2,replace(template,1,2,core),0,'captured-balance'
  matches=[r for r in ROWS if r['type']==typ and r['action_hex']==action.hex()]
  if not matches:matches=[r for r in ROWS if r['type']==typ]
  if not matches:return typ,b'',400,'unsupported-type'
  row=matches[0];return typ,bytes.fromhex(row['raw_hex']),row['ret'],'captured-type'
server.pick_response=pick
server.SSO_JSON=copy.deepcopy(server.SSO_JSON)
server.SSO_JSON.update(token='0'*40,country='Indonesia',subDivision='',homeUrl='',clientApiParam={})
server.SSO_JSON['profile'].update(id='573',aid=573,siteId=0,account='local-replay-573',nickname='Replay573',newNickname='Replay573',coin=0,meta={'agentAccount':'local-replay-only'},platform='web',liveId='',liveSourceUrls={})

class Handler(server.Handler):
 def _send(self,code,body=b'',ctype='application/octet-stream',extra=None):
  if TEXTURE_FORMAT!='auto' and 'javascript' in ctype and b'SUPPORT_TEXTURE_FORMATS:[' in body:
   formats=['.webp','.jpg','.jpeg','.bmp','.png'] if TEXTURE_FORMAT=='webp' else ['.png','.jpg','.jpeg','.bmp','.webp']
   body,n=re.subn(rb'SUPPORT_TEXTURE_FORMATS:\[[^\]]+\]',b'SUPPORT_TEXTURE_FORMATS:'+json.dumps(formats,separators=(',',':')).encode(),body)
   if n!=1:raise ValueError('Unexpected Cocos texture policy; original files untouched')
   STATE['texture_policy_applied']=True
  extension=Path(urlsplit(self.path).path).suffix.lower()
  if code==200 and extension in ('.astc','.webp','.png','.jpg','.jpeg'):
   STATE['texture_requests'][extension]=STATE['texture_requests'].get(extension,0)+1
  if code==404:
   path=urlsplit(self.path).path
   if path not in STATE['missing']:STATE['missing'].append(path);print('[573 replay missing] '+path,flush=True)
  if ctype.startswith('text/')or'javascript'in ctype or'json'in ctype:
   if 'charset='not in ctype:ctype+='; charset=utf-8'
  if 'text/html'in ctype and body:
   badge='<div style="position:fixed;top:0;right:0;z-index:2147483647;background:#243545;color:#fff;font:12px sans-serif;padding:4px;pointer-events:none">573 本地重播 · 原局結果與餘額</div>'.encode()
   body=body.replace(b'</body>',badge+b'</body>')
  try:super()._send(code,body,ctype,extra)
  except (BrokenPipeError,ConnectionResetError):pass
 def status(self):
  self._send(200,json.dumps({**STATE,'pool_count':len(POOL.pools),'sample_count':sum(map(len,POOL.pools.values()))}).encode(),'application/json')
 def auxiliary(self):
  path=urlsplit(self.path).path
  if path.startswith(('/vipservice/','/favoriteservice/','/rankingservice/','/subagentservice/','/promotionservice/','/longhu/','/smartnotice/','/eventservice/','/tournamentservice/')):
   self._send(200,b'','application/x-protobuf');return True
  return False
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/__replay_status':return self.status()
  if path=='/time/1/current':return self._send(200,json.dumps({'time':int(time.time()*1000),'timestamp':int(time.time()*1000)}).encode(),'application/json')
  if path=='/':self._send(302,b'','text/plain',{'Location':'/rc2/'});return
  if self.auxiliary():return
  super().do_GET()
 def do_POST(self):
  path=urlsplit(self.path).path
  if path=='/__replay_diagnostic':
   body=self._read_body();d=json.loads(body);print('[573 diagnostic] '+json.dumps(d),flush=True);return self._send(200,b'{}','application/json')
  if path=='/__err__':
   body=self._read_body();d=json.loads(body)
   if d.get('kind')!='alive':STATE['frontend_errors'].append(d);print('[573 frontend error] '+json.dumps(d),flush=True)
   return self._send(200,b'{}','application/json')
  if path.startswith(('/vipservice/','/favoriteservice/','/rankingservice/','/subagentservice/','/promotionservice/','/longhu/','/smartnotice/','/eventservice/','/tournamentservice/')):
   self._read_body();self.auxiliary();return
  super().do_POST()

if __name__=='__main__':
 (HERE/'replay').mkdir(exist_ok=True);(HERE/('replay/server-%d.pid'%PORT)).write_text(str(os.getpid())+'\n')
 ThreadingHTTPServer.daemon_threads=True;ThreadingHTTPServer.request_queue_size=128
 print('[573 replay] http://127.0.0.1:%d; source=%s; samples=%d; offline only'%(PORT,SOURCE,sum(map(len,POOL.pools.values()))),flush=True)
 ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
