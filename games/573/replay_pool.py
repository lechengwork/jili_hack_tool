"""Pool by captured 573 input; sparse response echoes never erase extra mode."""
import json
import struct
from pathlib import Path
from math_adapter import records, fields, field, varint, math_to_wire, decode_message
from request_adapter import request_to_math

def action_key(action):
    request_to_math(action)
    def nested(buf, defaults):
        values, unknown = dict(defaults), []
        fields(buf)  # Reject ambiguous duplicated fields.
        for n, w, v, raw in records(buf):
            if n in defaults:
                if w != defaults[n][0]:
                    raise ValueError('Unexpected mode field wire type')
                values[n] = (w, v.hex() if isinstance(v, bytes) else v)
            else:
                unknown.append(raw.hex())
        return [sorted(values.items()), unknown]
    top = []
    for n, w, v, raw in records(action):
        if n == 25:
            # Only the observed UI context is omitted; unknown business fields remain.
            if w != 2 or any(i not in (1, 2, 4) or wt != 0 or val != 0
                             for i, wt, val, _ in records(v)):
                top.append((n, raw.hex()))
        elif n == 23 and w == 2:
            top.append((n, nested(v, {1: (0, 0), 2: (0, 0), 3: (1, '0000000000000000')})))
        elif n == 26 and w == 2:
            top.append((n, nested(v, {1: (0, 0)})))
        else:
            top.append((n, raw.hex()))
    return json.dumps(sorted(top), separators=(',', ':'))

def input_for_math(original_action, value, raw):
    """Keep original request-only fields; apply edited named bet/purchase inputs."""
    echo = fields(raw)[23][1]
    named = value['spinReq']
    output = bytearray()
    for n, w, v, encoded in records(original_action):
        if n == 1:
            output.extend(field(1, 1, struct.pack('<d', named['bet'])))
        elif n == 23:
            if 23 in fields(echo):
                ew, ev = fields(echo)[23]
                output.extend(field(23, ew, ev))
        elif n == 26 and named.get('f26'):
            output.extend(field(26, 2, bytes(named['f26'])))
        else:
            output.extend(encoded)
    if 23 not in fields(original_action) and named.get('purchase'):
        w, v = fields(echo)[23]
        output.extend(field(23, w, v))
    return bytes(output)

class ReplayPool:
    def __init__(self, rows, source='math', directory=None, rounds='', watch=True, bonus_first=False):
        if source not in ('math', 'wire'):
            raise ValueError('Expected math or wire replay')
        self.rows = {r['round_id']: r for r in rows if r['type'] == 0 and r['ret'] == 0}
        self.source, self.directory = source, Path(directory or Path(__file__).parent / 'math')
        self.selected = rounds.split(',') if rounds else []
        self.watch, self.bonus_first = watch, bonus_first
        self.signature, self.pools, self.metadata = None, {}, {}
        self.refresh()

    def refresh(self):
        if self.pools and not self.watch:
            return self.pools
        ids = self.selected or (sorted(p.stem for p in self.directory.glob('[0-9]*.json')
                                      if p.stem.isdigit()) if self.source == 'math' else sorted(self.rows))
        paths = [self.directory / (rid + '.json') for rid in ids]
        signature = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in paths) if self.source == 'math' else tuple(ids)
        if self.pools and self.signature == signature:
            return self.pools
        pools, meta = {}, {}
        for rid in ids:
            if rid not in self.rows:
                raise ValueError('Unknown captured input for round ' + rid)
            row = self.rows[rid]
            action = bytes.fromhex(row['action_hex'])
            if self.source == 'wire':
                raw = bytes.fromhex(row['raw_hex'])
            else:
                value = json.loads((self.directory / (rid + '.json')).read_text())
                if value['roundIndexV2'] != rid:
                    raise ValueError('Math filename and round ID differ')
                raw = math_to_wire(value)
                action = input_for_math(action, value, raw)
            decode_message(fields(raw)[1][1])
            key = action_key(action)
            pools.setdefault(key, []).append(raw)
            meta[key] = {'request': request_to_math(action)}
        if not pools:
            raise ValueError('No valid 573 replay samples')
        for key, pool in pools.items():
            if self.bonus_first and not self.selected:
                pool.sort(key=lambda raw: not any(r['GetBonus'] or r['BonusTotalRound'] > 0
                              for r in decode_message(fields(raw)[1][1])['RoundQueue']))
            meta[key]['sample_count'] = len(pool)
        self.pools, self.metadata, self.signature = pools, meta, signature
        return pools
