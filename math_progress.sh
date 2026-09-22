#!/usr/bin/env bash
# math_progress.sh — 擷取進度 & 還差什麼。開另一個終端跑,隨時看。
#   ./math_progress.sh                       # 預設看 games/696/math_ante8
#   ./math_progress.sh games/696/math        # 指定目錄
#   ./math_progress.sh --all                 # 所有 math* 目錄合起來看
#   watch -n 20 ./math_progress.sh           # 自動刷新(有裝 watch 的話)
set -u
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "${1:-}" = "--all" ]; then
  DIRS=$(ls -d games/696/math* 2>/dev/null)
else
  DIRS="${1:-games/696/math_ante8}"
fi
.venv/bin/python - "$DIRS" <<'PYEOF'
import sys, json, glob, collections
VAL = {9:1, 10:2, 11:3, 12:5, 13:10, 14:15, 15:20, 16:25, 17:50, 18:100, 19:500, 20:0}
# 20 = 轉輪上的 Ex Nudge 標記,計 0
# 符號 20 是轉輪上的 Ex Nudge 標記,不是倍率,所以不列進 VAL
rows = []
for d in sys.argv[1].split():
    for fp in glob.glob(d + '/*.json'):
        try:
            d = json.load(open(fp, encoding='utf-8'))
            rows.append(d.get('data') or d['spinresult'])   # data=新;spinresult=舊檔相容
        except Exception:
            pass
if not rows:
    print('  (還沒有局)'); raise SystemExit
# ── 側錄還活著嗎:看 shim 寫的側錄串流,不是檔案 mtime
#    (math_migrate_keys.sh 會重寫所有樣本檔,mtime 會被洗掉,不能拿來判斷)
import time, os as _os
_cap = 'games/696/webcap_exchanges.jsonl'
if _os.path.exists(_cap):
    age = time.time() - _os.path.getmtime(_cap)
    if age < 90:
        print(f"  側錄狀態: ● 活著(最後一筆 {age:.0f} 秒前)")
    elif age < 600:
        print(f"  側錄狀態: ◍ 最後一筆 {age/60:.1f} 分鐘前 —— 你沒在轉,還是 shim 掉了?")
    else:
        print(f"  側錄狀態: ○ ★停了★ 最後一筆 {age/60:.0f} 分鐘前 —— 現在轉的都沒被錄到")

nud  = [r for r in rows if r['board']['window_extra'] or len(r['board']['window']) > 5]
win  = [r for r in rows if r['board']['line_wins']]
ante = collections.Counter(r['ante'] for r in rows)
print(f"  總局 {len(rows)}   中獎 {len(win)} ({len(win)/len(rows)*100:.0f}%)   下注模式 {dict(ante)}")
# Ex Nudge:規則已解(5/5),這裡改成【回歸驗證】—— 每局新的都拿來考規則,撞到反例立刻報
def nudge_mult(b):
    """一條規則通吃(403/403 零反例):視窗 = 上2格 + 抓取區間 + 下2格,中間那段加總。
    不能用 window_extra —— 連鎖觸發(group=3)時它只記第一段。"""
    w = b['window']
    sl = w[2:len(w) - 2]
    if any(x not in VAL for x in sl):
        return None
    return sum(VAL[x] for x in sl)
good = bad = unknown = 0
for r in rows:
    got = nudge_mult(r['board'])
    if got is None: unknown += 1
    elif abs(got - r['board']['multiplier']) < 1e-9: good += 1
    else:
        bad += 1
        print(f"  ✗★反例★ extra={r['board']['window_extra']} group={r['board']['nudge_group']} "
              f"規則算出 {got} 但封包是 {r['board']['multiplier']:g}  → 規則要重解")
rate = f"{len(nud)/len(rows)*100:.1f}%" if rows else '-'
print(f"  Ex Nudge {len(nud)} 局(觸發率 {rate})  倍率規則 {good}/{good+bad} 局吻合"
      + (f" / {unknown} 含未知符號" if unknown else "")
      + ("   ★規則站得住★" if bad == 0 and good else ""))

# 倍率轉輪:中間格出現過哪些符號(擴張局的規則還沒定案,不列入)
ctr = collections.Counter(r['board']['window'][2] for r in rows if not r['board']['window_extra'])
unk = sorted(set(ctr) - set(VAL))
print(f"  倍率轉輪中間格: {' '.join(f'{k}={VAL[k]}x' for k in sorted(ctr) if k in VAL)}")
if unk:
    print(f"  ★ 新符號(倍率待解): {unk} → 對應倍率 " +
          str(sorted({r['board']['multiplier'] for r in rows
                      if not r['board']['window_extra'] and r['board']['window'][2] in unk})))
seen_any = set()
for r in rows:
    seen_any |= set(r['board']['window'])
todo = sorted(seen_any - set(VAL))
print(f"  轉輪符號: {'11 種倍率全部已知(1x–500x)' if not todo else f'★未知 {todo}★'}")

# 賠付表:哪些符號中過獎
pay = {}
for r in rows:
    for w in r['board']['line_wins']:
        s = w.get('symbol_id', 0)
        if r['base_bet'] and r['board']['multiplier']:
            pay[s] = round(w['win_cash'] / (r['base_bet'] / 5) / r['board']['multiplier'], 4)
print(f"  3 連線賠付表: {dict(sorted(pay.items())) if pay else '(還沒中獎)'}")
seen_reel = sorted({s for r in rows for x in r['board']['reels'] for s in x['symbols']})
gift = [r for r in rows if any(r['board'].get('nudge_pos') or [])]
print(f"  nudge_pos 非零(疑似饋贈): {len(gift)} 局" + (f"  → {[r['board']['nudge_pos'] for r in gift]}" if gift else ""))
todo_pay = sorted(set(seen_reel) - set(pay) - {7, 8})   # 7=WILD 8=ExNudge百搭,記在被替代的符號上
print(f"  賠付表 {'完整(J/Q/K/A/綠/藍/紅 全解出,與官方表 7/7 吻合)' if not todo_pay else f'還缺 {todo_pay}'}")
bybet = collections.defaultdict(lambda: [0, 0])
for r in rows:
    e = bybet[r['base_bet']]
    e[0] += 1
    e[1] += 1 if r['board']['line_wins'] else 0
print("  各注額樣本(局數/中獎數;驗金額線性要【中獎】才算數):")
for b in sorted(bybet):
    n, w = bybet[b]
    ok = '✓ 夠了' if w >= 3 else (f'還缺 {3-w} 個中獎' if n else '')
    print(f"     注額 {b:<8g} {n:>4} 局 / 中獎 {w:>3}   {ok}")
if len(bybet) < 2:
    print("     ← 只有一種注額,無法驗金額線性")
PYEOF
