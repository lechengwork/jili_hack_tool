#!/usr/bin/env python3
# pp_capture.py — 參數化版的 pp_capture_live.py（rtp/jili）。
#   用法: pp_capture.py <game_url> <out_dir> [seconds]
# 差別只在:輸出目錄可指定(不再寫死 captured_pg,免蓋掉 PG 的 _api.json),
# 並多印 frame 內文以判斷是否被 jscrambler 擋(tamper/受限)。
from playwright.sync_api import sync_playwright
from urllib.parse import urlsplit, unquote
from pathlib import Path
import time, json, sys
URL = sys.argv[1]
OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
SECS = int(sys.argv[3]) if len(sys.argv) > 3 else 120
api = []; hosts = {}; saved = 0; seen = set()
SKIP = ("google", "googletagmanager", "doubleclick", "analytics", "cloudflareinsights")
def skip(h): return any(s in h for s in SKIP)
APIK = ("auth/session", "verifyoperator", "gameservice", "playgame.do", "html5game",
        "spin", "/game-api", "/web-api", "index.json", "gameinfo", "getgame",
        "/v1/", "/v2/", "/fg", "/req", "sso", "login")
with sync_playwright() as p:
    b = p.chromium.launch(headless=False,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--disable-quic",
              "--ignore-certificate-errors"])
    ctx = b.new_context(viewport={"width": 1366, "height": 900},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    ctx.add_init_script("Object.defineProperty(navigator,\"webdriver\",{get:()=>undefined});")
    pg = ctx.new_page()
    def onresp(r):
        global saved
        u = r.url; sp = urlsplit(u); host = sp.netloc.lower()
        if not host or skip(host): return
        hosts[host] = hosts.get(host, 0) + 1
        low = u.lower()
        if any(k in low for k in APIK):
            try: body = r.text()[:2000000]
            except Exception: body = ""
            api.append({"status": r.status, "method": r.request.method, "url": u[:220], "resp": body})
        if u in seen: return
        rel = unquote(sp.path.lstrip("/")).replace("..", "_") or "index"
        dst = OUT / host / rel
        try:
            data = r.body()
            if data and len(data) < 10_000_000:
                dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(data); saved += 1; seen.add(u)
        except Exception: pass
    ctx.on("response", onresp)
    try: pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e: print("goto:", str(e)[:150], flush=True)
    def frames(tag):
        print(f"--- frames @ {tag} ---", flush=True)
        for fr in pg.frames:
            try: t = fr.evaluate("document.body?document.body.innerText.slice(0,220):\"\"")
            except Exception: t = "(na)"
            print(f"  [{fr.url[:100]}] {t!r}", flush=True)
    time.sleep(12); frames("12s")
    try:
        _urls = [fr.url for fr in pg.frames if fr.url and fr.url.startswith("http")]
        (OUT / "_launch_url.txt").write_text("\n".join(_urls))
        print("[launch] saved", len(_urls), "frame urls ->", OUT / "_launch_url.txt", flush=True)
        for _u in _urls: print("  FRAME:", _u, flush=True)
    except Exception as _e:
        print("launch-url save err:", _e, flush=True)
    print("HOSTS:", dict(sorted(hosts.items(), key=lambda x: -x[1])[:14]), flush=True)
    loops = max(1, (SECS - 12) // 12)
    for i in range(loops):
        time.sleep(12)
        if not b.is_connected(): break
        if i % 3 == 2: frames(f"{(i + 2) * 12}s")
        print(f"  assets={saved} api={len(api)}", flush=True)
    json.dump(api, open(OUT / "_api.json", "w"), ensure_ascii=False, indent=2)
    print("=== API hits ===")
    for a in api[:24]: print(" ", a["status"], a["method"], a["url"])
    print(f"[done] assets={saved} api={len(api)} out={OUT}", flush=True)
    try: b.close()
    except Exception: pass
