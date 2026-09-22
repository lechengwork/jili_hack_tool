#!/usr/bin/env python3
"""
game_analyze.py — Step 2: 分析擷取到的流量，產出 game_config.json

用法: .venv/bin/python game_analyze.py GAMEID [--verbose]

讀取 games/GAMEID/traffic_raw.json，輸出 games/GAMEID/game_config.json。

因為 JILI 的協定目前尚未確認，這支腳本的首要工作是「回報偵測到什麼」：
  · 走 HTTP 還是 WebSocket
  · WS frame 是文字(JSON) 還是二進位
  · 哪些 endpoint / action 重複出現（= 遊戲主迴圈）
分析結果會印在畫面上，並存進 game_config.json 的 protocol 區塊。
"""
import argparse
import base64
import binascii
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).parent
GAMES_DIR = BASE / "games"


def load_traffic(gameid: str) -> dict:
    p = GAMES_DIR / gameid / "traffic_raw.json"
    if not p.exists():
        sys.exit(f"[錯誤] 找不到 {p}\n  先執行： .venv/bin/python jili_capture.py {gameid}")
    return json.loads(p.read_text(encoding="utf-8"))


def try_json(text):
    if not text:
        return None
    t = text.strip()
    if not t or t[0] not in "{[":
        return None
    try:
        return json.loads(t)
    except ValueError:
        return None


# ── WS frame 分析 ────────────────────────────────────────────────────────────

def sniff_binary(hex_str: str) -> dict:
    """猜二進位 frame 的格式。"""
    try:
        b = binascii.unhexlify(hex_str)
    except (ValueError, binascii.Error):
        return {"format": "unparseable"}
    if not b:
        return {"format": "empty"}

    info = {"len": len(b), "head": b[:8].hex()}
    # SFS2X: 0x80 + uint16 length（fachai 用的格式）
    if b[0] == 0x80 and len(b) >= 3:
        declared = int.from_bytes(b[1:3], "big")
        if declared == len(b) - 3:
            info["format"] = "sfs2x"
            return info
    # protobuf 常見開頭：field 1 varint / length-delimited
    if b[0] in (0x08, 0x0a, 0x12, 0x1a):
        info["format"] = "protobuf?"
        return info
    # gzip / zlib
    if b[:2] == b"\x1f\x8b":
        info["format"] = "gzip"
        return info
    if b[0] == 0x78 and b[1] in (0x01, 0x9c, 0xda):
        info["format"] = "zlib"
        return info
    # 其實是 UTF-8 文字
    try:
        s = b.decode("utf-8")
        if try_json(s) is not None:
            info["format"] = "json-in-binary"
            info["sample"] = s[:200]
        else:
            info["format"] = "utf8-text"
            info["sample"] = s[:200]
        return info
    except UnicodeDecodeError:
        pass
    info["format"] = "unknown-binary"
    return info


def analyze_ws(conns: list, verbose: bool) -> dict:
    result = {"connections": [], "frame_total": 0, "binary": False}
    for c in conns:
        frames = c.get("frames", [])
        result["frame_total"] += len(frames)
        sent = [f for f in frames if f["dir"] == "SEND"]
        recv = [f for f in frames if f["dir"] == "RECV"]
        binary = any(f.get("binary") for f in frames)
        if binary:
            result["binary"] = True

        entry = {
            "url": c["url"],
            "frames": len(frames),
            "sent": len(sent),
            "recv": len(recv),
            "binary": binary,
        }

        if binary:
            fmts = Counter()
            for f in frames[:200]:
                if f.get("binary"):
                    fmts[sniff_binary(f["hex"]).get("format", "?")] += 1
            entry["binary_formats"] = dict(fmts)
            samples = [f["hex"][:80] for f in frames[:5] if f.get("binary")]
            entry["hex_samples"] = samples
        else:
            # 文字 frame：找出 action/cmd 欄位
            keys = Counter()
            actions = Counter()
            for f in frames:
                obj = try_json(f.get("text", ""))
                if isinstance(obj, dict):
                    for k in obj:
                        keys[k] += 1
                    for ak in ("cmd", "action", "act", "type", "c", "a",
                               "cmdType", "Cmd", "Action", "msgId", "id"):
                        if ak in obj:
                            actions[f"{ak}={obj[ak]}"] += 1
            entry["top_keys"] = dict(keys.most_common(12))
            entry["top_actions"] = dict(actions.most_common(15))
            entry["text_samples"] = [f.get("text", "")[:200] for f in frames[:5]]

        result["connections"].append(entry)
        if verbose:
            print(json.dumps(entry, ensure_ascii=False, indent=2)[:2000])
    return result


# ── HTTP 分析 ────────────────────────────────────────────────────────────────

def analyze_http(entries: list, verbose: bool) -> dict:
    by_path = defaultdict(list)
    for e in entries:
        by_path[urlparse(e["url"]).path].append(e)

    endpoints = []
    for path, group in sorted(by_path.items(), key=lambda kv: -len(kv[1])):
        methods = Counter(e["method"] for e in group)
        statuses = Counter(e["status"] for e in group)
        ep = {
            "path": path,
            "count": len(group),
            "methods": dict(methods),
            "statuses": dict(statuses),
        }
        # 找請求裡的 action 欄位（推測遊戲主迴圈）
        actions = Counter()
        for e in group:
            obj = try_json(e.get("request_body") or "")
            if isinstance(obj, dict):
                for ak in ("action", "cmd", "act", "type", "Cmd", "Action", "cmdType"):
                    if ak in obj:
                        actions[f"{ak}={obj[ak]}"] += 1
        if actions:
            ep["actions"] = dict(actions.most_common(10))
        sample = group[0]
        ep["sample_request"] = (sample.get("request_body") or "")[:400]
        ep["sample_response"] = (sample.get("response_body") or "")[:400]
        endpoints.append(ep)
        if verbose:
            print(f"\n--- {path} ({len(group)}x)")
            print("  req :", ep["sample_request"][:250])
            print("  resp:", ep["sample_response"][:250])
    return {"endpoints": endpoints, "total": len(entries)}


def guess_spin_loop(http_res: dict, ws_res: dict) -> dict:
    """挑出最可能是 spin 主迴圈的 endpoint/action。"""
    guess = {"transport": None, "target": None, "reason": ""}
    ws_frames = ws_res.get("frame_total", 0)
    http_count = http_res.get("total", 0)

    if ws_frames > http_count and ws_frames > 4:
        guess["transport"] = "ws"
        conns = ws_res.get("connections", [])
        if conns:
            top = max(conns, key=lambda c: c["frames"])
            guess["target"] = top["url"]
            if top.get("top_actions"):
                guess["reason"] = f"最頻繁 action: {list(top['top_actions'])[:3]}"
            else:
                guess["reason"] = f"{top['frames']} frames"
    elif http_count > 0:
        guess["transport"] = "http"
        eps = http_res.get("endpoints", [])
        # 排除純遙測
        real = [e for e in eps if "/event/" not in e["path"]]
        if real:
            top = real[0]
            guess["target"] = top["path"]
            guess["reason"] = f"呼叫 {top['count']} 次"
    return guess


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("gameid")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    gameid = args.gameid
    t = load_traffic(gameid)

    print("═" * 60)
    print(f"  JILI Analyze — gameID {gameid}")
    print("═" * 60)
    print(f"  擷取時間 : {t.get('captured_at')}")
    print(f"  靜態檔數 : {t.get('static_files')}")
    print(f"  HTTP 筆數: {len(t.get('http', []))}")
    ws_conns = t.get("websockets", [])
    print(f"  WS 連線  : {len(ws_conns)} 條 / {sum(len(c.get('frames', [])) for c in ws_conns)} frames")
    print("─" * 60)

    http_res = analyze_http(t.get("http", []), args.verbose)
    ws_res = analyze_ws(ws_conns, args.verbose)
    guess = guess_spin_loop(http_res, ws_res)

    # ── 畫面報告 ────────────────────────────────────────────────────────
    print("\n【HTTP endpoints】")
    if not http_res["endpoints"]:
        print("  （無）")
    for ep in http_res["endpoints"][:15]:
        acts = f"  actions={list(ep.get('actions', {}))[:3]}" if ep.get("actions") else ""
        print(f"  {ep['count']:4d}x  {list(ep['methods'])[0]:6s} {ep['path']}{acts}")

    print("\n【WebSocket】")
    if not ws_res["connections"]:
        print("  （無）")
    for c in ws_res["connections"]:
        kind = "binary" if c["binary"] else "text"
        print(f"  {c['url']}")
        print(f"    {c['frames']} frames ({c['sent']} send / {c['recv']} recv), {kind}")
        if c.get("binary_formats"):
            print(f"    格式推測: {c['binary_formats']}")
        if c.get("top_actions"):
            print(f"    常見 action: {list(c['top_actions'])[:6]}")

    print("\n【協定判定】")
    if guess["transport"]:
        print(f"  傳輸: {guess['transport'].upper()}")
        print(f"  主迴圈: {guess['target']}  ({guess['reason']})")
    else:
        print("  ⚠ 無法判定 — 沒有錄到後端流量")

    # ── 產出 game_config.json ───────────────────────────────────────────
    cfg = {
        "gameid": gameid,
        "game_url": t.get("game_url"),
        "captured_at": t.get("captured_at"),
        "protocol": {
            "transport": guess["transport"] or "unknown",
            "spin_target": guess["target"],
            "ws_binary": ws_res.get("binary", False),
        },
        "http": {
            "endpoints": [
                {k: v for k, v in ep.items()
                 if k in ("path", "count", "methods", "actions")}
                for ep in http_res["endpoints"]
            ],
            # 完整 replay 資料：path → 依序回應
            "replay": build_http_replay(t.get("http", [])),
        },
        "websocket": {
            "connections": [
                {k: v for k, v in c.items()
                 if k in ("url", "frames", "sent", "recv", "binary", "binary_formats")}
                for c in ws_res["connections"]
            ],
            "replay": build_ws_replay(ws_conns),
        },
    }

    out = GAMES_DIR / gameid / "game_config.json"
    out.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[輸出] {out}  ({out.stat().st_size // 1024} KB)")

    if guess["transport"] is None:
        print("\n[警告] 協定未判定，server 只能提供靜態資源，遊戲跑不起來。")
        sys.exit(3)
    print(f"\n[完成] 下一步： .venv/bin/python gen_server.py {gameid}")


def build_http_replay(entries: list) -> dict:
    """path → [依序的回應]，server 依序循環播放。"""
    replay = defaultdict(list)
    for e in entries:
        path = urlparse(e["url"])._replace(query="").path
        replay[path].append({
            "status": e.get("status", 200),
            "content_type": e.get("content_type", "application/json"),
            "body": e.get("response_body"),
            "body_b64": e.get("response_b64"),
            "request_body": e.get("request_body"),
        })
    return dict(replay)


def build_ws_replay(conns: list) -> list:
    """保留每條連線完整 frame 序列，server 照順序回放 RECV。"""
    out = []
    for c in conns:
        out.append({
            "url": c["url"],
            "frames": [
                {
                    "dir": f["dir"],
                    "binary": f.get("binary", False),
                    "hex": f.get("hex"),
                    "text": f.get("text"),
                }
                for f in c.get("frames", [])
            ],
        })
    return out


if __name__ == "__main__":
    main()
