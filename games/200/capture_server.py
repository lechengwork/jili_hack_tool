#!/usr/bin/env python3
"""Pappu passive WebSocket collector; only original-codec validated results publish."""
import io
import json
import os
from pathlib import Path
import ssl
import sys
import threading
from datetime import datetime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
os.umask(0o077)
SESSION = HERE / 'webcap' / datetime.now().strftime('%Y%m%d-%H%M%S')
SESSION.mkdir(parents=True, exist_ok=False)
account = json.loads((HERE/'capture_config.local.json').read_text())['capture_account']
(SESSION/'source.json').write_text(json.dumps(account))
(SESSION/'launch.local.json').write_text((HERE/'login_session.local.json').read_text())
os.environ.update(HOST='127.0.0.1', PORT='8200', TLS='1', VERBOSE='0',
                  STATIC=str(HERE/'static'), DOC_INDEX='/pappu/index.html',
                  ORIGIN='https://uat-wbgame.jlfafafa3.com', OUT=str(SESSION/'frames.jsonl'))
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'routex'))
import ws_capture_server as base
from round_export import Collector

base._BF_CTX = ssl.create_default_context()
_collector = Collector(HERE, SESSION, account['currency'])

def process(rec):
    with lock:
        status = _collector.feed(rec)
        if status:
            print(status, flush=True)

lock = threading.Lock()

class Handler(base.H):
    def _send(self, code, body=b'', ctype='text/plain', extra=None):
        if ctype.startswith('text/') or 'javascript' in ctype or 'json' in ctype:
            ctype += '; charset=utf-8'
        return super()._send(code,body,ctype,extra)

    def do_POST(self):
        if self.path.split('?',1)[0] != '/__wscap':return super().do_POST()
        raw = self.rfile.read(int(self.headers.get('Content-Length','0')))
        stream=self.rfile
        try:
            self.rfile=io.BytesIO(raw)
            super().do_POST()  # Raw frame is durable before any game-specific decode.
        finally:
            self.rfile=stream
        try:process(json.loads(raw))
        except Exception as error:
            _collector.log('decode_errors.jsonl', {'error':str(error),'raw_record_hex':raw.hex()})
            print('[200 decode] '+str(error),flush=True)

if __name__=='__main__':
    base.H=Handler
    (HERE/'current_session.txt').write_text(str(SESSION)+'\n')
    print('[200 capture] '+str(SESSION),flush=True)
    base.main()
