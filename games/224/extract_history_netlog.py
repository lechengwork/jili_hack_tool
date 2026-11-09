#!/usr/bin/env python3
"""Extract original HTTP entity bytes from dedicated private Chrome NetLog."""
import json,base64,hashlib
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
HERE=Path(__file__).resolve().parent
s=Path((HERE/'current_session.txt').read_text().strip())
types=json.loads((s/'netlog_event_types.local.json').read_text()); req={}
for line in (s/'netlog.json').open():
 try:e=json.loads(line.rstrip().rstrip(','))
 except ValueError:continue
 sid=e.get('source',{}).get('id');p=e.get('params',{});n=types.get(str(e.get('type')),'')
 if p.get('url') and n=='URL_REQUEST_START_JOB':req[sid]={'url':p['url'],'method':p.get('method'),'events':[]}
 if sid in req and ('BYTES_READ' in n or 'READ_RESPONSE_HEADERS' in n):req[sid]['events'].append({'name':n,'params':p})
private=s/'history_netlog';private.mkdir(exist_ok=True);manifest=[]
for sid,r in req.items():
 u=urlsplit(r['url'])
 if r['method']=='OPTIONS' or not any(x in u.netloc for x in ('history','web-cdn','language-api')):continue
 body=b''.join(base64.b64decode(e['params']['bytes']) for e in r['events'] if e['name']=='URL_REQUEST_JOB_FILTERED_BYTES_READ' and 'bytes'in e['params'])
 if not body:continue
 headers=next((e['params']['headers']for e in r['events']if e['name']=='HTTP_TRANSACTION_READ_RESPONSE_HEADERS'),[])
 file=str(sid)+'.body';(private/file).write_bytes(body)
 row={'source_id':sid,'url':r['url'],'method':r['method'],'headers':headers,'body':file,'sha256':hashlib.sha256(body).hexdigest(),'size':len(body)};manifest.append(row)
 if u.netloc=='uat-history.jlfafafa3.com':
  rel=u.path.lstrip('/')
  if rel.endswith('/'):rel+='index.html'
  target=HERE/'history/static'/rel
  if target.suffix in ('.js','.woff2','.css','.png','.svg','.html'):
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
(private/'manifest.local.json').write_text(json.dumps(manifest,indent=2))
print('Extracted',len(manifest),'HTTP entities; private manifest saved')
for r in manifest:
 u=urlsplit(r['url'])
 if 'history-api' in u.netloc and r['method']!='OPTIONS':
  data=json.loads((private/r['body']).read_bytes());print(u.path,'query keys',list(parse_qs(u.query)),'response keys',list(data),'Code',data.get('Code'))
