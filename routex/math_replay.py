"""Refresh numeric per-round math JSON before a local replay SPIN."""
import json
from pathlib import Path


def input_key(request):
    return float(request['bet']), json.dumps(request['special'], sort_keys=True, separators=(',', ':'))


class MathReplay:
    def __init__(self, directory, encode, rounds='', watch=True):
        self.directory = Path(directory)
        self.encode = encode
        self.rounds = [r for r in rounds.split(',') if r]
        self.watch = watch
        self.cache = {}
        self.pools = {}
        self.refresh(force=True)

    def refresh(self, force=False):
        if not force and not self.watch:
            return self.pools
        files = ([self.directory / (rid + '.json') for rid in self.rounds]
                 if self.rounds else sorted(p for p in self.directory.glob('*.json') if p.stem.isdigit()))
        if not files:
            raise ValueError('No math round JSON files: ' + str(self.directory))
        updated, pools = {}, {}
        for path in files:
            stat = path.stat()
            stamp = (stat.st_mtime_ns, stat.st_size)
            old = self.cache.get(path)
            if old is not None and old[0] == stamp:
                item = old
            else:
                sample = json.loads(path.read_text(encoding='utf-8'))
                if sample['roundIndexV2'] != path.stem:
                    raise ValueError('Round ID differs from filename: ' + path.name)
                item = (stamp, input_key(sample['spinReq']), self.encode(sample))
            updated[path] = item
            pools.setdefault(item[1], []).append(item[2])
        # Publish only a complete valid refresh. Invalid edits never fall back to
        # old wire samples or silently continue replaying a stale math result.
        self.cache, self.pools = updated, pools
        return self.pools
