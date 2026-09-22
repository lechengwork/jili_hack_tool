"""
jili_mitm.py — mitmproxy addon：擷取 JILI 靜態資源 + 全部後端流量

不要直接執行，由 jili_capture.py 透過 mitmdump 載入：
    JILI_GAMEID=696 JILI_OUT=/path/to/games mitmdump -s jili_mitm.py

為什麼用 mitmproxy 而不是 Playwright：
JILI 的 JS 過 jscrambler，會偵測 CDP／自動化瀏覽器並中止載入。
mitmproxy 是網路層的，配上真實 Chrome 就完全看不出是自動化環境。

產出：
  <OUT>/<GAMEID>/static/...      該遊戲靜態資源
  <OUT>/shared/...               astarte2 / smallicon 共用資源
  <OUT>/<GAMEID>/traffic.jsonl   後端流量（逐筆 append，中途被砍也不會全丟）
"""
import json
import os
import re
import threading
import time
import urllib.parse
from pathlib import Path

from mitmproxy import http

GAMEID = os.environ.get("JILI_GAMEID", "unknown")
OUT = Path(os.environ.get("JILI_OUT", "./games"))

GAME_DIR = OUT / GAMEID
STATIC_DIR = GAME_DIR / "static"
SHARED_DIR = OUT / "shared"
TRAFFIC = GAME_DIR / "traffic.jsonl"

# 這些路徑前綴的資源跨遊戲共用
SHARED_PREFIXES = ("/astarte2/", "/smallicon/")

# 第三方，完全略過
SKIP_HOST = re.compile(
    r"(google|gstatic|googleapis|googletagmanager|doubleclick|jscrambler|"
    r"facebook|sentry|cloudflareinsights|mozilla|apple|digicert|gvt1|gvt2)", re.I)

# 後端 host：這些 host 的所有流量都要錄（含 POST）
BACKEND = re.compile(r"(wbslot-fd|wbslot-platform|wbwebapi|/webservice/)", re.I)

_lock = threading.Lock()
_stats = {"static": 0, "api": 0, "ws": 0, "skipped": 0}


def _log_line(obj: dict):
    with _lock:
        TRAFFIC.parent.mkdir(parents=True, exist_ok=True)
        with open(TRAFFIC, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _target_path(host: str, path: str) -> Path:
    path = urllib.parse.unquote(path)
    if path in ("", "/") or path.endswith("/"):
        path += "index.html"
    rel = path.lstrip("/")
    for pre in SHARED_PREFIXES:
        if path.startswith(pre):
            return SHARED_DIR / rel
    return STATIC_DIR / rel


def _body_fields(content: bytes) -> dict:
    """回傳可 JSON 序列化的 body 欄位：能解 utf-8 就存文字，否則存 hex。"""
    if content is None:
        return {"text": None, "hex": None}
    try:
        return {"text": content.decode("utf-8"), "hex": None}
    except UnicodeDecodeError:
        return {"text": None, "hex": content.hex()}


# ── HTTP ─────────────────────────────────────────────────────────────────────

def response(flow: http.HTTPFlow):
    url = flow.request.pretty_url
    host = flow.request.pretty_host
    path = flow.request.path.split("?")[0]

    if SKIP_HOST.search(host):
        _stats["skipped"] += 1
        return

    is_backend = bool(BACKEND.search(host) or BACKEND.search(flow.request.path))

    # 後端流量：不論方法、不論狀態碼，全部錄
    if is_backend:
        req = _body_fields(flow.request.content)
        resp = _body_fields(flow.response.content if flow.response else None)
        _log_line({
            "kind": "http",
            "ts": time.time(),
            "method": flow.request.method,
            "url": url,
            "status": flow.response.status_code if flow.response else 0,
            "content_type": flow.response.headers.get("content-type", "") if flow.response else "",
            "http_version": flow.response.http_version if flow.response else "",
            "request_headers": dict(flow.request.headers),
            "response_headers": dict(flow.response.headers) if flow.response else {},
            "request_body": req["text"],
            "request_b64": req["hex"],
            "response_body": resp["text"],
            "response_b64": resp["hex"],
        })
        _stats["api"] += 1
        print(f"🔌 [API] {flow.request.method} {path} → "
              f"{flow.response.status_code if flow.response else '?'}")
        return

    # 靜態資源
    if not flow.response or flow.response.status_code != 200:
        return
    content = flow.response.content
    if not content:
        return

    fp = _target_path(host, path)
    try:
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_bytes(content)
        _stats["static"] += 1
        if _stats["static"] % 20 == 0:
            print(f"📁 [靜態] 已存 {_stats['static']} 個檔案")
    except OSError as e:
        print(f"⚠️  [存檔失敗] {path}: {e}")


def error(flow):
    """連線層錯誤：TLS reset、逾時、被中斷 —— 這些不會走到 response()。"""
    try:
        url = flow.request.pretty_url
        host = flow.request.pretty_host
    except Exception:
        return
    if SKIP_HOST.search(host):
        return
    msg = str(getattr(flow, "error", "")) or "unknown"
    _log_line({"kind": "error", "ts": time.time(), "url": url, "error": msg})
    _stats["error"] = _stats.get("error", 0) + 1
    print(f"❌ [連線錯誤] {url[:80]} :: {msg}")


# ── WebSocket ────────────────────────────────────────────────────────────────

def websocket_start(flow: http.HTTPFlow):
    print(f"🔗 [WS 連線] {flow.request.pretty_url}")
    _log_line({"kind": "ws_open", "ts": time.time(),
               "url": flow.request.pretty_url})


def websocket_message(flow: http.HTTPFlow):
    msg = flow.websocket.messages[-1]
    entry = {
        "kind": "ws_msg",
        "ts": time.time(),
        "url": flow.request.pretty_url,
        "dir": "SEND" if msg.from_client else "RECV",
        "binary": not msg.is_text,
    }
    if msg.is_text:
        entry["text"] = msg.text
    else:
        entry["hex"] = bytes(msg.content).hex()
    _log_line(entry)
    _stats["ws"] += 1
    if _stats["ws"] % 25 == 0:
        print(f"🔗 [WS] 已錄 {_stats['ws']} frames")


def websocket_end(flow: http.HTTPFlow):
    _log_line({"kind": "ws_close", "ts": time.time(),
               "url": flow.request.pretty_url})


# ── 生命週期 ─────────────────────────────────────────────────────────────────

def running():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    print("═" * 58)
    print(f"  JILI mitm addon — gameID {GAMEID}")
    print(f"  靜態 → {STATIC_DIR}")
    print(f"  共用 → {SHARED_DIR}")
    print(f"  流量 → {TRAFFIC}")
    print("═" * 58)


def done():
    print("─" * 58)
    print(f"  靜態 {_stats['static']} 檔 / API {_stats['api']} 筆 / "
          f"WS {_stats['ws']} frames / 連線錯誤 {_stats.get('error', 0)} / "
          f"略過 {_stats['skipped']}")
    print("─" * 58)
