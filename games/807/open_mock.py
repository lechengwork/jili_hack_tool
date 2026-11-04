#!/usr/bin/env python3
"""Open the local 807 replay. All browser DNS is routed to the local mock."""
from pathlib import Path
import json
import os
import ssl
import subprocess
import tempfile
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent
from runtime_support import chrome_path
port = int(os.environ.get('MOCK_PORT', '8808'))
query = {
    'ssoKey':'local-mock-token', 'lang':'zh-CN', 'apiId':'1778',
    'be':'moc.2afafaflj.ipabewbw-tau', 'domain_gs':'1afafaflj',
    'domain_platform':'moc.3afafaflj.mroftalp-tolsbw-tau', 'gameID':'807',
    'gs':'moc.1afafaflj.df-tolsbw-tau', 'iu':'true', 'legalLang':'true', 'skin':'0',
}
url = 'https://uat-wbgame.jlfafafa3.com:%s/fg1000/?' % port + urllib.parse.urlencode(query)
with urllib.request.urlopen('https://127.0.0.1:%s/fg1000/src/polyfills.bundle.5adbf.js' % port,
                            context=ssl._create_unverified_context(), timeout=5) as r:
    assert b'installed C2 compile-hook' in r.read(), 'Mock crypto shim is missing'
p = subprocess.Popen([
    chrome_path(),
    '--user-data-dir=' + tempfile.mkdtemp(prefix='jili-807-mock-'),
    '--host-resolver-rules=MAP * 127.0.0.1:%s' % port,
    '--ignore-certificate-errors', '--disable-quic', '--no-first-run',
    '--disable-background-networking', '--disable-component-update',
    '--no-default-browser-check', '--disable-features=ChromeWhatsNewUI,DnsOverHttps', url,
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
(HERE / 'mock_runtime.json').write_text(json.dumps({'chrome_pid':p.pid,'url':url}))
print('[807 mock] Chrome pid=%s; all hosts map to localhost:%s' % (p.pid, port), flush=True)
try:
    p.wait()
except KeyboardInterrupt:
    p.terminate()
    p.wait(timeout=10)
