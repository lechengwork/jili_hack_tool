#!/usr/bin/env python3
"""Real-sample and independent codec regression tests. Never starts a browser or wagers."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from round_export import Collector, atomic_json, codec

HERE=Path(__file__).resolve().parent

class MathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index=json.loads((HERE/'math_sources.json').read_text())['rounds']
        cls.original=[]
        for rid,info in cls.index.items():
            source=json.loads((HERE/'webcap'/info['session']/'math_wire'/(rid+'.json')).read_text())
            obj=codec.round_to_math(source,currency=info['currency'])
            cls.original.append((source,obj))

    def test_six_real_rounds_restore_complete_original_command(self):
        self.assertEqual(len(self.original),6)
        for source,obj in self.original:
            self.assertEqual(codec.math_round_to_wire(obj,source),bytes(source['data']['_wire']))
            self.assertEqual(obj['bets'][obj['winner']-1]*obj['return_odds'][obj['winner']-1],obj['total_win'])
            text=json.dumps(obj)
            for forbidden in ('_wire','token','accountID','req_body','ssoKey','bearer'):self.assertNotIn(forbidden,text)

    def test_edits_decode_with_original_frontend_and_math_proto(self):
        vectors=[]
        for source,obj in self.original:
            edited=deepcopy(obj)
            winner=next(i+1 for i,v in enumerate(obj['bets']) if v>0)
            edited.update(winner=winner,pic=winner)
            edited['return_odds'][winner-1]=20
            edited=codec.recalculate_round(edited)
            with self.assertRaises(ValueError):codec.math_round_to_wire(edited,source)
            balance=obj['balance_after']+edited['total_win']-obj['total_win']
            for template in (source,None):
                wire=codec.math_round_to_wire(edited,template,post_coin=balance)
                vectors.append({'hex':wire.hex(),'winner':winner,'odds':edited['return_odds'],
                                'win':edited['total_win'],'balance':balance,'round':edited})
        with tempfile.TemporaryDirectory(prefix='pappu-codec-') as tmp:
            p=Path(tmp)/'vectors.json';p.write_text(json.dumps(vectors))
            subprocess.run(['node',str(HERE/'analysis/verify_math.cjs'),str(p)],check=True)

    def test_zero_sentinel_invalid_modes_indices_and_wallet(self):
        source,obj=self.original[0]
        zero=deepcopy(obj);zero['return_odds']=[0]*12
        self.assertEqual(codec.recalculate_round(zero)['return_odds'],[10]*12)
        for key,value in [('bets',[0]*11),('return_odds',[10]*13),('winner',0),('winner',13),
                          ('is_bonus',True),('round_id',int(obj['round_id'])),('pic',99)]:
            bad=deepcopy(obj);bad[key]=value
            with self.assertRaises(ValueError):codec.validate_round(bad)
        bad=deepcopy(obj);bad['return_odds'][0]=9
        with self.assertRaises(ValueError):codec.validate_round(bad)
        bad=deepcopy(obj);bad['total_win']+=1
        with self.assertRaises(ValueError):codec.validate_round(bad)
        changed=deepcopy(obj);changed['bets'][0]+=1;changed=codec.recalculate_round(changed)
        with self.assertRaises(ValueError):codec.math_round_to_wire(changed,source,post_coin=obj['balance_after'])
        bad=deepcopy(obj);bad['return_odds'][0]=(1<<53)+1;bad=codec.recalculate_round(bad)
        with self.assertRaisesRegex(ValueError,'represented exactly'):codec.math_round_to_wire(bad,source)

    def test_unknown_wire_field_preserved_and_not_silently_published(self):
        source,obj=self.original[0];raw=bytes(source['data']['_wire'])+codec.field(100,0,codec.varint(7))
        d=codec.wire_to_math(raw,'RECV')
        self.assertEqual(codec.math_to_wire(d),raw)
        changed=deepcopy(source);changed['data']=d
        with self.assertRaisesRegex(ValueError,'Unconfirmed field'):codec.round_to_math(changed,currency=obj['currency'])

    def test_same_live_exporter_publishes_and_preserves_human_edits(self):
        sessions={info['session'] for info in self.index.values()};self.assertEqual(len(sessions),1)
        session=HERE/'webcap'/next(iter(sessions))
        frames=[json.loads(line) for line in (session/'frames.jsonl').read_text().splitlines()]
        with tempfile.TemporaryDirectory(prefix='pappu-live-export-') as tmp:
            root=Path(tmp);game=root/'200'
            a=Collector(game,root/'session-a','IDR')
            for frame in frames:a.feed(frame)
            self.assertEqual(a.stats['validation_errors'],0)
            self.assertEqual(a.stats['published_rounds'],6)
            p=game/'math'/(self.original[0][1]['round_id']+'.json')
            human=json.loads(p.read_text());human['return_odds'][0]=40
            human=codec.recalculate_round(human);p.write_text(json.dumps(human,indent=3)+'\n');before=p.read_bytes()
            b=Collector(game,root/'session-b','IDR')
            for frame in frames:b.feed(frame)
            self.assertEqual(b.stats['publish_conflicts'],1)
            self.assertEqual(p.read_bytes(),before)
            self.assertTrue((root/'session-b/math_export'/p.name).exists())
            self.assertTrue((root/'session-b/math_conflicts.jsonl').exists())

    def test_atomic_create_does_not_replace_existing_file(self):
        with tempfile.TemporaryDirectory(prefix='pappu-atomic-') as tmp:
            p=Path(tmp)/'round.json';atomic_json(p,{'value':1})
            self.assertEqual(atomic_json(p,{'value':1}),'unchanged')
            with self.assertRaises(FileExistsError):atomic_json(p,{'value':2})
            self.assertEqual(json.loads(p.read_text()),{'value':1})

    def test_other_player_ack_with_same_check_number_is_not_own_wager(self):
        session=HERE/'webcap'/next(iter(self.index.values()))['session']
        frames=[json.loads(line) for line in (session/'frames.jsonl').read_text().splitlines()]
        with tempfile.TemporaryDirectory(prefix='pappu-other-player-') as tmp:
            root=Path(tmp);collector=Collector(root/'200',root/'session','IDR');injected=False
            for rec in frames:
                if not injected and rec['dir']=='RECV':
                    try:d=codec.wire_to_math(bytes.fromhex(rec['hex']),'RECV')
                    except ValueError:d=None
                    if d and d['command']==22:
                        d['data']['accountID']=str(int(d['data']['accountID'])+1)
                        foreign=deepcopy(rec);foreign['hex']=codec.math_to_wire(d).hex()
                        collector.feed(foreign);injected=True
                collector.feed(rec)
            self.assertTrue(injected)
            self.assertEqual(collector.stats['other_player_acks'],1)
            self.assertEqual(collector.stats['validation_errors'],0)
            self.assertEqual(collector.stats['published_rounds'],6)

if __name__=='__main__':unittest.main(verbosity=2)
