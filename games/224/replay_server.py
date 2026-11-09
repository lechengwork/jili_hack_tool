#!/usr/bin/env python3
"""Local Go Rush replay: captured rate paths, original codec, local-only wallet."""
import base64,hashlib,importlib.util,json,os,struct,sys,threading,time
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit,unquote
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
sys.path.insert(0,str(HERE.parent.parent/'routex'))
from asset_archives import materialize as _materialize_archives
_materialize_archives(HERE/'static')
sys.path.insert(0,str(HERE))
from math_adapter import wire_to_math,math_to_wire
from watch_live_math import command
from history_replay import HistoryReplay
SESSION=Path(os.environ.get('REPLAY_SESSION') or HERE/'replay_data')
history=HistoryReplay(SESSION)
# Keep the previously verified native leaderboard snapshots with the complete history capture.
RANK_SOURCE=SESSION/'rank_frames.jsonl' if (SESSION/'rank_frames.jsonl').exists() else HERE/'webcap/20261109-100032/frames.jsonl'
PORT=int(os.environ.get('REPLAY_PORT','8225'))
os.environ['SESSION']=str(SESSION/'frames.jsonl')
spec=importlib.util.spec_from_file_location('ws_transport',ROOT/'dist124/ws_replay_server.py');transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
rows=[json.loads(l) for l in (SESSION/'frames.jsonl').read_text().splitlines()]
for r in rows:r['cmd']=command(r['hex'])
app=[r for r in rows if (r['dir']=='SEND' and r['cmd'] in (10,11)) or (r['dir']=='RECV' and r['cmd'] in (10,11,12,13,14,16))]
decoded=wire_to_math(app)
for r,d in zip(app,decoded):r['decoded']=d
bycmd={}
for r in rows:
 if r['dir']=='RECV':bycmd.setdefault(r['cmd'],[]).append(r)
rank_rows=[json.loads(l) for l in RANK_SOURCE.read_text().splitlines()]
rank_snapshots=[r for r in rank_rows if r['dir']=='RECV' and command(r['hex'])==14]
for r,d in zip(rank_snapshots,wire_to_math(rank_snapshots)):r['decoded']=d
for snapshot in rank_snapshots:
 if math_to_wire(snapshot['decoded']).hex()!=snapshot['hex']:
  raise ValueError('Original rank snapshot full-frame roundtrip failed')
print('[224 replay] verified rank snapshots=%d'%len(rank_snapshots),flush=True)
rounds=[];current=None
for r in rows:
 if r['dir']=='SEND' and r['cmd']==10:
  current={'request':r,'events':[]};rounds.append(current)
 elif current is not None and r['dir']=='RECV' and r['cmd'] in (10,11,12,13):
  current['events'].append(r)
  if r['cmd']==13:current=None
rounds=[r for r in rounds if r['events'] and r['events'][-1]['cmd']==13]
shim=(HERE/'replay_transport.js').read_bytes()

# Generic protobuf wrapper parsing used only for the captured initialization.
def rv(b,p):
 v=0;s=0
 while True:
  x=b[p];p+=1;v|=(x&127)<<s
  if not x&128:return v,p
  s+=7

def fields(b):
 out={};p=0
 while p<len(b):
  t,p=rv(b,p);n,w=t>>3,t&7
  if w==0:v,p=rv(b,p)
  elif w==2:
   size,p=rv(b,p);v=b[p:p+size];p+=size
  else:
   size=8 if w==1 else 4;v=b[p:p+size];p+=size
  out[n]=(w,v)
 return out
welcome=bytes.fromhex(bycmd[0][0]['hex']);login=fields(fields(welcome)[2][1]);user=fields(login[3][1]);uid=user[1][1];wallet=fields(user[4][1]);initial_coin=struct.unpack('<d',wallet[2][1])[0]
sso=json.loads((ROOT/'dist124/mock/sso.json').read_text())
sso.update(homeUrl='',token='local-replay-only',country='ID',clientApiParam={},agentId='local-replay-agent')
sso['response']={'error':0,'message':'OK','time':int(time.time())}
sso['profile'].update(id=str(uid),aid=uid,account='local-replay-224',nickname='Replay224',newNickname='Replay224',coin=initial_coin,meta={'agentAccount':'local-replay-agent','agentId':'local-replay-agent'},agentId='local-replay-agent',liveId='',liveSourceUrls={},prefix='replay')
sso['profile']['platform']='web'
# Original Go Rush SSO uses sub-agent code 2; it selects the history entrance API.
sso['profile']['subAgentCode']=2
state={'connections':0,'rounds_started':0,'rounds_finished':0,'assets':0,'missing':[],'rank_requests':0,'last_rank_snapshot':None}

class Cursor:
 def __init__(self,handler):
  self.h=handler;self.lock=threading.Lock();self.stop=threading.Event();self.active=False;self.index=0;self.balance=initial_coin;self.rate=1.;self.bets=[];self.paid=set();self.total=0.;self.round=None;self.rank_pos=0
 def send(self,b):
  with self.lock:transport.ws_send(self.h.wfile,b)
 def edit(self,template,data):
  value=dict(template['decoded']);value['data']=data;return math_to_wire(value)
 def cashout(self,area,rate):
  with self.round_lock:
   if not self.active or area in self.paid or not 0<=area<len(self.bets) or self.bets[area].get('bet',0)<=0:return
   win=self.bets[area]['bet']*rate;self.paid.add(area);self.total+=win;self.balance+=win
   template=bycmd[11][0];data={'myRate':rate,'win':win,'betType':area,'coin':self.balance}
   self.send(self.edit(template,data));print('[224 replay] local cashout area=%d rate=%.2f'%(area,rate),flush=True)
 def send_rank(self):
  if not rank_snapshots:
   self.send(bytes.fromhex('080e'));return
  index=min(self.rank_pos,len(rank_snapshots)-1);snapshot=rank_snapshots[index]
  self.send(bytes.fromhex(snapshot['hex']))
  self.rank_pos=min(index+1,len(rank_snapshots)-1)
  state['rank_requests']+=1;state['last_rank_snapshot']={'index':index+1,'capture_seq':snapshot['seq']}
  print('[224 replay rank] snapshot=%d/%d capture_seq=%s'%(index+1,len(rank_snapshots),snapshot['seq']),flush=True)
 def start(self,req):
  if self.active:return
  self.round_lock=threading.RLock();self.round=rounds[self.index%len(rounds)];self.index+=1
  self.bets=req['data'].get('betData',[]);self.balance-=sum(x.get('bet',0)for x in self.bets);self.rate=1.;self.total=0.;self.paid=set();self.active=True
  state['rounds_started']+=1
  print('[224 replay] trajectory %d/%d; local bets=%s'%((self.index-1)%len(rounds)+1,len(rounds),[x.get('bet',0)for x in self.bets]),flush=True)
  threading.Thread(target=self.play,daemon=True).start()
 def play(self):
  try:
   events=self.round['events'];start=events[0]['ts'];clock=time.monotonic()
   for r in events:
    if r['cmd']==11:continue # Captured cashouts are replaced by this replay's local inputs.
    delay=(r['ts']-start)/1000-(time.monotonic()-clock)
    if self.stop.wait(max(0,delay)):return
    if r['cmd']==12:
     self.rate=r['decoded']['data']['rate'];self.send(bytes.fromhex(r['hex']))
     for i,b in enumerate(self.bets):
      auto=b.get('autoRate',0)
      if auto>=1 and self.rate>=auto:self.cashout(i,auto)
    elif r['cmd']==13:
     with self.round_lock:
      self.active=False;d=dict(r['decoded']['data']);d.update(totalWin=self.total,coin=self.balance);self.send(self.edit(r,d));state['rounds_finished']+=1
    else:self.send(bytes.fromhex(r['hex']))
  except (OSError,ConnectionError):self.stop.set()
  except Exception as e:print('[224 replay error] '+str(e),flush=True);self.stop.set()
 def receive(self,b):
  c=command(b.hex())
  if c!=50:print('[224 replay] client command %d'%c,flush=True)
  if c==10:self.start(wire_to_math([{'hex':b.hex(),'dir':'SEND'}])[0]);return
  if c==11:
   q=wire_to_math([{'hex':b.hex(),'dir':'SEND'}])[0];self.cashout(q['data'].get('betType',0),self.rate);return
  if c==14:self.send(bytes.fromhex(bycmd[16][(self.index)%len(bycmd[16])]['hex']));return
  if c==12:self.send_rank();return # Captured snapshots in order, then retain the last snapshot.
  if c==50:self.send(bytes.fromhex('0832'));return
  response={111:112,144:146}.get(c,c)
  if response in bycmd and c!=0:self.send(bytes.fromhex(bycmd[response][0]['hex']))

class Handler(BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1'
 def log_message(self,*a):pass
 def send(self,code,data=b'',ctype='application/json'):
  self.send_response(code);self.send_header('Content-Length',str(len(data)));self.send_header('Content-Type',ctype);self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Headers','*');self.end_headers()
  try:self.wfile.write(data)
  except OSError:pass
 def do_OPTIONS(self):self.send(204)
 def api(self,path):
  captured=history.response(self.path,self.command)
  if captured:
   print('[224 history] %s %s -> %d'%(self.command,path,captured[0]),flush=True)
   self.send(*captured);return True
  if 'sso-login' in path:self.send(200,json.dumps(sso).encode());print('[224 replay] local SSO',flush=True);return True
  if path=='/time/1/current':return self.send(200,json.dumps({'time':int(time.time()*1000),'timestamp':int(time.time()*1000)}).encode()) or True
  if path=='/__replay_status':self.send(200,json.dumps({**state,'source_session':SESSION.name,'trajectories':len(rounds),'rank_snapshots':len(rank_snapshots),'rank_mode':'captured snapshots in order, last retained; local mock wins do not alter rankings','network':'local-only','wallet':'simulated; captured crash paths'}).encode());return True
  if path.startswith(('/webservice/','/rankingservice/','/subagentservice/','/vipservice/','/favoriteservice/','/historyservice/','/eventservice/','/tournamentservice/')):self.send(200,b'{}');return True
  return False
 def do_POST(self):
  n=int(self.headers.get('Content-Length','0'));body=self.rfile.read(n)
  if urlsplit(self.path).path=='/__replay_diagnostic':
   print('[224 frontend] '+body.decode(errors='replace')[:1600],flush=True);return self.send(200,b'{}')
  path=urlsplit(self.path).path
  if not self.api(path):print('[224 replay] unhandled POST '+path,flush=True);self.send(200,b'{}')
 def do_GET(self):
  path=urlsplit(self.path).path
  if self.headers.get('Upgrade','').lower()=='websocket':return self.ws(path)
  if self.api(path):return
  asset=history.asset(path,shim)
  if asset:
   self.send(200,*asset);return
  rel=unquote(path).lstrip('/') or 'aviator/index.html'
  if rel.endswith('/'):rel+='index.html'
  target=(HERE/'static'/rel).resolve()
  if HERE/'static' not in target.parents or not target.is_file():
   if path not in state['missing']:state['missing'].append(path);print('[224 replay 404] '+path,flush=True)
   return self.send(404,b'not found','text/plain')
  data=target.read_bytes()
  if target.name=='bundle.8ab85.js':data=data.replace(b'function C$j(Y0S,j5P,O6J,T5X){',b"function C$j(Y0S,j5P,O6J,T5X){if(j5P===undefined)fetch('/__replay_diagnostic',{method:'POST',body:JSON.stringify({missingField:Y0S})}).catch(()=>{});")
  ctype=transport.CTYPE.get(target.suffix,'application/octet-stream')
  if target.name.startswith('system.bundle') and target.suffix=='.js':data=shim+b'\n;'+data
  if target.suffix=='.html':data=data.replace(b'</body>','<div style="position:fixed;right:6px;top:4px;z-index:2147483647;background:#263346;color:white;padding:4px;font:12px sans-serif">Go Rush 本地重播 · 模擬餘額</div></body>'.encode())
  if ctype.startswith('text/') or 'javascript' in ctype or 'json' in ctype:ctype+='; charset=utf-8'
  state['assets']+=1;self.send(200,data,ctype)
 def ws(self,path):
  key=self.headers.get('Sec-WebSocket-Key','');accept=base64.b64encode(hashlib.sha1((key+transport.WS_GUID).encode()).digest()).decode()
  self.send_response(101);self.send_header('Upgrade','websocket');self.send_header('Connection','Upgrade');self.send_header('Sec-WebSocket-Accept',accept);self.end_headers()
  state['connections']+=1;cur=Cursor(self);print('[224 replay] WS connected '+path,flush=True)
  try:
   cur.send(welcome)
   while True:
    f=transport.ws_recv(self.rfile)
    if f is None or f[0]==8:break
    op,b=f
    if op==9:cur.send(b'');continue
    if op==2:cur.receive(b)
  except (OSError,ConnectionError):pass
  except Exception as e:print('[224 replay WS error] '+str(e),flush=True)
  finally:cur.stop.set();self.close_connection=True
if __name__=='__main__':
 (HERE/'replay').mkdir(exist_ok=True)
 (HERE/'replay/server.pid').write_text(str(os.getpid())+'\n')
 print('[224 replay] http://127.0.0.1:%d; %d captured trajectories; no upstream network'%(PORT,len(rounds)),flush=True)
 ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
