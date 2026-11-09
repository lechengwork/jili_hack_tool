"""Backfill current verified decoded log without interrupting the live browser."""
import argparse,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'routex'))
from live_math import export_spin,format_status
from math_adapter import wire_to_math,math_to_wire
ap=argparse.ArgumentParser();ap.add_argument('--once',action='store_true');a=ap.parse_args()
session=Path((HERE/'current_session.txt').read_text().strip());seen=set()
try:
 while True:
  p=session/'exchanges_ordered.jsonl'
  for line in p.read_bytes().splitlines(keepends=True) if p.exists() else []:
   if not line.endswith(b'\n'):continue
   d=json.loads(line);key=d['idx']
   if key in seen:continue
   seen.add(key);report=export_spin(d,HERE,session,wire_to_math,math_to_wire)
   if report:print(format_status(report),flush=True)
  if a.once:break
  time.sleep(1)
except KeyboardInterrupt:pass
