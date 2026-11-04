#!/usr/bin/env python3
"""Passive 807 evidence monitor. Does not send bets, change modes or alter proto files."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import time

from math_adapter import SCHEMA, fields, wire_fields, read_varint, wire_to_math, math_to_wire

HERE = Path(__file__).resolve().parent
PAY = {0:1,1:2,2:3.5,3:5,4:6,5:7.5,6:10}
MULT = {9:1,10:2,11:3,12:5,13:10,14:15,15:20,16:25,17:50,21:0}


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def packed(value):
    out, pos = [], 0
    while pos < len(value):
        number, pos = read_varint(value, pos)
        out.append(number)
    return out


def tree(raw, message='SpinResult', path='result'):
    """Retain unknown bytes without guessing their type or dropping the round."""
    top = {1:('data','SpinAck',2),2:('service',None,2),3:('total_win',None,1),
           6:('postMoney',None,1),20:('round_id',None,0),23:('bet','BetInfo',2)}
    bet = {1:('bet',None,1),25:('special',None,2)}
    if message in ('SpinResult','BetInfo'):
        specs = top if message == 'SpinResult' else bet
    else:
        specs = {}
        for f in SCHEMA[message]:
            typ = f['type']
            wire = 2 if typ in SCHEMA or f['repeated'] or typ=='packed_presence' else 1 if typ=='double' else 0
            specs[f['number']] = (f['name'], typ if typ in SCHEMA else None, wire)
    nodes, issues = [], []
    for number, wire, value in wire_fields(raw):
        label, sub, expected = specs.get(number, ('unknown',None,None))
        where = path + '.f' + str(number)
        node = {'field':number,'wire':wire,'name':label}
        if expected is None:
            issues.append(('new_field',where,{'wire':wire}))
        elif wire != expected:
            issues.append(('wire_change',where,{'expected':expected,'actual':wire}))
        if isinstance(value, bytes):
            node['raw_hex'] = value.hex()
            if sub and wire == 2:
                node['children'], found = tree(value,sub,where)
                issues.extend(found)
            elif wire == 1:
                node['double'] = struct.unpack('<d',value)[0]
        else:
            node['value'] = value
        nodes.append(node)
    return nodes, issues


def features(raw):
    outer = fields(raw)
    body = list(wire_fields(outer[1][1]))
    by = {}
    for no, wire, value in body:
        by.setdefault(no,[]).append(value)
    def one(no, default=0): return by.get(no,[default])[0]
    def vector(no): return packed(one(no,b''))
    win = struct.unpack('<d',one(19,bytes(8)))[0]
    lines=[]
    for value in by.get(11,[]):
        f=fields(value)
        lines.append({'symbol':f.get(1,(0,0))[1], 'cash':struct.unpack('<d',f.get(4,(1,bytes(8)))[1])[0]})
    reel=packed(fields(one(3,b''))[1][1]) if one(3,b'') else []
    return {'round_id':str(outer[20][1]),'bet':struct.unpack('<d',fields(outer[23][1])[1][1])[0],
            'win':win,'outer_win':struct.unpack('<d',outer.get(3,(1,bytes(8)))[1])[0],
            'lines':lines,'win_type':one(12),'multiplier':one(18),'reel':reel,
            'slots13':vector(13),'slots17':vector(17),'f9_present':9 in by,
            'f9_nonempty':bool(one(9,b'')), 'f21':struct.unpack('<d',one(21,bytes(8)))[0],
            'special_fields':[n for n in [4,5,6,7,8,9] if n in by],
            'body':by}


class Monitor:
    def __init__(self, directory, baseline, resume=True):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True,exist_ok=True)
        baseline = Path(baseline)
        fingerprint = hashlib.sha256(baseline.read_bytes()).hexdigest()
        self.state = {'version':2,'baseline_sha256':fingerprint,'seen':{},'known':{},'examples':{},
                      'baseline_rounds':0,'new_rounds':0,'special_rounds':0,'last_spin':None,
                      'last_activity':None,'cursors':{},'status':'waiting_for_capture'}
        for row in json.loads(baseline.read_text(encoding='utf-8')):
            if row['type'] == 0 and row['ret'] == 0:
                raw=bytes.fromhex(row['raw_hex']);f=features(raw)
                self.state['seen'][f['round_id']]=hashlib.sha256(raw).hexdigest()
                self.state['baseline_rounds']+=1
                for kind,key in self.signatures(f,bytes.fromhex(row['action_hex'])):
                    self.remember(kind,key)
        saved=self.directory/'state.json'
        if resume and saved.exists():
            previous=json.loads(saved.read_text(encoding='utf-8'))
            if previous.get('version')!=2 or previous.get('baseline_sha256')!=fingerprint:
                raise ValueError('Baseline changed; use a new --out directory to preserve evidence')
            self.state=previous
        self.save()

    def remember(self,kind,key):
        values=self.state['known'].setdefault(kind,[])
        encoded=json.dumps(key,sort_keys=True,separators=(',',':'))
        if encoded in values:return False
        values.append(encoded);return True

    @staticmethod
    def signatures(f, action):
        result=[('win_type',f['win_type']),('bet',f['bet']),('config_f21',f['f21'])]
        if action is not None:result.append(('spin_action',action.hex()))
        if f['special_fields']:
            result.append(('effect_combination',f['special_fields']))
            result.append(('extension',[f['body'].get(4,[0])[0],packed(f['body'].get(5,[b''])[0])]))
            result.append(('effect_shape',[(n,len(f['body'].get(n,[]))) for n in [4,5,6,7,8,9]]))
            for no in [6,7]:
                for raw_symbol in f['body'].get(no,[]):
                    item=fields(raw_symbol)
                    result.append(('effect_symbol_f'+str(no),[item.get(1,(0,0))[1],item.get(2,(0,0))[1]]))
        for name in ['slots13','slots17']:
            for i,value in enumerate(f[name]):
                if value:
                    result.append((name+'_slot',i))
                    result.append((name+'_value',[i,value]))
        if f['f9_nonempty']:result.append(('nonempty_f9',True))
        if len(f['reel'])==5 and not f['special_fields']:
            result.append(('center_symbol',f['reel'][2]))
        return result

    def save(self):
        atomic_json(self.directory/'state.json',self.state)
        public={k:v for k,v in self.state.items() if k not in ['seen','known','cursors']}
        public['unique_rounds']=len(self.state['seen'])
        public['open_questions']=['f6/f7 full feature meaning','f8 indices','nonempty f9',
                                  'f13/f17 effect slots','unseen modes and win types','f21 meaning']
        public['proto_complete']=False
        atomic_json(self.directory/'summary.json',public)

    def emit(self,kind,message,rid=None,details=None,evidence=None):
        event={'time':datetime.now(timezone.utc).isoformat(),'kind':kind,'message':message}
        if rid:event['round_id']=rid
        if details is not None:event['details']=details
        if evidence:event['evidence']=str(evidence)
        with (self.directory/'events.jsonl').open('a', encoding='utf-8') as output:
            output.write(json.dumps(event,ensure_ascii=False)+'\n')
        notice_key=kind+':'+str((details or {}).get('path',''))
        counts=self.state.setdefault('notice_counts',{})
        counts[notice_key]=counts.get(notice_key,0)+1
        if counts[notice_key]<=3:
            print('[807 watch] '+message+(' | round='+rid if rid else ''),flush=True)
        elif counts[notice_key]==4:
            print('[807 watch] 同類 '+kind+' 後續只寫入事件與證據檔，避免刷屏',flush=True)

    def process(self,row,action=None,source=None):
        self.state['last_activity']=time.time()
        if not isinstance(row,dict):
            self.emit('invalid_record','側錄行不是回應物件，不納入證據')
            return
        if row.get('_sig_ok') is not True:
            self.emit('signature_failure','回應驗章未通過；不納入規則證據',details={'source':source,'idx':row.get('idx')})
            return
        if row.get('type')!=0 or row.get('ret')!=0:return
        try:
            raw=bytes(row['raw'])
        except (ValueError,TypeError,KeyError):
            self.emit('invalid_record','側錄缺少有效 raw payload，不納入證據')
            return
        digest=hashlib.sha256(raw).hexdigest()
        try:
            f=features(raw);rid=f['round_id']
        except Exception as error:
            evidence=self.directory/'evidence'/('unparsed-'+digest[:16]+'.json')
            atomic_json(evidence,{'payload_hex':raw.hex(),'source':source,'idx':row.get('idx'),'error':str(error)})
            self.emit('parse_failure','新轉局結構無法按現有規格解析，原始 payload 已保留',evidence=evidence)
            return
        previous=self.state['seen'].get(rid)
        if previous==digest:return
        if previous:
            self.emit('round_conflict','同一單號出現不同 payload，需確認 session／資料來源',rid)
            return
        self.state['seen'][rid]=digest
        self.state['new_rounds']+=1
        self.state['last_spin']=time.time()
        self.state['status']='capturing'
        try:
            nodes,issues=tree(raw)
        except Exception as error:
            nodes=[]
            issues=[('structure_error','result',{'error':str(error)})]
        events=[(kind,'發現未知欄位或 wire type 變化：'+where,dict(path=where,**detail)) for kind,where,detail in issues]
        for kind,key in self.signatures(f,action):
            if self.remember(kind,key):
                events.append(('new_'+kind,'首次遇到 '+kind+'：'+str(key),{'value':key}))
        if f['special_fields'] or any(f['slots13']) or any(f['slots17']):
            self.state['special_rounds']+=1
            pattern=json.dumps([f['special_fields'],[i for i,v in enumerate(f['slots13']) if v],
                                [i for i,v in enumerate(f['slots17']) if v]],separators=(',',':'))
            count=self.state['examples'].get(pattern,0)+1
            self.state['examples'][pattern]=count
            if count<=3:events.append(('special_example','保留隨機效果的第 '+str(count)+' 個新樣本',{'pattern':json.loads(pattern)}))
        if not math.isclose(sum(x['cash'] for x in f['lines']),f['win'],abs_tol=1e-8,rel_tol=1e-9) or not math.isclose(f['outer_win'],f['win'],abs_tol=1e-8,rel_tol=1e-9):
            events.append(('win_sum_counterexample','派彩加總規則出現反例',{}))
        # Only test the observed normal-reel rule in its established domain.
        if len(f['reel'])==5 and not f['special_fields'] and f['win_type'] in [0,1]:
            symbol=f['reel'][2]
            if symbol in MULT and MULT[symbol]!=f['multiplier']:
                events.append(('multiplier_counterexample','普通轉輪中間格／倍率對照出現反例',{'symbol':symbol,'multiplier':f['multiplier']}))
        for line in f['lines']:
            if line['symbol'] in PAY:
                expected=f['bet']*PAY[line['symbol']]*f['multiplier']/5
                if not math.isclose(line['cash'],expected,abs_tol=1e-8,rel_tol=1e-9):
                    events.append(('payrate_counterexample','線獎／下注／倍率公式出現反例',line))
        decoded=None
        try:
            decoded=wire_to_math(raw)
            if math_to_wire(decoded)!=raw:events.append(('roundtrip_failure','既有 adapter 無法 byte 級還原此局',{}))
        except Exception as error:
            events.append(('adapter_rejected','既有 adapter 拒絕此局；保留原始證據供擴充 proto',{'error':str(error)}))
        if events:
            evidence=self.directory/'evidence'/(rid+'.json')
            # Never persist the request's bearer token, X25519 key or AES session key.
            atomic_json(evidence,{'round_id':rid,'source':source,'idx':row.get('idx'),
                        'capture_time':row.get('time'),'payload_hex':raw.hex(),'spin_action_hex':action.hex() if action is not None else None,
                        'field_tree':nodes,'math':decoded,'events':[{'kind':k,'details':d} for k,m,d in events]})
            for kind,message,details in events:self.emit(kind,message,rid,details,evidence)
        self.save()

    def read_lines(self,path):
        path=Path(path)
        if not path.exists():return []
        key=str(path.resolve());stat=path.stat();cursor=self.state['cursors'].get(key,{})
        offset=cursor.get('offset',0) if cursor.get('inode')==stat.st_ino else 0
        if offset>stat.st_size:offset=0
        rows=[]
        with path.open('rb') as stream:
            stream.seek(offset)
            while True:
                start=stream.tell();line=stream.readline()
                if not line or not line.endswith(b'\n'):
                    stream.seek(start);break
                try:rows.append(json.loads(line))
                except (ValueError,UnicodeDecodeError):
                    self.emit('invalid_json','側錄出現完整但無法解析的 JSON 行',details={'file':key,'offset':start})
            offset=stream.tell()
        self.state['cursors'][key]={'offset':offset,'inode':stat.st_ino}
        return rows

    def scan(self,session):
        session=Path(session)
        # Rebuild a local action index on each pass; authentication fields are discarded.
        actions={}
        requests=session/'exchanges.jsonl'
        if requests.exists():
            with requests.open() as stream:
                for line in stream:
                    try:
                        r=json.loads(line);request=fields(bytes.fromhex(r['req_body_hex']))
                        actions[r['seq']]=request.get(2,(2,b''))[1]
                    except (ValueError,KeyError,IndexError):continue
        for row in self.read_lines(session/'exchanges_ordered.jsonl'):
            self.process(row,actions.get(row.get('idx')),str(session))
        self.save()



def acquire_lock(directory):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    handle=(directory/'watch.lock').open('a+b')
    try:
        if os.name=='nt':
            import msvcrt
            handle.seek(0)
            if not handle.read(1):handle.write(b'0');handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:
        handle.close()
        raise RuntimeError('Another 807 monitor already owns this output directory')
    return handle


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--session',help='Fixed capture directory; otherwise follow current_session.txt')
    ap.add_argument('--baseline',default=str(HERE/'replay_samples.json'))
    ap.add_argument('--out',default=str(HERE/'monitor'))
    ap.add_argument('--once',action='store_true')
    ap.add_argument('--poll',type=float,default=2)
    ap.add_argument('--idle',type=float,default=300)
    ap.add_argument('--max-new-rounds',type=int,default=2000,help='0 means unlimited; reaching a count does not mean the proto is complete')
    args=ap.parse_args()
    if args.poll<=0 or args.idle<=0 or args.max_new_rounds<0:ap.error('Invalid polling/goal values')
    try:
        lock_handle=acquire_lock(args.out)
    except RuntimeError as error:
        ap.error(str(error))
    monitor=Monitor(args.out,args.baseline)
    atomic_json(Path(args.out)/'process.json',{'pid':os.getpid(),'max_new_rounds':args.max_new_rounds,'passive_only':True})
    print('[807 watch] baseline=%s; new=%s; waiting for verified live capture; output=%s' %
          (monitor.state['baseline_rounds'],monitor.state['new_rounds'],Path(args.out).resolve()),flush=True)
    idle_reported=False;started=time.time()
    try:
        while True:
            pointer=HERE/'current_session.txt'
            session=Path(args.session) if args.session else Path(pointer.read_text(encoding='utf-8').strip()) if pointer.exists() else None
            old=monitor.state['new_rounds']
            if session:monitor.scan(session)
            if monitor.state['new_rounds']>old:idle_reported=False
            if args.once:
                print(json.dumps({'baseline':monitor.state['baseline_rounds'],'new_rounds':monitor.state['new_rounds'],'status':monitor.state['status']},ensure_ascii=False));break
            if args.max_new_rounds and monitor.state['new_rounds']>=args.max_new_rounds:
                monitor.state['status']='round_limit_reached';monitor.save()
                monitor.emit('round_limit','已達本次樣本數上限，監看結束；這不代表欄位語意已全部確認')
                break
            if time.time()-(monitor.state['last_spin'] or started)>=args.idle and not idle_reported:
                monitor.state['status']='no_new_spins';monitor.save()
                monitor.emit('no_new_spins','已 '+str(int(args.idle))+' 秒沒有新轉局；請檢查自動轉是否停止或擷取是否斷線')
                idle_reported=True
            time.sleep(args.poll)
    except KeyboardInterrupt:
        monitor.state['status']='stopped';monitor.save()
        print('[807 watch] stopped; evidence and cursors saved',flush=True)


if __name__=='__main__':main()
