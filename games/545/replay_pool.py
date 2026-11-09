"""545 replay pools keyed by measured request fields, excluding UI context f25."""
import json
from pathlib import Path
from math_adapter import records,fields,math_to_wire


def action_key(action):
    return b''.join(raw for n,w,v,raw in records(action) if n!=25)


class MathReplay:
    def __init__(self,directory,rounds='',watch=True):
        self.directory=Path(directory);self.selected=rounds.split(',') if rounds else []
        self.watch=watch;self.pools={};self.refresh()
    def refresh(self):
        if self.pools and not self.watch:return self.pools
        paths=[self.directory/(rid+'.json') for rid in self.selected] if self.selected else sorted(p for p in self.directory.glob('*.json') if p.stem.isdigit())
        pools={}
        for path in paths:
            obj=json.loads(path.read_text());raw=math_to_wire(obj)
            key=action_key(fields(raw)[23][1]);pools.setdefault(key,[]).append(raw)
        if not pools:raise ValueError('No math replay samples')
        self.pools=pools
        return pools
