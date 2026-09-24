#!/usr/bin/env python3
"""ws_live.py — JILI 124 (7up7down) 即時逐局解碼(精簡標準格式)+ 每局存一筆。

跟隨(tail)側錄檔 games/124/webcap_ws.jsonl,每個【開獎 frame(cmd22 RECV)】就:
  ① 印出該局(下面這個格式,封包序 13 格):
       { "source", "roundId", "die1", "die2", "betsPkt"[13], "extraPkt"[13], "totalWin" }
  ② 存一筆:games/124/ws_rounds/<roundId>.json(同格式,另含 rawHex)

  betsPkt[pos] = 該注點(封包序 0..12)這局下的金額(沒下=0)
  extraPkt[pos]= 該注點這局的額外倍率(1=無,2/5/10…)

用法:
  python ws_live.py            # 跟隨(邊玩邊看),Ctrl+C 停
  python ws_live.py --once     # 只處理現有側錄檔一次,不跟隨
env: WS_SRC(側錄檔,預設 games/124/webcap_ws.jsonl)  WS_OUT(每局輸出目錄,預設 games/124/ws_rounds)
"""
import json, struct, os, sys, time

def _rv(b, i):
    s = 0; r = 0
    while True:
        x = b[i]; i += 1; r |= (x & 0x7f) << s
        if not x & 0x80: break
        s += 7
    return r, i

def fields(b):
    """generic protobuf → list of (field, wtype, value);wt2 回原始 bytes。"""
    i = 0; out = []; n = len(b)
    while i < n:
        try: key, i = _rv(b, i)
        except Exception: break
        f = key >> 3; wt = key & 7
        try:
            if wt == 0:
                v, i = _rv(b, i); out.append((f, 0, v))
            elif wt == 1:
                out.append((f, 1, struct.unpack('<d', b[i:i + 8])[0])); i += 8
            elif wt == 2:
                ln, i = _rv(b, i); out.append((f, 2, bytes(b[i:i + ln]))); i += ln
            elif wt == 5:
                out.append((f, 5, struct.unpack('<f', b[i:i + 4])[0])); i += 4
            else: break
        except Exception:
            break
    return out

def get(fs, fn, wt=None):
    for f, t, v in fs:
        if f == fn and (wt is None or t == wt): return v
    return None

def getall(fs, fn, wt=None):
    return [v for f, t, v in fs if f == fn and (wt is None or t == wt)]

def packed_doubles(bs):
    return [struct.unpack('<d', bs[i:i + 8])[0] for i in range(0, len(bs) - 7, 8)]

def build_round(raw, source):
    """RECV cmd22 frame → 精簡標準格式 dict;非遊戲局回 None。"""
    fs = fields(raw)
    if get(fs, 1, 0) != 22: return None                 # f1 = cmd,只要 22
    body = get(fs, 2, 2)
    if not body: return None
    bf = fields(body)
    res = get(bf, 1, 2)                                  # body.f1 = Result
    if not res: return None
    rf = fields(res)
    die1 = get(rf, 2, 0); die2 = get(rf, 3, 0)          # Result.f2/f3 = 骰子
    if not (isinstance(die1, int) and isinstance(die2, int) and 1 <= die1 <= 6 and 1 <= die2 <= 6):
        return None
    total_win = get(rf, 1, 1) or 0.0                     # Result.f1 = total_win(贏才有)
    extra_arr = get(rf, 5, 2)                            # Result.f5 = packed double[13] 額外倍率
    extra = packed_doubles(extra_arr) if extra_arr else [1.0] * 13
    extra = (extra + [1.0] * 13)[:13]
    extraPkt = [int(e) if e == int(e) else e for e in extra]
    bets = [0.0] * 13                                    # body.f5 = repeated Bet → 攤成 13 格
    for eb in getall(bf, 5, 2):
        ef = fields(eb)
        amt = get(ef, 1, 1) or 0.0
        pos = get(ef, 2, 0) or 0
        if isinstance(pos, int) and 0 <= pos < 13:
            bets[pos] = round(bets[pos] + amt, 6)
    return {
        "source": source,
        "roundId": get(bf, 4, 0),                        # body.f4 = round_id
        "die1": die1,
        "die2": die2,
        "betsPkt": bets,
        "extraPkt": extraPkt,
        "totalWin": round(total_win, 6),
    }

def main():
    src = os.environ.get('WS_SRC') or os.path.join('games', '124', 'webcap_ws.jsonl')
    outdir = os.environ.get('WS_OUT') or os.path.join('games', '124', 'ws_rounds')
    once = '--once' in sys.argv
    source = os.path.basename(src)
    os.makedirs(outdir, exist_ok=True)
    seen = set()

    def handle(line):
        try: d = json.loads(line)
        except Exception: return
        if d.get('dir') != 'RECV': return
        try: raw = bytes.fromhex(d.get('hex', ''))
        except Exception: return
        r = build_round(raw, source)
        if not r: return
        rid = str(r['roundId'])
        if rid in seen: return
        seen.add(rid)
        rec = dict(r); rec['rawHex'] = d.get('hex')
        with open(os.path.join(outdir, rid + '.json'), 'w', encoding='utf-8') as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        print(json.dumps(r, ensure_ascii=False, indent=2) + ',', flush=True)

    print(f"[ws_live] 讀 {src} → 每局印出+存 {outdir}{os.sep}<roundId>.json ;Ctrl+C 停", flush=True)
    print("─" * 60, flush=True)

    if once:
        if os.path.exists(src):
            with open(src, encoding='utf-8') as f:
                for ln in f: handle(ln)
        print(f"\n[ws_live] 共 {len(seen)} 局", flush=True)
        return

    pos = 0
    try:
        while True:
            if os.path.exists(src):
                sz = os.path.getsize(src)
                if sz < pos:
                    pos = 0; seen.clear()
                    print("\n[ws_live] 偵測到新一場擷取,重新開始\n" + "─" * 60, flush=True)
                with open(src, encoding='utf-8') as f:
                    f.seek(pos)
                    while True:
                        ln = f.readline()
                        if not ln: break
                        handle(ln)
                    pos = f.tell()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print(f"\n[ws_live] 停。本場共 {len(seen)} 局。", flush=True)

if __name__ == '__main__':
    main()
