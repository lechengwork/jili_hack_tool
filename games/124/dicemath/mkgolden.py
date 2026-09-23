#!/usr/bin/env python3
"""從 ws_session*.jsonl 解出真實對局，產生 testdata/rounds_124.json（adapter 黃金測試用）。

用法：cd games/124/dicemath && python3 mkgolden.py
"""
import json, struct, os

HERE = os.path.dirname(os.path.abspath(__file__))
GAMEDIR = os.path.dirname(HERE)
SESSIONS = ['ws_session1.jsonl', 'ws_session2_map.jsonl', 'ws_session3_multiplayer.jsonl']
OUT = os.path.join(HERE, 'testdata', 'rounds_124.json')


def varint(b, i):
    r = s = 0
    while True:
        x = b[i]; i += 1
        r |= (x & 0x7f) << s
        if not x & 0x80:
            return r, i
        s += 7


def fields(b):
    i, out = 0, []
    while i < len(b):
        try:
            k, i = varint(b, i)
        except IndexError:
            break
        fn, wt = k >> 3, k & 7
        if wt == 0:
            v, i = varint(b, i); out.append((fn, wt, v))
        elif wt == 1:
            out.append((fn, wt, b[i:i + 8])); i += 8
        elif wt == 2:
            ln, i = varint(b, i); out.append((fn, wt, b[i:i + ln])); i += ln
        elif wt == 5:
            out.append((fn, wt, b[i:i + 4])); i += 4
        else:
            break
    return out


def d64(x):
    return struct.unpack('<d', x)[0]


def packed_doubles(b):
    return [struct.unpack('<d', b[i:i + 8])[0] for i in range(0, len(b) - 7, 8)]


def parse_bets(msgs):
    out = []
    for raw in msgs:
        amt, pos = 0.0, 0
        for fn, wt, v in fields(raw):
            if fn == 1 and wt == 1:
                amt = d64(v)
            elif fn == 2 and wt == 0:
                pos = v
        out.append((amt, pos))
    return out


def main():
    rounds = []
    for name in SESSIONS:
        pending = None
        for line in open(os.path.join(GAMEDIR, name)):
            d = json.loads(line)
            if d.get('kind') != 'ws_msg' or not d.get('binary'):
                continue
            b = bytes.fromhex(d['hex'])
            if len(b) < 3:
                continue
            cmd = body = None
            for fn, wt, v in fields(b):
                if fn == 1 and wt == 0:
                    cmd = v
                elif fn == 2 and wt == 2:
                    body = v
            if cmd != 22 or body is None:
                continue
            if d['dir'] == 'SEND':
                pending = parse_bets([v for fn, wt, v in fields(body) if fn == 1 and wt == 2])
                continue
            res, echo, rid = None, [], None
            for fn, wt, v in fields(body):
                if fn == 1 and wt == 2:
                    res = v
                elif fn == 4 and wt == 0:
                    rid = v
                elif fn == 5 and wt == 2:
                    echo.append(v)
            if res is None:
                continue
            win, d1, d2, extra = 0.0, 0, 0, []
            for fn, wt, v in fields(res):
                if fn == 1 and wt == 1:
                    win = d64(v)
                elif fn == 2 and wt == 0:
                    d1 = v
                elif fn == 3 and wt == 0:
                    d2 = v
                elif fn == 5 and wt == 2:
                    extra = packed_doubles(v)
            bets = parse_bets(echo) or pending or []
            arr = [0.0] * 13
            for amt, pos in bets:
                arr[pos] += amt
            rounds.append(dict(source=name, roundId=rid, die1=d1, die2=d2,
                               betsPkt=arr, extraPkt=[int(x) for x in extra],
                               totalWin=win))
            pending = None

    out = {
        "_readme": "JILI 124 (7up7down) 真實對局實測資料，供 adapter 黃金測試使用。"
                   "所有陣列都是【封包順序】(0=和,1=小,2=大,3..12=點數2,3,4,5,6,8,9,10,11,12)。"
                   "金額單位是元(double)，測試裡會 x10000 轉成 db point。",
        "_source": "games/124/ws_session*.jsonl，由 mkgolden.py 產生",
        "baseOddsPkt": [4, 1, 1, 26, 12, 8, 6, 5, 5, 6, 8, 12, 26],
        "rounds": rounds,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
    print(f'wrote {OUT} ({len(rounds)} rounds)')


if __name__ == '__main__':
    main()
