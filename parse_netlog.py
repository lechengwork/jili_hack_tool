#!/usr/bin/env python3
"""
parse_netlog.py — 解析 Chrome netlog（--no-proxy 擷取的產物）

用法: ./.venv/bin/python parse_netlog.py GAMEID

Chrome 用 --log-net-log --net-log-capture-mode=Everything 側錄時，
會把每條 socket 的「解密後應用層 bytes」以 base64 記進 netlog。
這支把它還原成：
  · 請求流程摘要（method / url / status / headers）— 一定抽得到
  · 後端 socket 的解密 bytes（含 /fg5/req 的請求與回應）— 盡力抽
輸出 games/GAMEID/traffic_raw.json（與 mitm 版同結構，給 game_analyze.py 用）。
"""
import argparse
import base64
import json
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).parent
GAMES_DIR = BASE / "games"

BACKEND_HINT = ("wbslot-fd", "wbslot-platform", "wbwebapi")


def load_netlog(path: Path) -> dict:
    """netlog 可能因 Chrome 沒正常關而被截斷，容錯讀取。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        return json.loads(text)
    except ValueError:
        pass
    # 截斷救援：砍到最後一個完整 event，補上結尾
    idx = text.rfind("},")
    if idx > 0:
        salvaged = text[:idx + 1] + "]}"
        try:
            return json.loads(salvaged)
        except ValueError:
            pass
    # 再退一步：只留 events 陣列能解析的部分
    marker = '"events": ['
    p = text.find(marker)
    if p >= 0:
        head = text[:p + len(marker)]
        body = text[p + len(marker):]
        last = body.rfind("},")
        if last > 0:
            try:
                return json.loads(head + body[:last + 1] + "]}")
            except ValueError:
                pass
    sys.exit(f"[錯誤] netlog 無法解析（可能全空或嚴重截斷）: {path}")


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("gameid")
    ap.add_argument("--dump-bytes", action="store_true",
                    help="把後端 socket 的解密 bytes 也存成 .bin 檔")
    args = ap.parse_args()
    gameid = args.gameid

    netlog_path = GAMES_DIR / gameid / "netlog.json"
    if not netlog_path.exists():
        sys.exit(f"[錯誤] 找不到 {netlog_path}\n  先跑： jili_capture.py {gameid} --no-proxy")

    data = load_netlog(netlog_path)
    consts = data.get("constants", {})
    ev_types = consts.get("logEventTypes", {})
    id2name = {v: k for k, v in ev_types.items()}
    events = data.get("events", [])

    print("═" * 60)
    print(f"  netlog 解析 — gameID {gameid}")
    print(f"  事件數: {len(events)}")
    print("═" * 60)

    # ── URL_REQUEST 流程（可靠）──────────────────────────────────────────
    requests = defaultdict(lambda: {"url": None, "method": None,
                                     "req_headers": None, "resp_headers": None,
                                     "status": None})
    # ── SOCKET 解密 bytes ────────────────────────────────────────────────
    sock_sent = defaultdict(bytearray)
    sock_recv = defaultdict(bytearray)
    sock_host = {}

    SENT = ev_types.get("SSL_SOCKET_BYTES_SENT")
    RECV = ev_types.get("SSL_SOCKET_BYTES_RECEIVED")
    SEND_HDR = ev_types.get("HTTP_TRANSACTION_SEND_REQUEST_HEADERS")
    READ_HDR = ev_types.get("HTTP_TRANSACTION_READ_RESPONSE_HEADERS")
    START = ev_types.get("URL_REQUEST_START_JOB")
    CONNECT = ev_types.get("SOCKET_POOL_CONNECT_JOB") or ev_types.get("TCP_CONNECT")
    HOST_RES = ev_types.get("HOST_RESOLVER_MANAGER_JOB")

    for e in events:
        src = e.get("source", {})
        sid = src.get("id")
        t = e.get("type")
        p = e.get("params") or {}

        if t == START and "url" in p:
            requests[sid]["url"] = p["url"]
        if t == SEND_HDR:
            if isinstance(p.get("headers"), list):
                requests[sid]["req_headers"] = p["headers"]
            line = p.get("line", "")
            if line:
                requests[sid]["method"] = line.split(" ", 1)[0]
            if "url" not in requests[sid] or not requests[sid]["url"]:
                # 有些版本 url 在這裡
                for h in (p.get("headers") or []):
                    if h.lower().startswith(":path:") or h.lower().startswith("host:"):
                        pass
        if t == READ_HDR and isinstance(p.get("headers"), list):
            requests[sid]["resp_headers"] = p["headers"]
            for h in p["headers"]:
                if h.startswith(":status:") or h.lower().startswith("status"):
                    digits = "".join(ch for ch in h if ch.isdigit())
                    if digits:
                        requests[sid]["status"] = int(digits[:3])

        if t in (SENT, RECV):
            b64 = p.get("bytes")
            if b64:
                raw = base64.b64decode(b64)
                (sock_sent if t == SENT else sock_recv)[sid] += raw

    # 把 socket 對應到 host（用 sent bytes 裡的 Host: 或 :authority）
    for sid, buf in sock_sent.items():
        head = bytes(buf[:2000])
        host = None
        for key in (b"\r\nhost: ", b"host: ", b":authority"):
            i = head.lower().find(key)
            if i >= 0:
                seg = head[i:i + 120]
                try:
                    txt = seg.decode("latin1")
                    host = txt.split(":authority")[-1].strip(": \r\n").split("\r")[0] \
                        if b":authority" in key else txt.split("host:")[-1].strip().split("\r")[0]
                except Exception:
                    pass
                break
        sock_host[sid] = host or "?"

    # ── 印請求流程 ───────────────────────────────────────────────────────
    from urllib.parse import urlparse
    print("\n【請求流程】(method status path)")
    fg5_req_count = 0
    empty_get = 0
    flow = []
    for sid, r in requests.items():
        if not r["url"]:
            continue
        u = urlparse(r["url"])
        if not any(h in u.netloc for h in BACKEND_HINT + ("wbgame",)):
            continue
        method = r["method"] or "?"
        status = r["status"] if r["status"] is not None else "?"
        flow.append((r["url"], method, status, u.path, u.netloc))
        if "/fg5/req" in r["url"]:
            fg5_req_count += 1
        if u.path == "/fg5/" and "wbslot-fd" in u.netloc:
            empty_get += 1
    for url, method, status, path, host in flow:
        tag = "  ← 遊戲主邏輯" if "/fg5/req" in url else ""
        print(f"  {method:<5} {str(status):>3}  {host}{path}{tag}")

    # ── 判定 ─────────────────────────────────────────────────────────────
    print("\n【判定】")
    print(f"  POST /fg5/req 次數: {fg5_req_count}")
    print(f"  空 GET /fg5/（重試迴圈）: {empty_get}")
    if fg5_req_count >= 2:
        print("  🎉 遊戲主迴圈有多次互動 = 沒有 proxy 時遊戲能跑！MITM 就是 MSG 211 的元凶")
    elif fg5_req_count == 1 and empty_get > 3:
        print("  ⚠️ 仍然 1 次 req 後進重試迴圈 = 拿掉 proxy 也沒解 → 不是 MITM 問題（可能帳號/伺服器）")
    elif fg5_req_count <= 1:
        print("  只有 ≤1 次 req，需人工確認畫面是否可玩")

    # ── 後端 socket 解密 bytes ───────────────────────────────────────────
    print("\n【後端 socket 解密 bytes】")
    game_dir = GAMES_DIR / gameid
    backend_socks = [sid for sid in set(list(sock_sent) + list(sock_recv))
                     if any(h in sock_host.get(sid, "") for h in BACKEND_HINT)]
    for sid in backend_socks:
        s = bytes(sock_sent.get(sid, b""))
        rv = bytes(sock_recv.get(sid, b""))
        proto = "h2" if s[:3] == b"PRI" else ("h1" if b"HTTP/1" in s[:400] or s[:4] in (b"POST", b"GET ") else "?")
        print(f"  socket {sid}  host={sock_host.get(sid)}  proto={proto}  "
              f"sent={len(s)}B recv={len(rv)}B")
        if args.dump_bytes:
            (game_dir / f"sock_{sid}_sent.bin").write_bytes(s)
            (game_dir / f"sock_{sid}_recv.bin").write_bytes(rv)

    # ── 輸出 traffic_raw.json（流程層，body 之後補）───────────────────────
    http_entries = []
    for url, method, status, path, host in flow:
        http_entries.append({
            "kind": "http", "method": method, "url": url,
            "status": status if isinstance(status, int) else 0,
            "note": "netlog flow（body 在 socket dump 裡）",
        })
    out = {
        "gameid": gameid,
        "captured_at": "",
        "capture_method": "chrome netlog (no-proxy)",
        "http": http_entries,
        "websockets": [],
        "fg5_req_count": fg5_req_count,
        "backend_sockets": len(backend_socks),
    }
    (game_dir / "traffic_raw.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[輸出] {game_dir / 'traffic_raw.json'}")
    if not args.dump_bytes:
        print("  （加 --dump-bytes 可把 socket 解密 bytes 存成 .bin 進一步分析）")


if __name__ == "__main__":
    main()
