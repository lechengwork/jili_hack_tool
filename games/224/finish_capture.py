#!/usr/bin/env python3
"""Reverify a fixed capture; live math is already published by the collector/watcher."""
import hashlib,json
from pathlib import Path
from collections import Counter
from watch_live_math import Collector
from verify_math import verify
HERE=Path(__file__).resolve().parent
if __name__=='__main__':
    s=Path((HERE/'current_session.txt').read_text().strip())
    raw=(s/'frames.jsonl').read_bytes()
    if raw and not raw.endswith(b'\n'):raise ValueError('Incomplete raw tail retained; review required')
    c=Collector(s);audit=[]
    c.log=lambda name,value:audit.append({'log':name,**value})
    frames=0
    for line in raw.splitlines():
        r=json.loads(line);frames+=1
        try:c.feed(r)
        except Exception as exc:c.error(exc,c.last_seq);c.pending=None;c.active=None
    c.status()
    (s/'finish_audit.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in audit))
    report=verify(s)
    coverage=Counter()
    for p in (s/'math').glob('*.json'):
        v=json.loads(p.read_text());bets=v['spinReq']['betData'];coverage['two_bet_areas' if sum(b.get('bet',0)>0 for b in bets)==2 else 'one_bet_area']+=1
        coverage['with_cashout' if v['data']['cashOuts'] else 'no_cashout_loss']+=1
    summary={**report,**c.counts,'raw_frames':frames,'raw_sha256':hashlib.sha256(raw).hexdigest(),'incomplete_tail':False,'pending_bet':bool(c.pending),'active_round':bool(c.active),'coverage':dict(coverage),'session':s.name,'closed':(s/'capture_closed.json').exists(),'known_gaps':['Exact crash distribution, RTP and complete seed-to-combined-hash-to-multiplier verification not established; see the separate rank/fairness audit for the verified one-round commitment','Free-bet and unobserved special/cashout variants remain fail-closed'],'development_diagnostics':['Initial wrapper parser cursor bug fixed; all original frames reprocessed','Zero-bet settlements classified separately; excluded from successful math']}
    for p in [s/'final_capture_summary.json',HERE/'final_capture_summary.json']:p.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False))
