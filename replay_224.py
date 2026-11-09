#!/usr/bin/env python3
"""Start Go Rush local replay with its recorded trajectories and a simulated wallet."""
import argparse,os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HERE=ROOT/'games/224'
ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8225);ap.add_argument('--no-browser',action='store_true');args=ap.parse_args()
with socket.socket() as probe:
 if probe.connect_ex(('127.0.0.1',args.port))==0:raise SystemExit('Replay port is already in use; close the previous local replay first.')
env=dict(os.environ,REPLAY_PORT=str(args.port))
with (HERE/'replay.log').open('w') as log:
 server=subprocess.Popen([sys.executable,'-B','-u',str(HERE/'replay_server.py')],stdout=log,stderr=subprocess.STDOUT,env=env)
 browser=None
 try:
  for _ in range(60):
   if server.poll() is not None:raise RuntimeError('Replay server failed; see games/224/replay.log')
   try:
    with urllib.request.urlopen('http://127.0.0.1:%d/__replay_status'%args.port,timeout=1) as r:
     if r.status==200:break
   except OSError:time.sleep(.1)
  else:raise RuntimeError('Replay server readiness timeout')
  if args.no_browser:server.wait()
  else:
   browser=subprocess.Popen([sys.executable,'-B',str(HERE/'open_replay.py')],env=env);browser.wait()
 except KeyboardInterrupt:pass
 finally:
  for p in (browser,server):
   if p is not None and p.poll() is None:p.terminate()
