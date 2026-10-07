#!/usr/bin/env python3
"""
ws_fish736_view.py — JILI Jackpot Fishing 2(遊戲號 736) WS 封包 → 每發 math JSON + session 統計。

魚機(連續射擊,非回合制)。讀 games/<GID>/traffic.jsonl(或 --src 指定的 webcap_ws.jsonl),
依 games/736/ws_fish736.proto 把明文 protobuf 解成:每發開砲的成本/捕獲/配當/餘額。

★金流模型(實測,見 games/736/WS_PROTOCOL.md)★
  · 每發成本 cost = bet(f2.f3) × power(砲台倍率;由 cmd25.f2.f2 決定)
  · 捕獲配當 payout = bet × 魚倍率M(M=payout/bet 為乾淨整數)
  · 餘額 = 前餘額 − cost + payout(miss 則 payout=0);★按 bullet_id 排序才會鏈對★
  · cmd24 = 作廢的一發(server 處理時魚已不在)→ 金流淨 0,RTP 排除
  · RTP = Σpayout / Σcost
power_map(f2.f2 → 倍數)會【自動從本 session 的 miss 餘額差校正】,
  不寫死,以容納更多砲台等級;無法校正時退回內建 {None:1, 1:1, 6:5}。

用法:
  ./.venv/bin/python ws_fish736_view.py 736
  ./.venv/bin/python ws_fish736_view.py 736 --src games/736/traffic.jsonl --out games/736/math

輸出:
  games/736/math/shots.jsonl    每發一行(bullet_id/cost/bet/power/fish/payout/mult/balance/voided)
  games/736/math/summary.json   Σcost/Σpayout/RTP/倍率直方圖/power直方圖/彩金池/拾取…
  games/736/math/INTERFACE.md   給機率團隊的欄位與金流說明
"""
import argparse, json, struct, sys, collections
from pathlib import Path

# ── 通用 protobuf ────────────────────────────────────────────────────────
def _rv(b, i):
    s = v = 0
    while True:
        x = b[i]; i += 1; v |= (x & 0x7f) << s
        if not x & 0x80: break
        s += 7
    return v, i

def fields(b):
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

def sub_i(fs, fnum):
    g = get(fs, fnum); return g[1] if g and g[0] == 0 else None

def sub_f(fs, fnum):
    g = get(fs, fnum); return as_f64(g[1]) if g and g[0] == 1 else None

def sub_b(fs, fnum):
    g = get(fs, fnum); return g[1] if g and g[0] == 2 else None

def envelope(b):
    cmd = None; body = b''
    for fn, wt, v in fields(b):
        if fn == 1 and wt == 0: cmd = v
        elif fn == 2 and wt == 2: body = v
    return cmd, body

# ── frame 載入 ────────────────────────────────────────────────────────────
def load_frames(src):
    frames = []
    for line in Path(src).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except Exception: continue
        hx = r.get("hex")
        is_ws = (r.get("kind") == "ws_msg") or (r.get("dir") and hx is not None)
        if not is_ws or not hx: continue
        b = bytes.fromhex(hx)
        if len(b) < 2: continue
        cmd, body = envelope(b)
        frames.append((len(frames), r.get("dir"), cmd, body, b))
    return frames

# ── 握手歡迎幀(無 cmd envelope):玩家/餘額/幣別/下注級距 ────────────────
def parse_welcome(b):
    fs = fields(b)
    info = {}
    g3 = get(fs, 3)
    if g3 and g3[0] == 2:
        f3 = fields(g3[1])
        acct = sub_b(f3, 2)
        if acct:
            try: info["account"] = acct.decode("utf-8")
            except Exception: info["account"] = acct.hex()
        g4 = get(f3, 4)
        if g4 and g4[0] == 2:
            f4 = fields(g4[1])
            info["start_balance"] = sub_f(f4, 2)
            cur = sub_b(f4, 5)
            if cur:
                try: info["currency"] = cur.decode("utf-8")
                except Exception: pass
    g8 = get(fs, 8)
    if g8 and g8[0] == 2:
        inner = sub_b(fields(g8[1]), 3)
        if inner:
            info["bet_ladder"] = [round(struct.unpack('<d', inner[i:i+8])[0], 4)
                                  for i in range(0, len(inner) - 7, 8)]
    return info

# ── cmd25 / cmd24 解析 ─────────────────────────────────────────────────────
def parse_shot(cmd, body):
    """RECV cmd25(結算) / cmd24(作廢) → dict。"""
    fs = fields(body)
    if cmd == 25:
        g2 = get(fs, 2); f2 = fields(g2[1]) if g2 and g2[0] == 2 else []
        bullet = sub_i(f2, 1); power_flag = sub_i(f2, 2); bet = sub_f(f2, 3)
        fish = payout = None
        g5 = get(fs, 5)
        if g5 and g5[0] == 2:
            f5 = fields(g5[1]); fish = sub_i(f5, 1); payout = sub_f(f5, 2)
        return {"cmd": 25, "voided": False, "bullet": bullet, "power_flag": power_flag,
                "bet": bet, "fish": fish, "payout": payout or 0.0, "balance": sub_f(fs, 6)}
    else:  # cmd24
        g1 = get(fs, 1); f1 = fields(g1[1]) if g1 and g1[0] == 2 else []
        return {"cmd": 24, "voided": True, "bullet": sub_i(f1, 1), "power_flag": None,
                "bet": sub_f(f1, 3), "fish": None, "payout": 0.0, "balance": sub_f(fs, 3)}

# 內建 power 對照(f2.f2 → 成本倍數);會被本 session 校正覆蓋
DEFAULT_POWER = {None: 1.0, 1: 1.0, 6: 5.0}

def calibrate_power(shots):
    """用 miss(無捕獲)的餘額差 校正 power_flag→倍數。回 {flag: ratio}。"""
    byid = {s["bullet"]: s for s in shots if s["bullet"] is not None}
    bids = sorted(byid)
    prev = None
    samples = collections.defaultdict(list)  # flag -> [cost/bet]
    for bid in bids:
        s = byid[bid]; bal = s["balance"]
        if prev is not None and bal is not None and not s["voided"] and not s["fish"] and s["bet"]:
            cost = prev - bal                       # miss: 餘額只減 cost
            if cost > 0:
                samples[s["power_flag"]].append(round(cost / s["bet"], 3))
        if bal is not None: prev = bal
    pmap = dict(DEFAULT_POWER)
    for flag, rs in samples.items():
        if rs:
            pmap[flag] = collections.Counter(rs).most_common(1)[0][0]   # 眾數
    return pmap, {str(k): collections.Counter(v) for k, v in samples.items()}

# ── 單檔拆解 ────────────────────────────────────────────────────────────────
def build(frames):
    """一個側錄檔 → welcome, shots(依到達順序 cmd24/25), pickups, bigwins, jackpots。"""
    welcome = None
    shots = []
    pickups = []; bigwins = []; jackpots = []
    for idx, d, cmd, body, raw in frames:
        if d == "RECV" and cmd is None and len(raw) > 200 and welcome is None:
            welcome = parse_welcome(raw)
        if cmd in (24, 25) and d == "RECV":
            shots.append(parse_shot(cmd, body))
        elif cmd == 46 and d == "RECV":
            fs = fields(body); amt = sub_f(fs, 2)
            if amt is not None: pickups.append(round(amt, 4))
        elif cmd == 30 and d == "RECV":
            fs = fields(body)
            bigwins.append({"mult": sub_f(fs, 3), "net": sub_f(fs, 5)})
        elif cmd == 28 and d == "RECV":
            fs = fields(body)
            jackpots.append([round(x, 4) for x in
                             (as_f64(v) for _, v in getall(fs, 1) + getall(fs, 2) + getall(fs, 3) + getall(fs, 4))
                             if x is not None])
    return welcome, shots, pickups, bigwins, jackpots

def split_sessions(shots):
    """一檔內可能含多次重連(idle-kick 後 game 自動重連)。新 session = bullet_id 真的從頭(≤3)
    重新開始(重連會重置計數)。只看「倒退」會誤切(frame 按到達時間排,同 session 子彈到達本就亂序)。"""
    sessions = []; cur = []; maxbid = 0
    for s in shots:
        bid = s["bullet"]
        if bid is not None and bid <= 3 and maxbid > 20:   # 歸零重連 = 新 session
            if cur: sessions.append(cur)
            cur = []; maxbid = 0
        cur.append(s)
        if bid is not None: maxbid = max(maxbid, bid)
    if cur: sessions.append(cur)
    return sessions

def session_rows(shots, sid):
    """單一 session(bullet_id 1..N 連續) → 每發 row(含成本/倍率);power 本 session 校正。"""
    pmap, _ = calibrate_power(shots)
    rows = []
    for s in sorted((x for x in shots if x["bullet"] is not None), key=lambda x: x["bullet"]):
        if s["voided"]:
            rows.append({"session": sid, "bullet": s["bullet"], "voided": True,
                         "bet": s["bet"], "cost": 0.0, "fish": None, "payout": 0.0,
                         "mult": None, "power": 0, "balance": s["balance"]})
            continue
        bet = s["bet"] or 0.0
        power = pmap.get(s["power_flag"], DEFAULT_POWER.get(s["power_flag"], 1.0))
        cost = round(bet * power, 6)
        mult = round(s["payout"] / bet) if (s["fish"] and bet) else None
        rows.append({"session": sid, "bullet": s["bullet"], "voided": False,
                     "bet": round(bet, 4), "power": power, "cost": cost, "fish": s["fish"],
                     "payout": round(s["payout"], 4), "mult": mult,
                     "balance": s["balance"], "power_flag": s["power_flag"]})
    return rows, pmap

def aggregate(rows, welcome, pickups, bigwins, jackpots, n_sessions, n_files):
    tot_cost = tot_pay = 0.0; n_shot = n_catch = n_void = 0
    mult_hist = collections.Counter(); power_hist = collections.Counter(); bet_hist = collections.Counter()
    for r in rows:
        if r["voided"]: n_void += 1; continue
        tot_cost += r["cost"]; tot_pay += r["payout"]; n_shot += 1
        if r["fish"]:
            n_catch += 1
            if r["mult"] is not None: mult_hist[r["mult"]] += 1
        power_hist[r["power"]] += 1
        if r["bet"]: bet_hist[round(r["bet"], 3)] += 1
    pk = round(sum(pickups), 4)
    return {
        "game": "736 Jackpot Fishing 2 (fishing)",
        "sessions": n_sessions, "capture_files": n_files,
        "player": (welcome or {}).get("account"),
        "currency": (welcome or {}).get("currency"),
        "start_balance": (welcome or {}).get("start_balance"),
        "bet_ladder": (welcome or {}).get("bet_ladder"),
        "shots_charged": n_shot, "shots_voided": n_void, "catches": n_catch,
        "catch_rate": round(n_catch / n_shot, 4) if n_shot else None,
        "total_cost": round(tot_cost, 4), "total_payout": round(tot_pay, 4),
        "RTP": round(tot_pay / tot_cost, 4) if tot_cost else None,   # ★權威 RTP = Σpayout/Σcost
        "cmd46_amount_sum_UNVERIFIED": pk, "cmd46_count": len(pickups),
        "_cmd46_note": "cmd46(金幣/道具)加總,語意未定(加進 RTP 會>100%,故【不是】玩家淨收入,已排除於 RTP)。",
        "fish_multiplier_histogram": dict(sorted(mult_hist.items())),
        "power_histogram": dict(sorted(power_hist.items())),
        "bet_histogram": dict(sorted(bet_hist.items())),
        "bigwins": bigwins,
        "jackpot_pool_last": jackpots[-1] if jackpots else None,
        "jackpot_pool_samples": len(jackpots),
        "_note": "跨 session 累加(含 raw_sessions/)。RTP 需大量樣本才有統計意義。cost=bet×power;payout=bet×mult。",
    }

def collect_sources(src):
    """主來源 + 同目錄 raw_sessions/*.jsonl(被 idle-kick 重連的歷史段),去重。"""
    srcs = []
    seen = set()
    def add(p):
        p = Path(p)
        if p.exists():
            rp = str(p.resolve())
            if rp not in seen: seen.add(rp); srcs.append(p)
    add(src)
    arch = src.parent / "raw_sessions"
    if arch.is_dir():
        for p in sorted(arch.glob("*.jsonl")): add(p)
    return srcs

# ── 主程式 ────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gid", nargs="?", default="736")
    ap.add_argument("--src", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-accumulate", action="store_true",
                    help="只解 --src 單檔,不累加 raw_sessions/")
    args = ap.parse_args()

    src = Path(args.src) if args.src else Path(f"games/{args.gid}/traffic.jsonl")
    out = Path(args.out) if args.out else Path(f"games/{args.gid}/math")
    if not src.exists() and not (src.parent / "raw_sessions").is_dir():
        sys.exit(f"✗ 找不到來源:{src}(先 ./wscapture_boot.sh {args.gid} 或 wscapture.sh {args.gid})")
    out.mkdir(parents=True, exist_ok=True)

    sources = [src] if args.no_accumulate else collect_sources(src)
    all_rows = []; welcome = None; pickups = []; bigwins = []; jackpots = []
    pmap_last = {}; n_sessions = 0
    for fp in sources:
        frames = load_frames(fp)
        w, shots, pk, bw, jp = build(frames)
        if w and not welcome: welcome = w
        pickups += pk; bigwins += bw; jackpots += jp
        for si, sess in enumerate(split_sessions(shots)):
            sid = f"{fp.stem}:{si}"
            rows, pmap = session_rows(sess, sid)
            if rows: n_sessions += 1; all_rows += rows; pmap_last = pmap or pmap_last

    all_rows.sort(key=lambda r: (r["session"], r["bullet"]))
    summary = aggregate(all_rows, welcome, pickups, bigwins, jackpots, n_sessions, len(sources))
    summary["power_map_calibrated"] = {str(k): v for k, v in pmap_last.items()}

    with open(out / "shots.jsonl", "w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_interface(out / "INTERFACE.md", summary)

    print(f"✓ 解出 {summary['shots_charged']} 發(作廢 {summary['shots_voided']})"
          f" 捕獲 {summary['catches']}({(summary['catch_rate'] or 0)*100:.1f}%)")
    print(f"  Σcost={summary['total_cost']}  Σpayout={summary['total_payout']}"
          f"  ★RTP={(summary['RTP'] or 0)*100:.2f}%★  (sessions={summary['sessions']})")
    print(f"  power_map(校正)={summary['power_map_calibrated']}  bet={summary['bet_histogram']}")
    print(f"  魚倍率直方圖={summary['fish_multiplier_histogram']}")
    print(f"  → {out}/shots.jsonl  summary.json  INTERFACE.md")

def write_interface(path, s):
    md = """# JILI 736 Jackpot Fishing 2 — 機率團隊介面

魚機(連續射擊),無「局」。每一**發子彈**是一筆事件。明文 protobuf WS,零加密。

## 每發欄位(`shots.jsonl`,一行一發,已按 bullet_id 排序)
| 欄位 | 意義 |
|---|---|
| `bullet` | 子彈序號(遞增) |
| `voided` | true=作廢的一發(server 處理時魚已不在)→ **金流淨 0,RTP 排除** |
| `bet` | 下注基數(cmd25 f2.f3;= 砲台 coin 值) |
| `power` | 砲台倍率(成本 = bet × power) |
| `cost` | 這發成本 = bet × power |
| `fish` | 捕獲的魚實例 id(null=沒捕到;畫面 transient,非魚種) |
| `payout` | 捕獲配當(= bet × 魚倍率 M) |
| `mult` | 魚倍率 M = payout / bet(乾淨整數) |
| `balance` | 這發結算後餘額 |

## 金流模型(實測全域守恆驗過)
```
cost   = bet × power              # power 由砲台等級決定
payout = bet × M (捕獲時)          # M = 魚倍率(整數)
餘額   = 前餘額 − cost + payout     # miss: payout=0;按 bullet_id 排序才會鏈對
RTP    = Σpayout / Σcost
```
`power` 由封包 `cmd25.f2.f2` 旗標決定,本工具會**自動從 miss 的餘額差校正** flag→倍數,
不寫死。本 session 校正結果:`{pmap}`。

## 累加摘要(跨 session;{nsess} session / {nfiles} 檔)
- 玩家 {acct} / 幣別 {cur} / 起始餘額 {bal}
- 開砲 **{nshot}** 發(作廢 {nvoid})、捕獲 **{ncatch}**({crate:.2f}%)
- Σcost = **{tcost}**、Σpayout = **{tpay}**、**RTP = {rtp:.2f}%**(= Σpayout/Σcost,權威)
- 魚倍率直方圖(M→次數):`{mh}`
- power 直方圖:`{ph}`、bet 直方圖:`{bh}`
- 彩金池(Jackpot 四層,最後快照):`{jp}`

## 注意
1. **RTP 需大量樣本**(魚機單發變異極大,大魚倍率可達上千倍);衝量越多越穩。
2. `fish` 是畫面實例 id,不是魚種;魚種→基礎倍率對照在目錄封包 cmd82/cmd45(待補)。
3. ★cmd46(金幣/道具)**語意未定、不是玩家淨收入**(加進 RTP 會 >100%),已【排除】於 RTP。
   大獎公告 cmd30、彩金池 cmd28 另附於 summary。若要含彩金的完整 RTP,需把中彩事件也納入(待補)。
4. 被 idle-kick 重連=重跑 `webcapture.sh`(自動歸檔 raw_sessions/),finish 會跨 session 累加。
""".format(
        pmap=s["power_map_calibrated"], acct=s["player"], cur=s["currency"], bal=s["start_balance"],
        nsess=s.get("sessions", 1), nfiles=s.get("capture_files", 1),
        nshot=s["shots_charged"], nvoid=s["shots_voided"], ncatch=s["catches"],
        crate=(s["catch_rate"] or 0) * 100, tcost=s["total_cost"], tpay=s["total_payout"],
        rtp=(s["RTP"] or 0) * 100, mh=s["fish_multiplier_histogram"],
        ph=s["power_histogram"], bh=s["bet_histogram"], jp=s["jackpot_pool_last"])
    Path(path).write_text(md, encoding="utf-8")

if __name__ == "__main__":
    main()
