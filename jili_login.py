#!/usr/bin/env python3
"""
jili_login.py — 本地產生 game_url（取代那個開了 VPN 就不能用的網頁）

用法:
  ./.venv/bin/python jili_login.py GAMEID [--player-id X] [--game-id Y] [--json]

  GAMEID        遊戲數字 ID（會用 config.json 的 game_id 樣板組出 game_id）
  --player-id   覆蓋 config.json 的 player_id
  --game-id     直接指定完整 game_id（覆蓋樣板，例如 111000696）
  --json        只印出 JSON（給程式接）

讀 config.json 的 login 區塊，POST 到 LoginGame，印出單次有效的 game_url。

重點：LoginGame 站台會擋巴西 IP，所以**這支要在 VPN 關閉時跑**。
拿到 game_url 後再開 VPN，用 jili_capture.py --url "<game_url>" 擷取。
（若之後確認 LoginGame 在 BR 也能通，capture 會自動呼叫它，就不用手動兩段。）
"""
import argparse
import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent
CONFIG_PATH = BASE / "config.json"


def dig(obj, path):
    cur = obj
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]; continue
            except (ValueError, IndexError):
                return None
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def subst(obj, gameid):
    if isinstance(obj, str):
        try:
            return obj.format(gameid=int(gameid))
        except (ValueError, KeyError, IndexError):
            return obj.replace("{gameid}", gameid)
    if isinstance(obj, dict):
        return {k: subst(v, gameid) for k, v in obj.items()}
    if isinstance(obj, list):
        return [subst(v, gameid) for v in obj]
    return obj


class LoginError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"code={code} message={message}")


def login(gameid, player_id=None, game_id=None, verbose=True, account=None):
    import requests

    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    L = cfg.get("login", {})
    url = L.get("url", "")
    headers = subst(L.get("headers") or {}, gameid)
    body = subst(L.get("body") or {}, gameid)
    if account:
        accts = cfg.get("login_accounts") or {}
        acc = accts.get(account)
        if not acc:
            sys.exit(f"[錯誤] config.json 沒有候選帳號 {account!r}"
                     f"（有:{[k for k in accts if not k.startswith('_')]}）")
        headers["authorization"] = "bearer " + str(acc["token"]).replace("bearer ", "").strip()
        body["player_id"] = acc.get("player_id", body.get("player_id"))
        if verbose:
            print(f"[登入] 用候選帳號 --account {account}: player_id={body['player_id']} "
                  f"agent={acc.get('agent','?')} currency={acc.get('currency','?')}", file=sys.stderr)
    if player_id:
        body["player_id"] = player_id
    if game_id:
        body["game_id"] = game_id

    if "<" in url or any("<" in str(v) for v in headers.values()):
        sys.exit("[錯誤] config.json 的 login 還有沒填的佔位符（<api-host> / <JWT>）")

    if verbose:
        print(f"[登入] POST {url}", file=sys.stderr)
        print(f"[登入] body: {json.dumps(body, ensure_ascii=False)}", file=sys.stderr)

    import os
    headers.setdefault("Accept-Encoding", "gzip, deflate")   # 不宣告 zstd,避免收到解不開的壓縮
    token_path = L.get("token_path", "data.game_url")
    tries = int(os.environ.get("LOGIN_RETRIES", "4"))
    for attempt in range(1, tries + 1):
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=30)
        except requests.exceptions.RequestException as e:
            sys.exit(f"[錯誤] 連線失敗: {e}\n  · 若目前開著 VPN，關掉再試（LoginGame 擋巴西 IP）")
        try:
            data = resp.json()
        except ValueError:
            data = None
        code = data.get("code") if isinstance(data, dict) else None
        msg = data.get("message", "") if isinstance(data, dict) else resp.text[:200]
        game_url = dig(data, token_path) if isinstance(data, dict) else None
        if verbose:
            print(f"[登入] HTTP {resp.status_code} code={code} msg={msg!r} game_url="
                  f"{'ok' if game_url else 'null'} (第{attempt}/{tries}次)", file=sys.stderr)

        if resp.status_code == 200 and code in (0, None) and game_url:
            return {"game_url": game_url, "gameid": gameid, "game_id": body.get("game_id"),
                    "player_id": body.get("player_id"),
                    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "raw": data}

        # 限流(907)/429/「code=0 但 game_url=null」都是暫時性 → 退避重試
        retriable = (code == 907 or resp.status_code == 429
                     or (resp.status_code == 200 and code in (0, None) and not game_url))
        if attempt < tries and retriable:
            wait = 12 * attempt
            print(f"[登入] 暫時性未成功 → 等 {wait}s 重試…", file=sys.stderr)
            time.sleep(wait)
            continue

        # 放棄:給清楚原因
        if isinstance(data, dict):
            print(json.dumps(data, ensure_ascii=False, indent=2)[:1200], file=sys.stderr)
        if resp.status_code >= 400 and code != 907:
            sys.exit(f"[錯誤] LoginGame 回 HTTP {resp.status_code}")
        if code == 907:
            sys.exit("[錯誤] 一直被限流 (code 907 api too frequent) — 等幾分鐘再跑 go.sh")
        if code not in (0, None):
            raise LoginError(code, msg)
        sys.exit(f"[錯誤] 拿不到 game_url (code={code} msg={msg!r}) — 多為暫時性/限流,稍後再試")


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("gameid")
    ap.add_argument("--player-id", default=None)
    ap.add_argument("--game-id", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--account", default=None,
                    help="用 config.json 的 login_accounts 候選帳號(如 usd / thb);覆蓋 token+player_id")
    ap.add_argument("--count", type=int, default=1,
                    help="一次產幾張（VPN 關閉時先囤一批，之後開 VPN 連續擷取不用再切）")
    ap.add_argument("--save", action="store_true",
                    help="存進 games/<gameid>/tokens.jsonl 供 jili_capture.py --from-pool 取用")
    args = ap.parse_args()

    import time as _t
    pool = BASE / "games" / args.gameid / "tokens.jsonl"
    if args.save:
        pool.parent.mkdir(parents=True, exist_ok=True)

    def save_one(r):
        with open(pool, "a", encoding="utf-8") as f:
            f.write(json.dumps({"game_url": r["game_url"],
                                "fetched_at": r["fetched_at"],
                                "used": False}, ensure_ascii=False) + "\n")

    results = []
    target = max(1, args.count)
    i = 0
    while i < target:
        try:
            r = login(args.gameid, args.player_id, args.game_id,
                      verbose=(not args.json and target == 1), account=args.account)
        except LoginError as e:
            if e.code == 907:            # 速率限制 → 退避重試（同一張）
                print(f"  [{i+1}/{target}] 907 速率限制，等 8 秒重試...", file=sys.stderr)
                _t.sleep(8)
                continue
            print(f"  [{i+1}/{target}] 失敗: {e}", file=sys.stderr)
            break
        results.append(r)
        if args.save:
            save_one(r)                  # 每張立刻存，中途失敗不會全丟
        if target > 1:
            print(f"  [{i+1}/{target}] ssoKey="
                  f"{r['game_url'].split('ssoKey=')[1][:24]}...  已存", file=sys.stderr)
        i += 1
        if i < target:
            _t.sleep(5)                  # 間隔，避開 907

    if not results:
        sys.exit("[錯誤] 一張都沒產到")

    if args.save:
        remaining = sum(1 for l in pool.read_text().splitlines()
                        if l.strip() and not json.loads(l).get("used"))
        print(f"\n[池] 這次新增 {len(results)} 張，池內未用共 {remaining} 張 → {pool}", file=sys.stderr)
        print(f"     開 VPN 後： ./.venv/bin/python jili_capture.py {args.gameid} --no-proxy --from-pool", file=sys.stderr)
        return

    if args.json:
        print(json.dumps([{k: v for k, v in r.items() if k != "raw"} for r in results],
                         ensure_ascii=False))
    else:
        r = results[0]
        print()
        print("═" * 60)
        print(f"  game_url（單次有效）:")
        print(f"  {r['game_url']}")
        print("═" * 60)
        print(f"\n下一步（記得先開 VPN 到巴西）：")
        print(f'  ./.venv/bin/python jili_capture.py {r["gameid"]} --url "{r["game_url"]}"')


if __name__ == "__main__":
    main()
