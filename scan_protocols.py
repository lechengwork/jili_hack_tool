#!/usr/bin/env python3
"""
scan_protocols.py — 對一批 gameID 跑 LoginGame，分類 data.game_url 的形態，
找出「非舊協議」的異常（＝真正的新協議候選）。

分類邏輯（依 memory jili-game-launch-flow 的實測）：
  direct : uat-wbgame.../<path>/?ssoKey=&gameID=   → 舊 fg5-family 協議，只差 path
  guide  : uat-www.../zh-CN/guide?token=&game=      → 該款沒上架的 fallback（跳過）
  OTHER  : 以上都不符                                → ★新協議候選★，值得深挖

用法：
  ./.venv/bin/python scan_protocols.py                # 掃 games.json 尚未分類的 ID
  ./.venv/bin/python scan_protocols.py 2 9 17 300     # 指定 ID
  SLEEP=6 ./.venv/bin/python scan_protocols.py 200-260 # 掃一段範圍（含）

前提：LoginGame 擋巴西 IP → 這支要在 **VPN 關閉** 時跑。
      每次 login 會消耗一張單次有效 game_url（我們只看形態、不跑遊戲，無妨）。
"""
import json, os, sys, time
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))
import jili_login  # 重用 login()

# 0907 memory 已分類為 direct 的 path，只是列出來對照，不影響掃描
KNOWN_DIRECT = {"696": "/fg5/", "49": "/fullhouse/", "94": "/rummy/index.html"}

# games.json 裡尚未被 memory 分類的 ID（預設掃這批）
DEFAULT_IDS = ["2", "9", "17", "30", "35", "38", "45", "47", "51", "58",
               "102", "103", "106", "108"]

SECRET_KEYS = ("ssoKey", "token", "sign", "key", "auth")


def parse_ids(argv):
    out = []
    for a in argv:
        a = a.strip().strip(",")
        if not a:
            continue
        if "-" in a and all(p.isdigit() for p in a.split("-", 1)):
            lo, hi = a.split("-", 1)
            out += [str(n) for n in range(int(lo), int(hi) + 1)]
        else:
            out.append(a)
    return out or DEFAULT_IDS


def redact(url):
    if not url:
        return url
    s = urlsplit(url)
    if not s.query:
        return url
    q = parse_qs(s.query, keep_blank_values=True)
    for k in list(q):
        if any(sk.lower() in k.lower() for sk in SECRET_KEYS):
            q[k] = ["<redacted>"]
    newq = "&".join(f"{k}={v[0]}" for k, v in q.items())
    return f"{s.scheme}://{s.netloc}{s.path}?{newq}"


def classify(url):
    if not url:
        return "no_url", ""
    s = urlsplit(url)
    host, path = s.netloc, s.path
    qkeys = set(parse_qs(s.query, keep_blank_values=True).keys())
    if "wbgame" in host and {"ssoKey", "gameID"} <= qkeys:
        return "direct", path                       # 舊協議，path 就是家族
    if "guide" in path or ("wbslot" not in host and "token" in qkeys and "game" in qkeys):
        return "guide", path                        # 沒上架
    return "OTHER", f"{host}{path}?{','.join(sorted(qkeys))}"   # ★新協議候選★


def scan_one(gid):
    """回傳 dict；把 login() 的 sys.exit/例外都吞成一列結果，不中斷整批。"""
    try:
        r = jili_login.login(gid, verbose=False)
    except jili_login.LoginError as e:
        return {"gid": gid, "kind": f"login_err({e.code})", "detail": e.message[:80]}
    except SystemExit as e:                          # 連線失敗/HTTP4xx/限流
        return {"gid": gid, "kind": "conn/exit", "detail": str(e)[:120]}
    except Exception as e:                           # noqa
        return {"gid": gid, "kind": "exc", "detail": f"{type(e).__name__}: {e}"[:120]}
    url = r.get("game_url")
    kind, detail = classify(url)
    return {"gid": gid, "kind": kind, "detail": detail,
            "url": redact(url), "game_id": r.get("game_id")}


def main():
    ids = parse_ids(sys.argv[1:])
    sleep = float(os.environ.get("SLEEP", "5"))
    out_path = Path(os.environ.get("OUT", "/tmp/jili_scan.jsonl"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[scan] {len(ids)} 個 gameID，間隔 {sleep}s，結果 → {out_path}", file=sys.stderr)
    print(f"[scan] 提醒：LoginGame 擋 BR IP，請確認 VPN 已關閉", file=sys.stderr)

    rows, others = [], []
    with open(out_path, "w", encoding="utf-8") as f:
        for i, gid in enumerate(ids, 1):
            row = scan_one(gid)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            tag = row["kind"]
            mark = "★" if tag == "OTHER" else " "
            print(f"  {mark}[{i}/{len(ids)}] {gid:>5}  {tag:<14} {row.get('detail','')}",
                  file=sys.stderr)
            rows.append(row)
            if tag == "OTHER":
                others.append(row)
            if i < len(ids):
                time.sleep(sleep)

    # 摘要
    from collections import Counter
    c = Counter(r["kind"] for r in rows)
    print("\n" + "═" * 56, file=sys.stderr)
    print("摘要：", dict(c), file=sys.stderr)
    if others:
        print(f"\n★ 新協議候選 {len(others)} 個（game_url 不符舊式直連/guide）：", file=sys.stderr)
        for r in others:
            print(f"    gid={r['gid']}  {r.get('url','')}", file=sys.stderr)
    else:
        print("\n（本批全是舊協議 direct / guide / 錯誤，未見新協議形態）", file=sys.stderr)
    # 也印出所有 direct 的 path，補充 memory 的 path 清單
    dpaths = sorted({r["detail"] for r in rows if r["kind"] == "direct"})
    if dpaths:
        print(f"\ndirect path（可補進 memory 清單）：{dpaths}", file=sys.stderr)


if __name__ == "__main__":
    main()
