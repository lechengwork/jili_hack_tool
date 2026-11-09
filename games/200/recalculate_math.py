#!/usr/bin/env python3
"""Recalculate derived reference amounts after editing a Pappu math outcome."""
import argparse,json,os,tempfile
from pathlib import Path
from replay_pool import codec

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('file',type=Path)
    ap.add_argument('--winner',type=int,help='Also set ordinary-round pic to this type 1..12')
    ap.add_argument('--odds',help='Twelve comma-separated gross final return odds')
    ap.add_argument('--write',action='store_true',help='Write the recalculated JSON; otherwise print only')
    args=ap.parse_args();original=args.file.read_bytes();obj=json.loads(original)
    if args.winner is not None:obj.update(winner=args.winner,pic=args.winner)
    if args.odds is not None:obj['return_odds']=[int(x)for x in args.odds.split(',')]
    obj=codec.recalculate_round(obj);text=json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
    if args.write:
        if args.file.read_bytes()!=original:raise SystemExit('File changed while recalculating; no write performed')
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=args.file.parent,delete=False,prefix='.'+args.file.name+'.')as f:
            tmp=Path(f.name);f.write(text);f.flush();os.fsync(f.fileno())
        try:os.replace(tmp,args.file)
        finally:tmp.unlink(missing_ok=True)
        print('Updated '+str(args.file))
    else:print(text,end='')
