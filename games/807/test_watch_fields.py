import contextlib,copy,io,json,tempfile,unittest
from pathlib import Path
from math_adapter import field,varint,wire_fields
from watch_fields import Monitor,HERE,acquire_lock


def replace(buf,number,wire,value):
    out=b'';found=False
    for n,w,v in wire_fields(buf):
        if n==number:w,v=wire,value;found=True
        out+=field(n,w,varint(v) if w==0 else v)
    if not found:out+=field(number,wire,varint(value) if wire==0 else value)
    return out


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.baseline=HERE/'replay_samples.json'
        self.monitor=Monitor(self.root/'out',self.baseline)
        rows=json.loads(self.baseline.read_text(encoding='utf-8'));self.row=next(r for r in rows if r['type']==0 and r['ret']==0)
        self.raw=bytes.fromhex(self.row['raw_hex']);self.action=bytes.fromhex(self.row['action_hex'])
        self.raw=replace(self.raw,20,0,9999999999990000807)
        self.board=next(v for n,w,v in wire_fields(self.raw) if n==1)

    def process(self,raw,signature=True):
        with contextlib.redirect_stdout(io.StringIO()):
            self.monitor.process({'raw':list(raw),'type':0,'ret':0,'_sig_ok':signature,'idx':1},self.action,'fixture')

    def events(self):
        p=self.root/'out/events.jsonl'
        return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []

    def test_duplicate_monitor_is_rejected(self):
        handle=acquire_lock(self.root/'locked');self.addCleanup(handle.close)
        with self.assertRaises(RuntimeError):acquire_lock(self.root/'locked')

    def test_baseline_is_not_new_and_replay_is_deduplicated(self):
        self.process(bytes.fromhex(self.row['raw_hex']))
        self.assertEqual(self.monitor.state['new_rounds'],0)
        self.process(self.raw);self.process(self.raw)
        self.assertEqual(self.monitor.state['new_rounds'],1)

    def test_unknown_nested_field_is_preserved_when_adapter_rejects(self):
        raw=replace(self.raw,1,2,replace(self.board,10,0,77));self.process(raw)
        events=self.events();self.assertIn('new_field',[x['kind'] for x in events])
        evidence=json.loads(Path(events[0]['evidence']).read_text(encoding='utf-8'))
        self.assertEqual(evidence['payload_hex'],raw.hex())
        self.assertTrue(any(x['kind']=='adapter_rejected' for x in events))
        self.assertNotIn('token',evidence)

    def test_nonempty_f9_and_nonzero_f17_are_detected(self):
        board=replace(replace(self.board,9,2,b'\x01'),17,2,b'\0\0\x01\0\0')
        self.process(replace(self.raw,1,2,board));kinds={x['kind'] for x in self.events()}
        self.assertIn('new_nonempty_f9',kinds);self.assertIn('new_slots17_slot',kinds)
        self.assertIn('adapter_rejected',kinds)

    def test_counterexample_is_not_promoted_to_rule(self):
        board=replace(self.board,19,1,__import__('struct').pack('<d',999))
        self.process(replace(replace(self.raw,1,2,board),3,1,__import__('struct').pack('<d',999)))
        self.assertIn('win_sum_counterexample',{x['kind'] for x in self.events()})

    def test_unverified_signature_is_excluded(self):
        self.process(self.raw,False)
        self.assertEqual(self.monitor.state['new_rounds'],0)
        self.assertEqual(self.events()[0]['kind'],'signature_failure')

    def test_partial_line_and_resume_do_not_lose_or_duplicate_round(self):
        session=self.root/'session';session.mkdir();p=session/'exchanges_ordered.jsonl'
        line=json.dumps({'raw':list(self.raw),'type':0,'ret':0,'_sig_ok':True,'idx':1})+'\n'
        p.write_text(line[:len(line)//2], encoding='utf-8');self.monitor.scan(session)
        self.assertEqual(self.monitor.state['new_rounds'],0)
        with p.open('a', encoding='utf-8') as out:out.write(line[len(line)//2:])
        self.monitor.scan(session);self.assertEqual(self.monitor.state['new_rounds'],1)
        restored=Monitor(self.root/'out',self.baseline);restored.scan(session)
        self.assertEqual(restored.state['new_rounds'],1)


if __name__=='__main__':unittest.main()
