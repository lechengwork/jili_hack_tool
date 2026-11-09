#!/usr/bin/env python3
"""Open the local replay; all browser DNS maps to the loopback server."""
import json,os,subprocess
from pathlib import Path
from urllib.parse import urlencode
HERE=Path(__file__).resolve().parent
port=int(os.environ.get('REPLAY_PORT','8225'))
query={'ssoKey':'local-replay-224','lang':'zh-CN','apiId':'1778','be':'moc.2afafaflj.ipabewbw-tau','domain_gs':'1afafaflj','domain_platform':'moc.3afafaflj.mroftalp-tolsbw-tau','gameID':'224','gs':'1afafaflj','iu':'true','legalLang':'true','skin':'0'}
url='http://uat-wbgame.jlfafafa3.com:%d/aviator/index.html?'%port+urlencode(query)
profile=HERE/'replay/chrome-profile';profile.mkdir(parents=True,exist_ok=True)
p=subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--user-data-dir='+str(profile),'--host-resolver-rules=MAP * 127.0.0.1:%d'%port,'--disable-quic','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--disable-features=ChromeWhatsNewUI,DnsOverHttps',url],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
(HERE/'replay/chrome.pid').write_text(str(p.pid)+'\n')
print('Go Rush local replay Chrome pid=%d; real accounts and wallets are unused'%p.pid,flush=True)
p.wait()
