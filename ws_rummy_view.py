#!/usr/bin/env python3
"""
ws_rummy_view.py — JILI Rummy(遊戲號 94) WS 封包 → 每局完整 JSON。

讀 games/<GID>/traffic.jsonl(或 --src 指定的 webcap_ws.jsonl),依 games/94/ws_rummy.proto
把明文 protobuf 解成：發牌 / 動作序列(摸/棄/撿) / 結算(亮牌組合+分數) / 金流。

用法:
  ./.venv/bin/python ws_rummy_view.py 94
  ./.venv/bin/python ws_rummy_view.py 94 --src games/94/traffic.jsonl --out games/94/math

輸出:
  games/94/math/<round_id>.json   每局一檔(完整可讀)
  games/94/math/all.jsonl         每局一行(跑統計用)
"""
import argparse, json, struct, sys
from pathlib import Path

# ── 通用 protobuf 讀取 ────────────────────────────────────────────────
def _rv(b, i):
    s = v = 0
    while True:
        x = b[i]; i += 1; v |= (x & 0x7f) << s
        if not x & 0x80: break
        s += 7
    return v, i

def fields(b):
    """回傳 [(fnum, wtype, raw)]；wt0=varint(int) wt1=8B wt2=bytes wt5=4B。"""
    i = 0; out = []
    try:
        while i < len(b):
            key, i = _rv(b, i); fn = key >> 3; wt = key & 7
            if wt == 0:   v, i = _rv(b, i); out.append((fn, 0, v))
            elif wt == 1: out.append((fn, 1, b[i:i+8])); i += 8
            elif wt == 2: ln, i = _rv(b, i); out.append((fn, 2, b[i:i+ln])); i += ln
            elif wt == 5: out.append((fn, 5, b[i:i+4])); i += 4
            else: break
    except Exception:
        pass
    return out

def get(fs, fnum):
    for fn, wt, v in fs:
        if fn == fnum: return (wt, v)
    return None

def getall(fs, fnum):
    return [(wt, v) for fn, wt, v in fs if fn == fnum]

def as_f64(v):
    return struct.unpack('<d', v)[0] if isinstance(v, (bytes, bytearray)) and len(v) == 8 else None

def envelope(b):
    """Envelope{f1=cmd, f2=body}。cmd 省略→0。"""
    cmd = 0; body = b''
    for fn, wt, v in fields(b):
        if fn == 1 and wt == 0: cmd = v
        elif fn == 2 and wt == 2: body = v
    return cmd, body

# ── 牌 ────────────────────────────────────────────────────────────────
# suit: 0..3 = 四個真花色(對真實 ♣♦♥♠ 的順序【待確認】,int 才是權威);4 = 印牌鬼牌(PJ) 佔位
_SUIT = {0: '♣', 1: '♦', 2: '♥', 3: '♠', 4: 'PJ'}
_RANK = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}

def card(b):
    """Card{f1=suit, f2=rank, f4=joker}。回 dict(含 raw int + label)。"""
    fs = fields(b); s = r = 0; j = 0
    for fn, wt, v in fs:
        if fn == 1 and wt == 0: s = v
        elif fn == 2 and wt == 0: r = v
        elif fn == 4 and wt == 0: j = v
    if s == 4:                       # 印牌鬼牌:花色是佔位,rank 無意義
        label = 'PJ' + ('*' if j else '')
    else:
        label = f"{_SUIT.get(s, '?')}{_RANK.get(r, r)}" + ('*' if j else '')
    return {"suit": s, "rank": r, "joker": bool(j), "label": label}

def _is_card(v):
    """真的是一張牌 = 有 rank 欄(f2);排除只有 f1 的分組計數 trailer(如 {f1=4})。"""
    fs = fields(v)
    return any(fn == 2 and wt == 0 for fn, wt, _ in fs)

def card_list(b):
    """牌串 = message{ repeated f1: Card }。回 [card,...](濾掉無 rank 的 trailer)。"""
    return [card(v) for wt, v in getall(fields(b), 1) if wt == 2 and _is_card(v)]

# ── 各 cmd 解 ─────────────────────────────────────────────────────────
def parse_deal(body):
    fs = fields(body)
    rid = ''
    g1 = get(fs, 1)
    if g1 and g1[0] == 2:
        try: rid = g1[1].decode('utf-8')
        except Exception: rid = g1[1].hex()
    seats = []
    for wt, v in getall(fs, 3):
        if wt != 2: continue
        sf = fields(v); seat = 0; acct = ''; amt = None
        for fn, w, val in sf:
            if fn == 1 and w == 0: seat = val
            elif fn == 2 and w == 2:
                try: acct = val.decode('utf-8')
                except Exception: acct = val.hex()
            elif fn == 4 and w == 1: amt = as_f64(val)
        seats.append({"seat": seat, "account": acct, "amount": amt})
    def _card_field(n):
        g = get(fs, n)
        return card(g[1]) if g and g[0] == 2 else None
    g11 = get(fs, 11)
    g12 = get(fs, 12)
    hand = card_list(g12[1]) if g12 and g12[0] == 2 else []
    melds = [card_list(v) for wt, v in getall(fs, 13) if wt == 2]
    return {
        "round_id": rid,
        "seats": seats,
        "wild_joker": _card_field(8),
        "open_top": _card_field(9),
        "stock_start": g11[1] if g11 and g11[0] == 0 else None,
        "your_hand": hand,
        "your_hand_count": len(hand),
        "your_melds_init": [m for m in melds if m],
    }

def parse_settlement(body):
    fs = fields(body)
    results = []
    for wt, v in getall(fs, 1):
        if wt != 2: continue
        pf = fields(v)
        g1 = get(pf, 1); g2 = get(pf, 2)
        seat = g1[1] if g1 and g1[0] == 0 else 0      # proto3 省略 0 → 你(座位0)
        score = g2[1] if g2 and g2[0] == 0 else 0     # 省略 → 0 分 = 贏家
        melds = [card_list(mv) for mw, mv in getall(pf, 4) if mw == 2]
        results.append({"seat": seat, "score": score, "melds": [m for m in melds if m]})
    gb = get(fs, 3)
    return {"results": results, "balance": as_f64(gb[1]) if gb and gb[0] == 1 else None}

def parse_action(cmd, dir_, body):
    """摸/棄/撿動作 → 精簡事件。"""
    fs = fields(body)
    ev = {"cmd": cmd, "dir": dir_}
    def iv(n):
        g = get(fs, n); return g[1] if g and g[0] == 0 else None
    def cv(n):
        g = get(fs, n); return card(g[1]) if g and g[0] == 2 and fields(g[1]) else None
    if cmd == 13:      # 摸閉牌堆
        ev.update(type="draw_closed", seat=iv(1), card=cv(3), stock=iv(9))
    elif cmd == 14:    # 棄牌到開牌堆
        ev.update(type="discard", seat=iv(1), card=cv(2), stock=iv(8))
    elif cmd == 15:    # 撿開牌堆頂
        ev.update(type="draw_open", picked=cv(4), stock=iv(10))
    elif cmd == 16:    # 你棄牌(SEND 指定 {suit,rank};RECV 更新)
        if dir_ == "SEND":
            s = iv(1) or 0; r = iv(2) or 0
            lbl = 'PJ' if s == 4 else f"{_SUIT.get(s,'?')}{_RANK.get(r, r)}"
            ev.update(type="my_discard", card={"suit": s, "rank": r, "label": lbl})
        else:
            ev.update(type="my_discard_ack", stock=iv(7))
    return ev

# ── 每局組裝 ──────────────────────────────────────────────────────────
def build_hands(frames):
    """frames = [(idx,dir,cmd,body)]。以 RECV cmd12 為界切局。"""
    starts = [k for k, f in enumerate(frames) if f[1] == "RECV" and f[2] == 12]
    hands = []
    for hi, s in enumerate(starts):
        e = starts[hi+1] if hi+1 < len(starts) else len(frames)
        seg = frames[s:e]
        deal = parse_deal(seg[0][3])
        actions = []; settle = None; end_balance = None
        for idx, d, cmd, body in seg:
            if cmd in (13, 14, 15, 16):
                a = parse_action(cmd, d, body)
                # 只留帶資訊的(過濾純 2B 請求空殼)
                if any(a.get(k) is not None for k in ("card", "picked", "seat", "stock")):
                    a["i"] = idx; actions.append(a)
            elif cmd == 17 and d == "RECV":
                settle = parse_settlement(body)
            elif cmd == 19 and d == "RECV":
                gb = get(fields(body), 3)
                end_balance = as_f64(gb[1]) if gb and gb[0] == 1 else None
        you = next((s for s in deal["seats"] if s["account"] and not s["account"].startswith("*")), None)
        start_bal = you["amount"] if you else None
        hand = {
            "round_id": deal["round_id"],
            "you": you["account"] if you else None,
            "start_balance": start_bal,
            "seats": deal["seats"],
            "wild_joker": deal["wild_joker"],
            "open_top": deal["open_top"],
            "stock_start": deal["stock_start"],
            "your_hand": deal["your_hand"],
            "your_hand_count": deal["your_hand_count"],
            "your_melds_init": deal["your_melds_init"],
            "actions": actions,
            "action_count": len(actions),
            "settlement": settle,
            "end_balance": end_balance if end_balance is not None else (settle or {}).get("balance"),
        }
        if start_bal is not None and hand["end_balance"] is not None:
            hand["balance_delta"] = round(hand["end_balance"] - start_bal, 4)
        # ── 分類本局結果(你=座位0):win/first_drop/middle_drop/full_count/loss/partial ──
        _res = (settle or {}).get("results") or []
        _you = next((r for r in _res if r.get("seat") == 0), None)
        _bd = hand.get("balance_delta")
        if _res:                                   # 有結算 = 你打到最後 / 撿尾
            _ys = _you["score"] if _you else None
            if _ys == 0:          hand["outcome"], hand["your_points"] = "win", 0
            elif _ys == 80:       hand["outcome"], hand["your_points"] = "full_count", 80
            elif _ys is not None: hand["outcome"], hand["your_points"] = "loss", _ys
            else:                 hand["outcome"], hand["your_points"] = "loss", None
        elif _bd is None:                          # 無結算也無 cmd19 餘額 = 擷取中斷
            hand["outcome"], hand["your_points"] = "partial", None
        else:                                      # 無結算但有餘額 = 你放棄離桌
            _pts = round(-_bd / 0.2)
            hand["outcome"] = {20: "first_drop", 40: "middle_drop"}.get(_pts, "drop")
            hand["your_points"] = _pts
        hands.append(hand)
    return hands

# ── 主程式 ────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gid", nargs="?", default="94")
    ap.add_argument("--src", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    src = Path(args.src) if args.src else Path(f"games/{args.gid}/traffic.jsonl")
    out = Path(args.out) if args.out else Path(f"games/{args.gid}/math")
    if not src.exists():
        sys.exit(f"✗ 找不到來源:{src}")
    out.mkdir(parents=True, exist_ok=True)

    frames = []
    for line in src.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        if r.get("kind") == "ws_msg" and r.get("binary") and r.get("hex"):
            b = bytes.fromhex(r["hex"]); cmd, body = envelope(b)
            frames.append((len(frames), r.get("dir"), cmd, body))
        elif r.get("dir") and r.get("hex"):   # webcap_ws.jsonl 形狀(無 kind)
            b = bytes.fromhex(r["hex"]); cmd, body = envelope(b)
            frames.append((len(frames), r.get("dir"), cmd, body))

    hands = build_hands(frames)
    # 本次 session 每局寫檔(檔名=round_id → 跨 session 自然累積,不覆蓋舊局)
    for idx, h in enumerate(hands):
        rid = h["round_id"] or ("hand%d" % idx)
        (out / f"{rid}.json").write_text(
            json.dumps(h, ensure_ascii=False, indent=2), encoding="utf-8")
    # 重建 all.jsonl = out 底下【所有】每局檔(跨 session 累積,依 round_id 去重排序)
    acc = {}
    for jf in sorted(out.glob("*.json")):
        try:
            o = json.loads(jf.read_text(encoding="utf-8"))
            if isinstance(o, dict) and o.get("round_id"):
                acc[o["round_id"]] = o
        except Exception:
            pass
    with open(out / "all.jsonl", "w", encoding="utf-8") as af:
        for rid in sorted(acc):
            af.write(json.dumps(acc[rid], ensure_ascii=False) + "\n")

    print(f"✓ 本次解出 {len(hands)} 局;all.jsonl 累積 {len(acc)} 局 → {out}/")
    for h in hands:
        s = h["settlement"] or {}
        winner = None
        if s.get("results"):
            winner = min((r for r in s["results"] if r.get("score") is not None),
                         key=lambda r: r["score"], default=None)
        print(f"  局 {h['round_id']}: 手牌{h['your_hand_count']}張 "
              f"鬼牌={h['wild_joker']['label'] if h['wild_joker'] else '?'} "
              f"動作{h['action_count']} "
              f"結算{len(s.get('results',[]))}家 "
              f"最低分家=座位{winner['seat'] if winner else '?'}(score={winner['score'] if winner else '?'}) "
              f"餘額Δ={h.get('balance_delta','?')}")

if __name__ == "__main__":
    main()
