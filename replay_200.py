#!/usr/bin/env python3
"""Start Pappu offline replay from locally editable math or original captured outcomes."""
import argparse,os,socket,subprocess,sys,time,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent;HERE=ROOT/'games/200'
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',choices=['math','wire'],default='math')
    ap.add_argument('--math-dir');ap.add_argument('--rounds',default='');ap.add_argument('--port',type=int,default=8201)
    ap.add_argument('--balance',type=int,default=3000000);ap.add_argument('--no-browser',action='store_true');args=ap.parse_args()
    with socket.socket()as probe:
        if probe.connect_ex(('127.0.0.1',args.port))==0:raise SystemExit('Port already in use; close the previous Pappu replay first.')
    env=dict(os.environ,REPLAY_PORT=str(args.port),REPLAY_SOURCE=args.source,REPLAY_BALANCE=str(args.balance),SELECT_ROUNDS=args.rounds)
    if args.math_dir:env['MATH_DIR']=str(Path(args.math_dir).resolve())
    (HERE/'replay').mkdir(exist_ok=True)
    with (HERE/'replay/server.log').open('w')as log:
        server=subprocess.Popen([sys.executable,'-B','-u',str(HERE/'replay_server.py')],env=env,stdout=log,stderr=subprocess.STDOUT)
        browser=None
        try:
            for _ in range(60):
                if server.poll()is not None:raise RuntimeError('Replay server failed; see games/200/replay/server.log')
                try:
                    with urllib.request.urlopen('http://127.0.0.1:%d/__replay_status'%args.port,timeout=1)as r:
                        if r.status==200:break
                except OSError:time.sleep(.1)
            else:raise RuntimeError('Replay readiness timeout')
            print('Pappu local replay ready: port=%d source=%s; no real account/wallet used'%(args.port,args.source),flush=True)
            if args.no_browser:server.wait()
            else:
                browser=subprocess.Popen([sys.executable,'-B',str(HERE/'open_replay.py')],env=env);browser.wait()
        except KeyboardInterrupt:pass
        finally:
            for p in(browser,server):
                if p is not None and p.poll()is None:
                    p.terminate()
                    try:p.wait(timeout=5)
                    except subprocess.TimeoutExpired:p.kill()
