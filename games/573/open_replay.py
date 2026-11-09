#!/usr/bin/env python3
"""Launch a local-only 573 replay without live credentials or TLS bypass flags."""
import os,subprocess,signal
from pathlib import Path
from urllib.parse import urlencode
HERE=Path(__file__).resolve().parent
if __name__=='__main__':
 port=int(os.environ.get('REPLAY_PORT','8574'))
 query={'ssoKey':'local-replay-573','lang':'zh-CN','apiId':'1778','be':'moc.2afafaflj.ipabewbw-tau','domain_gs':'1afafaflj','domain_platform':'moc.3afafaflj.mroftalp-tolsbw-tau','gameID':'573','gs':'moc.1afafaflj.df-tolsbw-tau','iu':'true','legalLang':'true','skin':'0'}
 url='http://uat-wbgame.jlfafafa3.com:%d/rc2/?'%port+urlencode(query)
 profile=HERE/'replay/chrome-profile';profile.mkdir(parents=True,exist_ok=True)
 p=subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--user-data-dir='+str(profile),'--host-resolver-rules=MAP * 127.0.0.1:%d'%port,'--disable-quic','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--disable-features=ChromeWhatsNewUI,DnsOverHttps',url],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 (HERE/'replay/chrome.pid').write_text(str(p.pid)+'\n');print('573 local replay Chrome pid=%d'%p.pid,flush=True)
 def stop(signum,frame):raise KeyboardInterrupt
 signal.signal(signal.SIGTERM,stop)
 try:p.wait()
 except KeyboardInterrupt:
  if p.poll()is None:
   p.terminate()
   try:p.wait(timeout=5)
   except subprocess.TimeoutExpired:p.kill()
