#!/usr/bin/env python3
"""
extract_fg5.py — 從 Everything netlog 抽出 /fg5/req 的請求與加密回應

/fg5/req 走 HTTP/2：路徑/標頭是 HPACK 壓縮、body 在 DATA frame。
本工具解 h2 框架 + HPACK，配對出每筆 spin 的 (protobuf 請求, 加密回應)。

用法: ./.venv/bin/python extract_fg5.py GAMEID [--netlog PATH]
輸出: games/GAMEID/fg5_exchanges.json
"""
import argparse, base64, json, sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).parent
GAMES_DIR = BASE / "games"
PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"


def read_event_types(path):
    head = open(path, encoding="utf-8", errors="replace").read(300000)
    ci = head.find('"events"')
    consts = json.loads(head[head.find('{'):ci].rstrip().rstrip(',') + "}")
    return consts["constants"]["logEventTypes"]


def iter_frames(buf: bytes):
    """逐一 yield HTTP/2 frame: (length, type, flags, stream_id, payload)。"""
    i = 0
    if buf[:len(PREFACE)] == PREFACE:
        i = len(PREFACE)
    while i + 9 <= len(buf):
        ln = int.from_bytes(buf[i:i+3], "big")
        typ = buf[i+3]; flags = buf[i+4]
        sid = int.from_bytes(buf[i+5:i+9], "big") & 0x7fffffff
        payload = buf[i+9:i+9+ln]
        if len(payload) < ln:
            break
        yield ln, typ, flags, sid, payload
        i += 9 + ln


def strip_padding(payload, flags, has_priority=False):
    """處理 HEADERS/DATA 的 PADDED(0x8) 與 HEADERS 的 PRIORITY(0x20)。"""
    idx = 0; pad = 0
    if flags & 0x08:  # PADDED
        pad = payload[0]; idx = 1
    if has_priority and (flags & 0x20):  # PRIORITY (HEADERS only)
        idx += 5
    end = len(payload) - pad
    return payload[idx:end]


def decode_stream_dir(buf: bytes):
    """解一個方向的 h2：回傳 {stream_id: {"headers":[(k,v)], "data":bytes}}。"""
    from hpack import Decoder
    dec = Decoder()
    streams = defaultdict(lambda: {"headers": [], "data": bytearray()})
    # HEADERS/CONTINUATION 需按順序餵給同一個 HPACK decoder
    pending = {}  # sid -> accumulated header block (for CONTINUATION)
    for ln, typ, flags, sid, payload in iter_frames(buf):
        if typ == 0x1:  # HEADERS
            block = strip_padding(payload, flags, has_priority=True)
            if flags & 0x04:  # END_HEADERS
                try: streams[sid]["headers"] = dec.decode(block)
                except Exception: pass
            else:
                pending[sid] = bytearray(block)
        elif typ == 0x9:  # CONTINUATION
            if sid in pending:
                pending[sid] += payload
                if flags & 0x04:
                    try: streams[sid]["headers"] = dec.decode(bytes(pending.pop(sid)))
                    except Exception: pending.pop(sid, None)
        elif typ == 0x0:  # DATA
            streams[sid]["data"] += strip_padding(payload, flags)
    return streams


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("gameid")
    ap.add_argument("--netlog", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    netlog = Path(args.netlog) if args.netlog else GAMES_DIR / args.gameid / "netlog.json"
    if not netlog.exists():
        sys.exit(f"[錯誤] 找不到 {netlog}")

    import ijson, ijson.common
    et = read_event_types(netlog)
    SENT = et.get("SSL_SOCKET_BYTES_SENT"); RECV = et.get("SSL_SOCKET_BYTES_RECEIVED")
    sent = defaultdict(bytearray); recv = defaultdict(bytearray); n = 0
    try:
        for ev in ijson.items(open(netlog, encoding="utf-8", errors="replace"), "events.item"):
            n += 1; t = ev.get("type"); p = ev.get("params") or {}
            if t in (SENT, RECV):
                b = p.get("bytes")
                if b:
                    sid = ev["source"]["id"]
                    (sent if t == SENT else recv)[sid] += base64.b64decode(b)
    except ijson.common.IncompleteJSONError:
        pass
    print(f"[掃] events {n}，sockets={len(set(list(sent)+list(recv)))}")

    exchanges = []
    for sid in sorted(set(list(sent) + list(recv))):
        sbuf = bytes(sent.get(sid, b"")); rbuf = bytes(recv.get(sid, b""))
        is_h2 = sbuf[:len(PREFACE)] == PREFACE
        if not is_h2:
            continue
        try:
            req_streams = decode_stream_dir(sbuf)
            resp_streams = decode_stream_dir(rbuf)
        except Exception as e:
            print(f"  [socket {sid}] 解析失敗: {e}"); continue
        for stid, req in req_streams.items():
            hdrs = dict(req["headers"])
            path = hdrs.get(":path", "")
            if path != "/fg5/req":
                continue
            resp = resp_streams.get(stid, {"headers": [], "data": b""})
            rhdrs = dict(resp["headers"])
            exchanges.append({
                "socket": sid, "stream": stid,
                "authority": hdrs.get(":authority", ""),
                "method": hdrs.get(":method", ""),
                "req_body_hex": bytes(req["data"]).hex(),
                "req_body_len": len(req["data"]),
                "resp_status": rhdrs.get(":status", ""),
                "resp_body_hex": bytes(resp["data"]).hex(),
                "resp_body_len": len(resp["data"]),
            })

    out = Path(args.out) if args.out else GAMES_DIR / args.gameid / "fg5_exchanges.json"
    out.write_text(json.dumps(exchanges, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[輸出] {len(exchanges)} 筆 /fg5/req → {out}")
    from collections import Counter
    if exchanges:
        print("\n=== 摘要 ===")
        for e in exchanges[:8]:
            print(f"  stream {e['stream']:>3}  req {e['req_body_len']}B → {e['resp_status']} {e['resp_body_len']}B")
        print(f"\n  請求長度分布: {dict(Counter(e['req_body_len'] for e in exchanges))}")
        print(f"  回應長度分布: {dict(Counter(e['resp_body_len'] for e in exchanges))}")
        print(f"  authority: {set(e['authority'] for e in exchanges)}")


if __name__ == "__main__":
    main()
