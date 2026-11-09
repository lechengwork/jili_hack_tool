#!/usr/bin/env python3
"""Launch the game-specific Lucky Jaguar 500 replay."""
import argparse,json,os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent;GAME=ROOT/'games/664'
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',choices=['math','wire'],default='math');ap.add_argument('--port',type=int,default=8665);ap.add_argument('--rounds',default='');ap.add_argument('--bonus-first',action='store_true');ap.add_argument('--math-dir');ap.add_argument('--no-watch-math',action='store_true');ap.add_argument('--no-browser',action='store_true');args=ap.parse_args()
 if not(GAME/'replay_samples.json').exists():subprocess.run([sys.executable,'-B',str(GAME/'build_replay_samples.py')],check=True)
 with socket.socket()as sock:
  if sock.connect_ex(('127.0.0.1',args.port))==0:raise SystemExit('Replay port occupied. Use --port or stop its existing replay.')
 rounds=args.rounds
 if args.bonus_first and not rounds:rounds=','.join(json.loads((GAME/'coverage.json').read_text())[k]['bonus_spins'][0]for k in ['normal','extra_1_5','extra_8','purchase'])
 env=dict(os.environ,REPLAY_PORT=str(args.port),REPLAY_SOURCE=args.source,SELECT_ROUNDS=rounds,WATCH_MATH='0'if args.no_watch_math else '1')
 if args.math_dir:env['MATH_DIR']=str(Path(args.math_dir).resolve())
 server=subprocess.Popen([sys.executable,'-B','-u',str(GAME/'replay_server.py')],env=env);browser=None
 try:
  for _ in range(100):
   if server.poll()is not None:raise RuntimeError('Replay failed to start')
   try:
    with urllib.request.urlopen('http://127.0.0.1:%d/__replay_status'%args.port,timeout=1)as response:json.load(response)
    break
   except OSError:time.sleep(.1)
  else:raise RuntimeError('Replay startup timed out')
  if args.no_browser:server.wait()
  else:browser=subprocess.Popen([sys.executable,'-B','-u',str(GAME/'open_replay.py')],env=env);browser.wait()
 except KeyboardInterrupt:pass
 finally:
  for p in [browser,server]:
   if p and p.poll()is None:
    p.terminate()
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:p.kill()
