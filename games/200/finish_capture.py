#!/usr/bin/env python3
"""Revalidate/backfill a stopped or snapshotted Pappu session; live uses the same exporter."""
import argparse
import json
from pathlib import Path
from round_export import Collector

HERE=Path(__file__).resolve().parent

def finish(session):
    session=Path(session)
    source=json.loads((session/'source.json').read_text())
    collector=Collector(HERE,session,source['currency'])
    raw=(session/'frames.jsonl').read_text()
    lines=raw.splitlines(keepends=True)
    for number,line in enumerate(lines,1):
        if not line.endswith('\n'):
            collector.stats['partial_lines_retained']+=1;continue
        try:rec=json.loads(line)
        except ValueError as error:
            collector.stats['malformed_lines_retained']+=1;collector.log('math_errors.jsonl',{'line':number,'error':str(error)});continue
        status=collector.feed(rec)
        if status:print(status)
    report={'session':session.name,'source_currency':source['currency'],
            'stats':dict(collector.stats),'round_ids':[r['round_id'] for r in collector.rounds],
            'protocol':'Plaintext Pappu Command protobuf over TLS; no independent application signature field in original codec or verified known frames',
            'checks':['complete request/ack/result frame byte round-trip','own uid and unique clientCheckNum match',
                      'original room/wagers context','single ordinary reward and picture','gross-return payout','wallet delta','exclusive atomic publication'],
            'limitations':['RTP/weights are not inferred','special isBonus mode has no positive sample','ordinary nonwinning area return-odds values preserved; full distribution unknown']}
    (HERE/'math_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    index={'rounds':{r['round_id']:{'session':session.name,'currency':source['currency'],'currency_code':r['currency_code'],'full_frame_roundtrip':True} for r in collector.rounds}}
    index_path=HERE/'math_sources.json'
    if index_path.exists():
        previous=json.loads(index_path.read_text());previous.setdefault('rounds',{}).update(index['rounds']);index=previous
    index_path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    # Curated Go regression fixtures live in pappumath/game/testdata; captures never overwrite them.
    print(json.dumps(report['stats'],ensure_ascii=False))
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--session',default=(HERE/'current_session.txt').read_text().strip());args=ap.parse_args()
    r=finish(args.session)
    if r['stats'].get('validation_errors') or r['stats'].get('publish_conflicts') or not r['round_ids']:raise SystemExit(1)
