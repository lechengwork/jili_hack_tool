#!/usr/bin/env python3
"""Go Rush independent passive collector; math remains gated on original codec validation."""
import io, json, os, ssl, sys, threading
from pathlib import Path
from datetime import datetime
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
os.umask(0o077)
SESSION=HERE/'webcap'/datetime.now().strftime('%Y%m%d-%H%M%S')
SESSION.mkdir(parents=True,exist_ok=False)
launch=json.loads((HERE/'login_session.local.json').read_text())
(SESSION/'launch.local.json').write_text(json.dumps(launch))
(SESSION/'source.json').write_text(json.dumps({'player_id':launch['player_id'],'currency':'IDR','currency_status':'account token confirmed; await runtime verification','provider_game_id':224}))
os.environ.update(HOST='127.0.0.1',PORT='8224',TLS='1',VERBOSE='1',STATIC=str(HERE/'static'),DOC_INDEX='/aviator/index.html',ORIGIN='https://uat-wbgame.jlfafafa3.com',OUT=str(SESSION/'frames.jsonl'))
sys.path.insert(0,str(ROOT))
import ws_capture_server as base
base._BF_CTX=ssl.create_default_context()
base.SHIM_SRC += '\n;' + (HERE/'capture_http_shim.js').read_text()
sys.path.insert(0,str(HERE))
from watch_live_math import Collector
collector=Collector(SESSION)
lock=threading.Lock()
class Handler(base.H):
    def _send(self,code,body=b'',ctype='text/plain',extra=None):
        if ctype.startswith('text/') or 'javascript' in ctype or 'json' in ctype:ctype+='; charset=utf-8'
        return super()._send(code,body,ctype,extra)
    def do_POST(self):
        if self.path.split('?',1)[0]=='/__httpcap':
            raw=self.rfile.read(int(self.headers.get('Content-Length','0')))
            try:
                rec=json.loads(raw)
                with lock:
                    with (SESSION/'http_exchanges.jsonl').open('a') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
                self._send(200,b'ok','text/plain')
            except Exception as error:
                with lock:
                    with (SESSION/'http_capture_errors.jsonl').open('a') as f:f.write(json.dumps({'error':str(error),'raw_hex':raw.hex()})+'\n')
                self._send(400,b'capture error','text/plain')
            return
        if self.path.split('?',1)[0]!='/__wscap':return super().do_POST()
        raw=self.rfile.read(int(self.headers.get('Content-Length','0')))
        stream=self.rfile
        try:
            self.rfile=io.BytesIO(raw)
            super().do_POST()
        finally:self.rfile=stream
        with lock:
            try:
                rec=json.loads(raw)
                from watch_live_math import command
                if rec.get('dir')=='RECV' and command(rec['hex'])==14:
                    from math_adapter import wire_to_math
                    try:
                        rank=wire_to_math([rec])[0]
                        collector.log('rank_verified.jsonl',rank)
                        print('[224 rank] original codec and full-frame roundtrip OK seq='+str(rec.get('seq')),flush=True)
                    except Exception as rank_error:
                        collector.log('rank_errors.jsonl',{'seq':rec.get('seq'),'error':str(rank_error),'raw_preserved':True})
                collector.feed(rec)
            except Exception as exc:
                collector.error(exc,collector.last_seq);collector.active=None;collector.pending=None
            collector.status()
if __name__=='__main__':
    base.H=Handler
    (HERE/'current_session.txt').write_text(str(SESSION)+'\n')
    (SESSION/'server.pid').write_text(str(os.getpid())+'\n')
    print('[224 capture] '+str(SESSION),flush=True)
    base.main()
