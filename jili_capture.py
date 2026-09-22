#!/usr/bin/env python3
"""
jili_capture.py — Step 1: 用 mitmproxy + 真實 Chrome 擷取 JILI 遊戲

用法:
  ./.venv/bin/python jili_capture.py GAMEID [--url URL] [--port 8080] [--timeout 600]

為什麼不用 Playwright:
  JILI 的 JS 過 jscrambler，會偵測 CDP／自動化瀏覽器並中止載入。
  改成「網路層攔截 + 真實 Chrome」就完全看不出是自動化環境。

流程:
  1. 依需要呼叫 LoginGame 換一張全新的 game_url（單次有效）
  2. 啟動 mitmdump，載入 jili_mitm.py
  3. 用獨立 profile 啟動真實 Chrome，走 proxy，直接開遊戲
  4. 等你把遊戲玩幾局後關掉 Chrome（或到 --timeout）
  5. 收掉 proxy，把 traffic.jsonl 整理成 traffic_raw.json

產出:
  games/GAMEID/static/...        靜態資源
  games/shared/...               astarte2 / smallicon 共用資源
  games/GAMEID/traffic_raw.json  後端流量（給 game_analyze.py 用）
"""
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

BASE = Path(__file__).parent
CONFIG_PATH = BASE / "config.json"
GAMES_DIR = BASE / "games"
ADDON = BASE / "jili_mitm.py"

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"[錯誤] 找不到 {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def rev(s: str) -> str:
    return s[::-1]


# ── 登入 ─────────────────────────────────────────────────────────────────────

def dig(obj, path: str):
    cur = obj
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
                continue
            except (ValueError, IndexError):
                return None
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj and obj[key]:
            return obj[key]
        for v in obj.values():
            r = _find_key(v, key)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_key(v, key)
            if r:
                return r
    return None


def _subst(obj, gameid: str):
    """把 {gameid} / {gameid:06d} 佔位換成實際 gameID。"""
    if isinstance(obj, str):
        try:
            return obj.format(gameid=int(gameid))
        except (ValueError, KeyError, IndexError):
            return obj.replace("{gameid}", gameid)
    if isinstance(obj, dict):
        return {k: _subst(v, gameid) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_subst(v, gameid) for v in obj]
    return obj


def do_login(login_cfg: dict, gameid: str) -> str:
    """呼叫 LoginGame。回傳完整 game_url（或 ssoKey）。"""
    import requests

    url = login_cfg.get("url", "")
    if not url:
        sys.exit("[錯誤] login.enabled=true 但 login.url 是空的")

    method = login_cfg.get("method", "POST").upper()
    headers = _subst(login_cfg.get("headers") or {}, gameid)
    body = _subst(login_cfg.get("body") or {}, gameid)
    token_path = login_cfg.get("token_path", "")

    if "<" in url or any("<" in str(v) for v in headers.values()):
        sys.exit("[錯誤] config.json 的 login 還有沒填的佔位符（<api-host> / <JWT>）")

    print(f"[登入] {method} {url}")
    print(f"[登入] body: {json.dumps(body, ensure_ascii=False)}")

    if method == "GET":
        resp = requests.get(url, headers=headers, params=body, timeout=30)
    elif "json" in str(headers.get("Content-Type", "")).lower():
        resp = requests.post(url, headers=headers, json=body, timeout=30)
    else:
        resp = requests.post(url, headers=headers, data=body, timeout=30)

    print(f"[登入] HTTP {resp.status_code}")
    if resp.status_code >= 400:
        print(f"[登入] 回應: {resp.text[:500]}")
        sys.exit("[錯誤] 登入失敗")

    try:
        data = resp.json()
    except ValueError:
        tok = resp.text.strip()
        if tok:
            return tok
        sys.exit("[錯誤] 登入回應無法解析")

    if token_path:
        tok = dig(data, token_path)
        if tok:
            tok = str(tok)
            print("[登入] 取得 game_url（單次有效）" if tok.startswith("http")
                  else f"[登入] 取得 ssoKey: {tok[:20]}...")
            return tok
        print(f"[登入] token_path='{token_path}' 取不到值。回應：")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:1500])
        sys.exit("[錯誤] 請修正 config.json 的 login.token_path")

    for key in ("game_url", "gameUrl", "url", "ssoKey", "token"):
        found = _find_key(data, key)
        if found:
            print(f"[登入] 自動偵測到 {key}")
            return str(found)
    print(json.dumps(data, ensure_ascii=False, indent=2)[:1500])
    sys.exit("[錯誤] 找不到 game_url／token，請設定 login.token_path")


def build_game_url(cfg: dict, gameid: str, sso: str) -> str:
    s = cfg["site"]
    params = {
        "ssoKey": sso, "lang": s.get("lang", "zh-CN"), "apiId": s.get("api_id", ""),
        "be": rev(s.get("be_host", "")),
        "domain_platform": rev(s.get("platform_host", "")),
        "gameID": gameid, "gs": rev(s.get("gs_host", "")),
        "iu": "true", "legalLang": "true", "skin": s.get("skin", "0"),
    }
    qs = "&".join(f"{k}={v}" for k, v in params.items() if v != "")
    return f"https://{s['game_host']}{s.get('game_path', '/fg5/')}?{qs}"


# ── traffic.jsonl → traffic_raw.json ─────────────────────────────────────────

def consolidate(game_dir: Path, gameid: str, game_url: str) -> dict:
    jsonl = game_dir / "traffic.jsonl"
    http_entries, ws_map, ws_order = [], {}, []

    if jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            k = e.get("kind")
            if k == "http":
                http_entries.append(e)
            elif k in ("ws_open", "ws_msg", "ws_close"):
                url = e.get("url", "")
                if url not in ws_map:
                    ws_map[url] = {"kind": "ws", "url": url, "frames": []}
                    ws_order.append(url)
                if k == "ws_msg":
                    ws_map[url]["frames"].append({
                        "dir": e.get("dir"), "ts": e.get("ts"),
                        "binary": e.get("binary", False),
                        "text": e.get("text"), "hex": e.get("hex"),
                    })

    static_count = sum(1 for _ in (game_dir / "static").rglob("*") if _.is_file())
    return {
        "gameid": gameid,
        "game_url": game_url,
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "capture_method": "mitmproxy + real Chrome",
        "http": http_entries,
        "websockets": [ws_map[u] for u in ws_order],
        "static_files": static_count,
    }


# ── token 池 ─────────────────────────────────────────────────────────────────

def pop_token(gameid: str) -> str:
    """從 games/<gameid>/tokens.jsonl 取一張未用的 game_url，標記為已用。"""
    pool = GAMES_DIR / gameid / "tokens.jsonl"
    if not pool.exists():
        sys.exit(f"[錯誤] 找不到 token 池：{pool}\n"
                 f"  先在 VPN 關閉時囤一批：\n"
                 f"  ./.venv/bin/python jili_login.py {gameid} --count 5 --save")
    lines = pool.read_text(encoding="utf-8").splitlines()
    entries = [json.loads(l) for l in lines if l.strip()]
    for e in entries:
        if not e.get("used"):
            e["used"] = True
            pool.write_text(
                "\n".join(json.dumps(x, ensure_ascii=False) for x in entries) + "\n",
                encoding="utf-8")
            remaining = sum(1 for x in entries if not x.get("used"))
            print(f"[池] 取用 1 張（剩 {remaining} 張未用）")
            return e["game_url"]
    sys.exit(f"[錯誤] token 池裡沒有未用的 token 了（{pool}）\n"
             f"  VPN 關閉時再囤一批： ./.venv/bin/python jili_login.py {gameid} --count 5 --save")


# ── 不做 MITM 的擷取（netlog）────────────────────────────────────────────────

def run_no_proxy(game_url: str, gameid: str, game_dir, profile, args):
    """一般 Chrome 連真伺服器，用 Chrome netlog + SSLKEYLOGFILE 側錄。

    為什麼：mitmproxy 當中間人會被 jscrambler 偵測（假 TLS 憑證），觸發 MSG 211。
    這條路徑完全不插手連線，遊戲連真 server、看到真憑證，
    Chrome 自己的 netlog 把每條 socket 的解密後 bytes 記下來（含 /fg5/req）。
    """
    netlog = game_dir / "netlog.json"
    keylog = game_dir / "sslkeys.log"
    if netlog.exists():
        netlog.unlink()

    print("═" * 60)
    print(f"  JILI Capture（no-proxy / netlog）— gameID {gameid}")
    print("═" * 60)
    print(f"  URL     : {game_url[:100]}{'...' if len(game_url) > 100 else ''}")
    print(f"  netlog  : {netlog}  (mode={args.netlog_mode})")
    print(f"  profile : {profile}  ({'保留快取' if args.keep_profile else '全新'})")
    print(f"  不做 MITM — 遊戲連真伺服器，避開 jscrambler 偵測")
    print("─" * 60)

    env = dict(os.environ, SSLKEYLOGFILE=str(keylog))
    chrome_args = [
        CHROME,
        f"--user-data-dir={profile}",
        f"--log-net-log={netlog}",
        f"--net-log-capture-mode={args.netlog_mode}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=ChromeWhatsNewUI",
        # 強制走 TCP/H2 而非 QUIC/H3，這樣 /fg5/req 會落在 SSL socket bytes 裡（netlog 才抓得到）
        "--disable-quic",
    ]
    if getattr(args, "hook", False):
        ext = str(BASE / "jili_hook_ext")
        chrome_args += [f"--load-extension={ext}", f"--disable-extensions-except={ext}"]
        print(f"  Hook    : 載入 {ext}（先確認 jili_hooklog.py 在跑）")
    chrome_args.append(game_url)
    chrome = subprocess.Popen(chrome_args, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"[Chrome] 已開啟 (pid {chrome.pid})")
    print()
    print("  ┌─────────────────────────────────────────────────────┐")
    print("  │  這次沒有 proxy，遊戲應該能正常連線。               │")
    print("  │  若進得去，請按幾次 spin；抓夠了關掉 Chrome。       │")
    print("  └─────────────────────────────────────────────────────┘")
    print()

    start = time.time()
    try:
        chrome.wait(timeout=args.timeout)
        print(f"\n[Chrome] 已關閉（歷時 {int(time.time() - start)} 秒）")
    except subprocess.TimeoutExpired:
        print(f"\n[Chrome] 到達 {args.timeout} 秒上限，關閉中...")
        chrome.terminate()
        try:
            chrome.wait(timeout=15)
        except subprocess.TimeoutExpired:
            chrome.kill()
    except KeyboardInterrupt:
        print("\n[中斷] 收尾中...")
        chrome.terminate()

    time.sleep(1)
    size = netlog.stat().st_size // 1024 if netlog.exists() else 0
    print()
    print("═" * 60)
    print(f"  netlog: {netlog}  ({size} KB)")
    print(f"  keys  : {keylog}  ({'有' if keylog.exists() else '無'})")
    print("═" * 60)
    if not netlog.exists() or size == 0:
        print("\n[警告] netlog 是空的，Chrome 可能沒正常啟動。")
        sys.exit(3)
    print(f"\n[完成] 下一步（解析 netlog）： ./.venv/bin/python parse_netlog.py {gameid}")


# ── 主程式 ───────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("gameid")
    ap.add_argument("--url", default=None)
    ap.add_argument("--port", type=int, default=0,
                    help="proxy 埠，0 = 自動找空的（從 8081 起）")
    ap.add_argument("--timeout", type=int, default=600,
                    help="等 Chrome 關閉的上限秒數（預設 600）")
    ap.add_argument("--keep-profile", action="store_true",
                    help="保留 Chrome 暫存 profile（預設每次砍掉重建）")
    ap.add_argument("--keep-going", action="store_true")
    ap.add_argument("--no-proxy", action="store_true",
                    help="不用 mitmproxy：一般 Chrome 連真伺服器 + netlog 側錄，"
                         "避開 jscrambler 對 MITM 的偵測（用來突破 MSG 211）")
    ap.add_argument("--from-pool", action="store_true",
                    help="從 games/<gameid>/tokens.jsonl 取一張未用的 token")
    ap.add_argument("--netlog-mode", default="IncludeSensitive",
                    choices=["Default", "IncludeSensitive", "Everything"],
                    help="netlog 詳細度。Everything 會錄 socket bytes（含 /fg5/req）但很重、"
                         "會拖垮遊戲；IncludeSensitive 只錄 headers（輕、夠診斷）")
    ap.add_argument("--hook", action="store_true",
                    help="載入 jili_hook_ext 擴充，攔 WebCrypto（需先跑 jili_hooklog.py）")
    args = ap.parse_args()

    cfg = load_config()
    gameid = args.gameid

    if not args.no_proxy:
        if not ADDON.exists():
            sys.exit(f"[錯誤] 找不到 addon：{ADDON}")
        if not shutil.which("mitmdump"):
            sys.exit("[錯誤] 找不到 mitmdump，請先 brew install mitmproxy")
    if not Path(CHROME).exists():
        sys.exit(f"[錯誤] 找不到 Chrome：{CHROME}")

    # ── 決定遊戲 URL ────────────────────────────────────────────────────────
    if args.from_pool:
        game_url = pop_token(gameid)
    elif args.url:
        game_url = args.url
        qs = parse_qs(urlparse(game_url).query)
        if "gameID" in qs and qs["gameID"][0] != gameid:
            print(f"[提示] URL 的 gameID={qs['gameID'][0]}，以 URL 為準")
            gameid = qs["gameID"][0]
    elif cfg.get("login", {}).get("enabled"):
        result = do_login(cfg["login"], gameid)
        game_url = result if result.startswith("http") else build_game_url(cfg, gameid, result)
    elif cfg.get("manual_url", {}).get("url"):
        game_url = cfg["manual_url"]["url"]
    else:
        sys.exit("[錯誤] 沒有可用的入口。三選一：\n"
                 "  1) --url \"<含 ssoKey 的完整遊戲 URL>\"\n"
                 "  2) config.json 設定 login.enabled=true 並填入 LoginGame\n"
                 "  3) config.json 填入 manual_url.url")

    game_dir = GAMES_DIR / gameid
    game_dir.mkdir(parents=True, exist_ok=True)
    jsonl = game_dir / "traffic.jsonl"
    if jsonl.exists():
        jsonl.unlink()   # 每次重抓，避免混到上一輪

    # 自動避開已被佔用的 port（使用者可能還開著自己的 mitmdump）
    if args.port == 0:
        import socket
        for cand in range(8081, 8120):
            with socket.socket() as sk:
                try:
                    sk.bind(("127.0.0.1", cand))   # 不設 SO_REUSEADDR，探測才準
                except OSError:
                    continue
            args.port = cand
            break
        else:
            sys.exit("[錯誤] 8081-8119 全部被佔用")

    profile = Path(f"/tmp/chrome_jili_{gameid}")
    if not args.keep_profile and profile.exists():
        shutil.rmtree(profile, ignore_errors=True)

    # ── 不做 MITM 的路徑：一般 Chrome + netlog 側錄 ────────────────────────
    if args.no_proxy:
        run_no_proxy(game_url, gameid, game_dir, profile, args)
        return

    print("═" * 60)
    print(f"  JILI Capture — gameID {gameid}")
    print("═" * 60)
    print(f"  URL     : {game_url[:100]}{'...' if len(game_url) > 100 else ''}")
    print(f"  Proxy   : 127.0.0.1:{args.port}")
    print(f"  Profile : {profile}")
    print("─" * 60)

    # ── 啟動 mitmdump ───────────────────────────────────────────────────────
    env = dict(os.environ, JILI_GAMEID=gameid, JILI_OUT=str(GAMES_DIR))
    mitm = subprocess.Popen(
        ["mitmdump", "-q", "--listen-port", str(args.port), "-s", str(ADDON)],
        cwd=str(BASE), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    def pump():
        for line in mitm.stdout:
            print("  " + line.rstrip(), flush=True)

    import threading
    threading.Thread(target=pump, daemon=True).start()

    time.sleep(2.5)
    if mitm.poll() is not None:
        sys.exit(f"[錯誤] mitmdump 啟動失敗（exit {mitm.returncode}），"
                 f"port {args.port} 可能被佔用")
    print(f"[Proxy] mitmdump 已啟動 (pid {mitm.pid})")

    # ── 啟動真實 Chrome ─────────────────────────────────────────────────────
    chrome = subprocess.Popen([
        CHROME,
        f"--proxy-server=127.0.0.1:{args.port}",
        f"--user-data-dir={profile}",
        "--ignore-certificate-errors",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=ChromeWhatsNewUI",
        game_url,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"[Chrome] 已開啟 (pid {chrome.pid})")
    print()
    print("  ┌─────────────────────────────────────────────────────┐")
    print("  │  現在請在 Chrome 裡把遊戲玩幾局（spin 越多越好）    │")
    print("  │  抓夠了就直接關掉 Chrome 視窗，擷取會自動收尾       │")
    print("  └─────────────────────────────────────────────────────┘")
    print()

    # ── 等 Chrome 關閉 ──────────────────────────────────────────────────────
    start = time.time()
    try:
        chrome.wait(timeout=args.timeout)
        print(f"\n[Chrome] 已關閉（歷時 {int(time.time() - start)} 秒）")
    except subprocess.TimeoutExpired:
        print(f"\n[Chrome] 到達 {args.timeout} 秒上限，關閉中...")
        chrome.terminate()
        try:
            chrome.wait(timeout=15)
        except subprocess.TimeoutExpired:
            chrome.kill()
    except KeyboardInterrupt:
        print("\n[中斷] 收尾中...")
        chrome.terminate()

    # ── 收掉 proxy ──────────────────────────────────────────────────────────
    time.sleep(2)
    mitm.send_signal(signal.SIGINT)
    try:
        mitm.wait(timeout=15)
    except subprocess.TimeoutExpired:
        mitm.kill()
    print("[Proxy] 已停止")

    # ── 整理輸出 ────────────────────────────────────────────────────────────
    traffic = consolidate(game_dir, gameid, game_url)
    out = game_dir / "traffic_raw.json"
    out.write_text(json.dumps(traffic, ensure_ascii=False, indent=2), encoding="utf-8")

    n_http = len(traffic["http"])
    n_ws = sum(len(c["frames"]) for c in traffic["websockets"])
    print()
    print("═" * 60)
    print(f"  靜態 {traffic['static_files']} 檔 / HTTP {n_http} 筆 / WS {n_ws} frames")
    print(f"  → {out}  ({out.stat().st_size // 1024} KB)")
    print("═" * 60)

    if n_http == 0 and n_ws == 0 and not args.keep_going:
        print("\n[警告] 沒有錄到任何後端流量。可能原因：")
        print("  · ssoKey 已用過或過期（game_url 只能開一次）")
        print("  · VPN 沒連到巴西 → scutil --nc list / curl ipinfo.io")
        print("  · 遊戲卡在載入畫面，沒真的進到遊戲")
        sys.exit(3)

    print(f"\n[完成] 下一步： ./.venv/bin/python game_analyze.py {gameid}")


if __name__ == "__main__":
    main()
