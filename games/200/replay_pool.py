"""Pappu replay results with per-settlement math reload and a simulated wallet."""
from copy import deepcopy
import importlib.util,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pappu_replay_codec',HERE/'math_adapter.py')
codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)

class ReplayPool:
    def __init__(self,source='math',math_dir=None,round_ids=None,samples=None):
        if source not in ('math','wire'):raise ValueError('source must be math or wire')
        self.source=source;self.math_dir=Path(math_dir)if math_dir else HERE/'math'
        self.samples=samples if samples is not None else json.loads((HERE/'replay_samples.json').read_text())
        rows=self.samples['rounds']
        if round_ids:
            lookup={r['round_id']:r for r in rows}
            if any(r not in lookup for r in round_ids):raise ValueError('Unknown selected original round')
            rows=[lookup[r]for r in round_ids]
        if not rows:raise ValueError('No replay samples')
        self.rows=rows

    def read(self,index):
        row=self.rows[index%len(self.rows)]
        obj=json.loads((self.math_dir/(row['round_id']+'.json')).read_text())if self.source=='math'else deepcopy(row['original_math'])
        obj=codec.validate_round(obj)
        if obj['round_id']!=row['round_id']:raise ValueError('Edited round ID differs from its filename')
        if obj['currency']!='IDR' or obj['currency_code']!=self.samples['currency_code']:raise ValueError('Replay currency mismatch')
        return row,obj

    def settle(self,index,bets,balance):
        if len(bets)!=12:raise ValueError('Expected twelve frozen local bets')
        bets=[codec.money(x)for x in bets];balance=codec.money(balance)
        row,obj=self.read(index)
        win=codec.wire_money(bets[obj['winner']-1]*obj['return_odds'][obj['winner']-1])
        post=codec.wire_money(balance+win)
        frame=codec.wire_to_math(bytes.fromhex(row['result_hex']),'RECV')
        d=frame['data'];entry=deepcopy(d['reward'][0]);entry.update(key=obj['winner'],value=True)
        d.update(win=win,postCoin=post,reward=[entry],pic=obj['pic'],bonus=[0]+obj['return_odds'],isBonus=False)
        wire=codec.math_to_wire(frame)
        decoded=codec.wire_to_math(wire,'RECV')
        if decoded['data']['win']!=win or decoded['data']['postCoin']!=post:raise ValueError('Replay result encoding mismatch')
        return wire,{'source_round':row['round_id'],'winner':obj['winner'],'return_odds':obj['return_odds'],
                     'local_bets':bets,'bet_total':sum(bets),'total_win':win,'balance_after':post,'source':self.source}
