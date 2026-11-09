#!/usr/bin/env python3
"""Capture the current account's history using the original history client's API contract."""
import json,os,time
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
BASE='https://uat-history-api.jlfafafa3.com'
pointer=HERE/'history_source.local.json'
SESSION=Path(json.loads(pointer.read_text())['session']) if pointer.exists() else Path((HERE/'current_session.txt').read_text().strip())
OUT=SESSION/'history_capture';OUT.mkdir(exist_ok=True);OUT.chmod(0o700)
os.umask(0o077)
http=requests.Session()
http.headers.update({'User-Agent':'Mozilla/5.0','Accept':'application/json','Accept-Encoding':'gzip, deflate'})

def fetch(method,path,*,body=None,params=None,form=None,origin=BASE):
    response=http.request(method,origin+path,json=body,data=form,params=params,timeout=30)
    number=len(list(OUT.glob('*.response.bin')))+1
    (OUT/('%03d.response.bin'%number)).write_bytes(response.content)
    meta={'method':method,'origin':origin,'path':path,'params':params,'request_body':body,'request_form':form,'status':response.status_code,'response_headers':dict(response.headers),'file':'%03d.response.bin'%number,'captured_at':time.strftime('%Y-%m-%dT%H:%M:%S%z')}
    with (OUT/'index.local.jsonl').open('a') as f:f.write(json.dumps(meta,ensure_ascii=False)+'\n')
    data=response.json()
    print(method,path,'HTTP',response.status_code,'Code',data.get('Code'),'Data type',type(data.get('Data')).__name__,flush=True)
    return data

def game_token():
    for line in (SESSION/'http_exchanges.jsonl').read_text().splitlines():
        row=json.loads(line)
        if '/sso-login.api' in row.get('url',''):
            sso=json.loads(bytes.fromhex(row['response']['hex']))
            return sso['token'],sso
    raise ValueError('No captured SSO response')

if __name__=='__main__':
    cached_sso=None
    if (OUT/'index.local.jsonl').exists():
        for line in (OUT/'index.local.jsonl').read_text().splitlines():
            entry=json.loads(line)
            if entry['path']=='/sso-login.api' and entry['status']==200:
                candidate=json.loads((OUT/entry['file']).read_bytes())
                if candidate.get('response',{}).get('error')==0:cached_sso=candidate
    if cached_sso is not None:
        sso=cached_sso;token=sso['token']
    elif (SESSION/'launch.local.json').exists():
        from urllib.parse import urlsplit,parse_qs
        launch=json.loads((SESSION/'launch.local.json').read_text());query=parse_qs(urlsplit(launch['game_url']).query)
        sso=fetch('POST','/sso-login.api',form={'key':query['ssoKey'][0],'lang':'zh-CN'},origin='https://uat-wbwebapi.jlfafafa2.com')
        if sso.get('response',{}).get('error')!=0:raise SystemExit('Fresh SSO failed; raw retained privately')
        token=sso['token']
    else:
        token,sso=game_token()
    result=fetch('POST','/v2/token/login',body={'Token':token,'GameNo':224,'IsJPEnabled':sso['profile'].get('isJPEnabled',0),'Lang':'zh-CN'})
    if result.get('Code')!=0:raise SystemExit('History token exchange not successful; raw response preserved privately')
    data=result['Data'];(OUT/'token_response.local.json').write_text(json.dumps(data,ensure_ascii=False)+'\n')
    print('history token Data keys',list(data)if isinstance(data,dict)else type(data).__name__)
