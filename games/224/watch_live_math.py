#!/usr/bin/env python3
"""Passive live export for a running 224 capture; no browser restart or wagering."""
import argparse,json,time
from pathlib import Path
from math_adapter import wire_to_math,round_to_math,math_to_round_wire
from atomic_math import _write_json
HERE=Path(__file__).resolve().parent

def command(hexstr):
    b=bytes.fromhex(hexstr);p=0
    def vi():
        nonlocal p
        n=0
        for shift in range(0,70,7):
            if p>=len(b):raise ValueError('truncated wrapper')
            v=b[p];p+=1;n|=(v&127)<<shift
            if v<128:return n
        raise ValueError('oversized wrapper varint')
    cmd=0
    while p<len(b):
        t=vi();n,w=t>>3,t&7
        if w==0:
            v=vi()
            if n==1:cmd=v
        elif w==2:
            length=vi();p+=length
        elif w==1:p+=8
        elif w==5:p+=4
        else:raise ValueError('unsupported wrapper')
        if p>len(b):raise ValueError('truncated wrapper')
    return cmd

class Collector:
    def __init__(self,session):
        self.session=session;self.pending=None;self.active=None;self.counts={'verified_rounds':0,'published_math':0,'observer_settlements':0,'zero_bet_settlements':0,'failed_bets':0,'errors':0,'conflicts':0,'verified_application_frames':0};self.last_seq=None
    def log(self,name,value):
        with (self.session/name).open('a') as f:f.write(json.dumps(value,ensure_ascii=False)+'\n')
    def error(self,exc,seq):
        self.counts['errors']+=1;self.log('math_errors.jsonl',{'seq':seq,'error':str(exc),'raw_preserved':True});print('[224 math error] '+str(exc),flush=True)
    def feed(self,r):
        self.last_seq=r.get('seq');c=command(r['hex']);direction=r.get('dir')
        if not ((direction=='SEND' and c in (10,11)) or (direction=='RECV' and c in (10,11,13,16))):return
        f=wire_to_math([r])[0];self.counts['verified_application_frames']+=1
        self.log('verified_decoded.jsonl',f)
        if f['message']=='BetReq':
            if self.pending or self.active:raise ValueError('Overlapping own bet needs explicit correlation')
            self.pending=f
        elif f['message']=='BetResp':
            if f['data'].get('betFailed',False):self.counts['failed_bets']+=1;self.pending=None;return
            if not self.pending:raise ValueError('Own bet ack missing request')
            self.active={'request':self.pending,'ack':f,'cashout_requests':[],'cashouts':[]};self.pending=None
        elif f['message']=='CashOutReq':
            if not self.active:raise ValueError('Cashout request without accepted bet')
            self.active['cashout_requests'].append(f)
        elif f['message']=='CashOut':
            if not self.active:raise ValueError('Cashout reply without accepted bet')
            self.active['cashouts'].append(f)
        elif f['message']=='FlyEnd':
            if not self.active:self.counts['observer_settlements']+=1;return
            source=self.active;self.active=None;source['end']=f
            if sum(b.get('bet',0) for b in source['request']['data'].get('betData',[]))<=0:
                self.counts['zero_bet_settlements']+=1;return
            value=round_to_math(source)
            if any(a.hex()!=b['_wire'] for a,b in zip(math_to_round_wire(value,source),[source['request'],source['ack'],*source['cashout_requests'],*source['cashouts'],source['end']])):raise ValueError('Public math/full frame reverse roundtrip failed')
            rid=value['round_id'];self.counts['verified_rounds']+=1
            _write_json(self.session/'math_wire'/(rid+'.json'),source)
            _write_json(self.session/'math'/(rid+'.json'),value)
            try:
                _write_json(HERE/'math'/(rid+'.json'),value);self.counts['published_math']+=1
            except FileExistsError as exc:
                self.counts['conflicts']+=1;self.log('math_conflicts.jsonl',{'round_id':rid,'error':str(exc),'source_preserved':True})
            print('[224 math] '+rid+' verified and saved',flush=True)
    def status(self):
        v={**self.counts,'session':str(self.session),'last_seq':self.last_seq,'pending_bet':bool(self.pending),'active_round':bool(self.active),'signature':'No independent application signature field in observed plaintext protobuf/TLS frames; original codec and full-frame roundtrip verified','currency':'IDR','updated_at':time.strftime('%Y-%m-%dT%H:%M:%S%z')}
        p=self.session/'math_status.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)

def run(session,once=False):
    collector=Collector(session);offset=0
    while True:
        path=session/'frames.jsonl'
        if path.exists():
            with path.open('rb') as f:
                f.seek(offset)
                while True:
                    start=f.tell();line=f.readline()
                    if not line or not line.endswith(b'\n'):break
                    offset=f.tell()
                    try:collector.feed(json.loads(line))
                    except Exception as exc:
                        collector.error(exc,collector.last_seq);collector.pending=None;collector.active=None
        collector.status()
        if once:return collector
        time.sleep(0.5)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--once',action='store_true');ap.add_argument('--session',type=Path);args=ap.parse_args()
    run(args.session or Path((HERE/'current_session.txt').read_text().strip()),args.once)
