"""Original history UI with captured HTTP entities; no production credentials served."""
import base64,json,time,re
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
HERE=Path(__file__).resolve().parent
class HistoryReplay:
 def __init__(self,session):
  self.session=session;public=session/'history/manifest.json';self.root=public.parent if public.exists() else session/'history_netlog';self.rows=json.loads((public if public.exists() else self.root/'manifest.local.json').read_text());self.api={};self.assets={};self.fairness={};self.requests=[]
  for row in self.rows:
   u=urlsplit(row['url']);body=(self.root/row['body']).read_bytes()
   if row.get('is_history_api', 'history-api.' in u.netloc):
    if u.path=='/v2/token':continue
    if u.path=='/v2/fairness/steps':self.fairness[self.key(parse_qs(u.query))]=body
    else:self.api[u.path]=body
   else:self.assets[u.path]=body
  self.list_path='/v2/history/aviator/get-history-record'
 @staticmethod
 def key(query):return tuple((k,tuple(query.get(k,[]))) for k in ('GameId','ServerSeed','ClientSeed1','ClientSeed2','ClientSeed3'))
 def response(self,url,method):
  u=urlsplit(url);path=u.path
  if not path.startswith('/v2/'):return None
  self.requests.append(path)
  if path=='/v2/token':
   # Local unsigned mock JWT. Only the replay endpoint accepts it.
   claims={'AID':'1','APIID':'1778','AT':'local-replay-224','CNAME':'IDR','CNO':'7','CSYMBOL':'Rp','EXPONENT':'4','RATIO':'1000','RATE':'0.0021','UNIT':'1','aud':'GameHistory','sub':'1','exp':int(time.time())+86400,'iat':int(time.time())}
   enc=lambda d:base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip('=')
   token=enc({'alg':'none','typ':'JWT'})+'.'+enc(claims)+'.local-replay-only'
   return 200,json.dumps({'Code':0,'Message':'本地重播','Data':{'Token':token,'UserApiInfo':{'ApiId':1778,'Name':'Local replay','IconType':3,'Timezone':7,'IsPremoneyDisplay':True,'IsPostmoneyDisplay':True}}}).encode(),'application/json'
  if path=='/v2/fairness/steps':body=self.fairness.get(self.key(parse_qs(u.query)))
  else:body=self.api.get(path)
  if body is None:return 404,json.dumps({'Code':404,'Message':'此查詢尚無擷取資料','Data':None}).encode(),'application/json'
  if path==self.list_path:
   # A fixed captured page, never duplicate it when the original UI asks for a later page.
   q=parse_qs(u.query)
   if int(q.get('StartRowIndex',['0'])[0])>1:body=b'{"Code":0,"Message":"captured page exhausted","Data":[]}'
  return 200,body,'application/json'
 def asset(self,path,shim):
  if path.startswith('/zh-CN/ingame'):path='/zh-CN/ingame/'
  body=self.assets.get(path)
  if body is None:
   target=(HERE/'history/static'/path.lstrip('/')).resolve()
   if target.is_file() and HERE/'history/static' in target.parents:body=target.read_bytes()
  if body is None:return None
  if path.endswith('/') or path.endswith('.html'):
   # Install offline routing before the original Nuxt scripts and suppress telemetry.
   body=re.sub(rb'<script[^>]*data-hid="gtm-script".*?</script>',b'',body,flags=re.S)
   body=re.sub(rb'<noscript.*?</noscript>',b'',body,flags=re.S)
   body=body.replace(b'<head>',b'<head><script>'+shim+b'</script>')
   body=body.replace(b'</body>','<div style="position:fixed;right:6px;bottom:4px;z-index:2147483647;background:#263346;color:white;padding:3px;font:12px sans-serif">Go Rush 擷取歷史 · 3 局</div></body>'.encode())
   return body,'text/html; charset=utf-8'
  import mimetypes
  return body,mimetypes.guess_type(path)[0] or 'application/octet-stream'
