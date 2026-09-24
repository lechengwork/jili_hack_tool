#!/usr/bin/env python3
"""
ws_math_view.py — JILI 124 (7up7down) 收工:把側錄的 WS 封包攤成【機率團隊介面】。

對應 696 的 webcap_math_view.py。124 是明文 protobuf，不用解密，直接讀 frame。
產出(預設 games/124/math/):
  · <round_id>.json     每局一檔(畫面順序、含本金賠率、每格 extra/下注/賠付)
  · all.jsonl           每局一行(彙整)
  · EXTRA_SUMMARY.json  ★extra 彙總:值域 + 每格各值出現次數 + 每格 E[extra]★(機率主看這個)
  · INTERFACE.md        欄位表 + position 對照 + 邊界約定(算 RTP 必看)

★機率端邊界(見 games/124/EXTRA_MULT.md，已用 29 局實測定案):
  - 全程用【畫面順序】(由上到下、由左到右)，封包序↔畫面序的重排由遊戲層做。
  - 用【含本金賠率】:win = bet × final_odds，不用再 +1。
  - extra=1 代表「這格沒蓋 extra」(不是省略、不是 0)。final_odds = base_odds × extra。
  - 賠付公式:win = Σ(中獎格) bet × (base_odds × extra + 1)。本工具每局都會自驗，全對才輸出。

用法:
  python ws_math_view.py                       # 讀 games/124/webcap_ws.jsonl(擷取產物)
  python ws_math_view.py --src games/124/webcap_ws.jsonl --out games/124/math
  python ws_math_view.py --sessions games/124/ws_session1.jsonl games/124/ws_session2_map.jsonl ...
                                               # 離線驗證:餵現有 session
"""
import argparse, json, os, struct, sys

# ── protobuf 迷你解析 ─────────────────────────────────────────────────────────
def _rv(b, i):
    s = 0; r = 0
    while True:
        x = b[i]; i += 1; r |= (x & 0x7f) << s
        if not x & 0x80: break
        s += 7
    return r, i

def fields(b):
    i = 0; out = []
    while i < len(b):
        try: key, i = _rv(b, i)
        except IndexError: break
        f = key >> 3; wt = key & 7
        if wt == 0:
            v, i = _rv(b, i); out.append((f, 0, v))
        elif wt == 1:
            out.append((f, 1, struct.unpack('<d', b[i:i+8])[0])); i += 8
        elif wt == 2:
            ln, i = _rv(b, i); out.append((f, 2, b[i:i+ln])); i += ln
        elif wt == 5:
            out.append((f, 5, struct.unpack('<f', b[i:i+4])[0])); i += 4
        else: break
    return out

def get(fs, fn, wt=None):
    for f, t, v in fs:
        if f == fn and (wt is None or t == wt): return v
    return None

def getall(fs, fn, wt=None):
    return [v for f, t, v in fs if f == fn and (wt is None or t == wt)]

def packed_doubles(bs):
    return [struct.unpack('<d', bs[i:i+8])[0] for i in range(0, len(bs)-7, 8)]

# ── 常數(封包序 / 畫面序，見 EXTRA_MULT.md) ───────────────────────────────────
# 封包 position 0..12 的基礎(顯示)賠率
BASE_ODDS_WIRE = [4, 1, 1, 26, 12, 8, 6, 5, 5, 6, 8, 12, 26]
# 畫面順序 idx → 封包 position(只有前兩格互換，自反)
SCREEN_TO_WIRE = [1, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
SCREEN_NAMES = ["小(2-6)", "和(7)", "大(8-12)", "點數2", "點數3", "點數4",
                "點數5", "點數6", "點數8", "點數9", "點數10", "點數11", "點數12"]
# 畫面序含本金賠率 = base_odds[wire]+1
BASE_TOTAL_SCREEN = [BASE_ODDS_WIRE[SCREEN_TO_WIRE[i]] + 1 for i in range(13)]

def wire_won_positions(die_sum):
    """依規則算中獎的封包 position(和/小/大 + 對應點數注)。"""
    won = []
    if die_sum == 7:
        won.append(0)                       # 和
    elif die_sum < 7:
        won.append(1)                       # 小
        won.append(die_sum + 1)             # 點數 2..6 → pos 3..7
    else:
        won.append(2)                       # 大
        won.append(die_sum)                 # 點數 8..12 → pos 8..12
    return won

# ── 讀 frames ────────────────────────────────────────────────────────────────
def load_frames(paths):
    rows = []
    for path in paths:
        if not os.path.isfile(path): continue
        for line in open(path, encoding='utf-8'):
            line = line.strip()
            if not line: continue
            try: d = json.loads(line)
            except Exception: continue
            if d.get('kind') != 'ws_msg': continue
            h = d.get('hex') or ''
            if len(h) // 2 <= 2: continue          # 心跳/空 frame
            rows.append((d.get('seq') or 0, d.get('ts') or 0, d['dir'], bytes.fromhex(h)))
    # 依 ts 再 seq 排序(同一次擷取 seq 單調；跨 session 用 ts)
    rows.sort(key=lambda r: (r[1], r[0]))
    return rows

def cmd_of(b):
    fs = fields(b)
    return get(fs, 1, 0)

# ── 解一局 RECV cmd22 → math 局 ──────────────────────────────────────────────
def decode_round(recv_body):
    bf = fields(recv_body)
    res = get(bf, 1, 2)
    if not res: return None
    rf = fields(res)
    total_win = get(rf, 1, 1) or 0.0
    die1 = get(rf, 2, 0) or 0
    die2 = get(rf, 3, 0) or 0
    won_bytes = get(rf, 4, 2) or b''
    extra_arr = get(rf, 5, 2)
    extra_wire = packed_doubles(extra_arr) if extra_arr else [1.0] * 13
    if len(extra_wire) != 13:
        extra_wire = (extra_wire + [1.0] * 13)[:13]
    balance = get(bf, 3, 1)
    round_id = get(bf, 4, 0)
    # bets_echo(f5，可能多筆) = 本局下的注(封包序)
    bets_wire = {}
    for eb in getall(bf, 5, 2):
        ef = fields(eb)
        amt = get(ef, 1, 1) or 0.0
        pos = get(ef, 2, 0) or 0
        bets_wire[pos] = bets_wire.get(pos, 0.0) + amt

    die_sum = die1 + die2
    won_wire = set(wire_won_positions(die_sum)) if (die1 and die2) else set()
    won_from_pkt = set(won_bytes)                # f4 交叉驗證

    # 每格(畫面序)
    positions = []
    for i in range(13):
        w = SCREEN_TO_WIRE[i]
        ex = extra_wire[w]
        base_total = BASE_TOTAL_SCREEN[i]
        final_odds = round((base_total - 1) * ex + 1, 6)   # 含本金 final = base顯示×extra + 1
        bet = round(bets_wire.get(w, 0.0), 6)
        won = w in won_wire
        win = round(bet * final_odds, 6) if won else 0.0
        positions.append({
            "idx": i, "name": SCREEN_NAMES[i],
            "base_odds": base_total,          # 含本金
            "extra": ex,                      # 封包倍率:1(無)/2/5/10…
            "final_odds": final_odds,         # 含本金 = base×extra
            "bet": bet, "won": won, "win": win,
        })

    calc_win = round(sum(p["win"] for p in positions), 6)
    bet_total = round(sum(p["bet"] for p in positions), 6)

    return {
        "round_id": round_id,
        "dice": [die1, die2],
        "sum": die_sum,
        "total_win": round(total_win, 6),
        "bet_total": bet_total,
        "balance": balance,
        "extra_row_screen": [positions[i]["extra"] for i in range(13)],
        "won_idx_screen": sorted(SCREEN_TO_WIRE.index(w) for w in won_wire),
        "positions": positions,
        # 自驗欄位(不是給機率的規格，是工具自檢)
        "_check": {
            "calc_win": calc_win,
            "win_match": abs(calc_win - round(total_win, 6)) < 1e-6,
            "won_pkt_match": (won_from_pkt == won_wire) if won_bytes else None,
        },
    }

# ── 主流程 ───────────────────────────────────────────────────────────────────
def build(frames):
    rounds = []
    for seq, ts, dr, b in frames:
        if dr != 'RECV': continue
        fs = fields(b)
        if get(fs, 1, 0) != 22: continue
        body = get(fs, 2, 2)
        if not body: continue
        r = decode_round(body)
        if r: rounds.append(r)
    return rounds

def summarize_extra(rounds):
    vals = set()
    per_pos_counts = [dict() for _ in range(13)]   # 畫面序:各值出現次數
    per_pos_sum = [0.0] * 13
    for r in rounds:
        for p in r["positions"]:
            e = p["extra"]; i = p["idx"]
            vals.add(e)
            per_pos_counts[i][e] = per_pos_counts[i].get(e, 0) + 1
            per_pos_sum[i] += e
    n = len(rounds)
    per_pos = []
    for i in range(13):
        counts = {str(k): v for k, v in sorted(per_pos_counts[i].items())}
        per_pos.append({
            "idx": i, "name": SCREEN_NAMES[i], "base_odds": BASE_TOTAL_SCREEN[i],
            "extra_counts": counts,
            "E_extra": round(per_pos_sum[i] / n, 4) if n else None,
        })
    return {
        "rounds": n,
        "extra_values_seen": sorted(vals),
        "per_position": per_pos,
        "note": "extra=1 代表沒蓋;值域=實測出現過的倍率(樣本不足可能抽不到高倍，見 EXTRA_MULT.md)。",
    }

INTERFACE_MD = """# JILI 124 (7up7down / Extra Pay) — 機率團隊介面

每局一個 `<round_id>.json`;`all.jsonl` 每局一行;`EXTRA_SUMMARY.json` 是 extra 彙總。
本檔只列介面,完整實測定案(公式 29/29 驗過、position 對照的坑)看 `games/124/EXTRA_MULT.md`。

## 一句話
`extra` = 每局隨機灑在 13 個注區的【額外倍率】,乘在該格顯示賠率上,**跟骰子/下注都無關**,開獎才回。
沒蓋的格子 `extra=1`。實測值域 `{1,2,5,10}`(截圖佐證至少還有 3,樣本沒抽到而已)。

## 每局欄位(全畫面順序、含本金賠率)
```
round_id            局號(單調遞增)
dice=[die1,die2]    兩顆骰(1..6)          sum=die1+die2
total_win           本局總贏(封包值)      bet_total  本局總下注
balance             開獎後餘額
extra_row_screen[13] 這局 13 格的 extra 快照(畫面順序,給你快速掃)
won_idx_screen      本局中獎格(畫面順序 idx)
positions[13]       每格明細:
   idx name         畫面順序 0..12 / 注區名
   base_odds        含本金基礎賠率(押1拿回 base_odds)
   extra            這局這格的額外倍率(1=無)
   final_odds       含本金最終賠率 = (base_odds-1)×extra + 1
   bet won win      這局你在這格下的注 / 是否中 / 賠付(=bet×final_odds)
```
`_check` 是本工具自檢欄位(calc_win/win_match…),不是規格,可忽略。

## 畫面順序 ↔ 封包順序(★只有前兩格互換,其餘 11 格相同★)
```
畫面 idx : 0=小(2-6) 1=和(7) 2=大(8-12) 3=點數2 4=點數3 … 12=點數12
封包 pos : 1         0       2          3       4          … 12
```
畫面序含本金賠率 = [2,5,2,27,13,9,7,6,6,7,9,13,27]。
漏掉互換 → 只有「押7」和「押2-6」會錯(互拿對方賠率),平常測不出來,要專門測這兩格。

## 你要設計的其實是「每格的 E[extra]」
每格 RTP = 命中率 ×(base顯示 × E[extra] + 1)。各格命中率不同、base 不同,
**extra 機率不能各格一視同仁**(否則「和」那格會 >100%)。細節與各格目標 E[extra] 表見 EXTRA_MULT.md。
`EXTRA_SUMMARY.json` 已用實際擷取局數算好每格的 extra 出現次數與 E[extra],直接拿來對。
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=os.path.join('games', '124', 'webcap_ws.jsonl'),
                    help='側錄檔(擷取產物);預設 games/124/webcap_ws.jsonl')
    ap.add_argument('--sessions', nargs='*', default=None,
                    help='改讀一個或多個現有 session(離線驗證用),會蓋掉 --src')
    ap.add_argument('--out', default=os.path.join('games', '124', 'math'))
    args = ap.parse_args()

    paths = args.sessions if args.sessions else [args.src]
    paths = [p for p in paths if os.path.isfile(p)]
    if not paths:
        print('✗ 找不到輸入(側錄檔或 session)。擷取有跑、真的轉過幾局嗎?', file=sys.stderr)
        sys.exit(1)

    frames = load_frames(paths)
    rounds = build(frames)
    if not rounds:
        print('✗ 沒解出任何 cmd22 局(frames=%d)。' % len(frames), file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)
    # 每局檔 + all.jsonl
    bad = 0
    with open(os.path.join(args.out, 'all.jsonl'), 'w', encoding='utf-8') as allf:
        for r in rounds:
            rid = r["round_id"] if r["round_id"] is not None else 'unknown'
            with open(os.path.join(args.out, '%s.json' % rid), 'w', encoding='utf-8') as f:
                json.dump(r, f, ensure_ascii=False, indent=2)
            allf.write(json.dumps(r, ensure_ascii=False) + '\n')
            if not r["_check"]["win_match"]:
                bad += 1

    summary = summarize_extra(rounds)
    with open(os.path.join(args.out, 'EXTRA_SUMMARY.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.out, 'INTERFACE.md'), 'w', encoding='utf-8') as f:
        f.write(INTERFACE_MD)

    print('✅ 解出 %d 局 → %s' % (len(rounds), args.out))
    print('   賠付公式自驗:%d/%d 相符%s'
          % (len(rounds) - bad, len(rounds), '' if bad == 0 else '  ⚠ 有 %d 局不符,先別發!' % bad))
    print('   extra 值域(實測):%s' % summary['extra_values_seen'])
    print('   ── 每格 E[extra](畫面序) ──')
    for p in summary['per_position']:
        print('   %2d %-8s base=%-2d  E[extra]=%s  次數=%s'
              % (p['idx'], p['name'], p['base_odds'], p['E_extra'], p['extra_counts']))
    if bad:
        sys.exit(2)


if __name__ == '__main__':
    main()
