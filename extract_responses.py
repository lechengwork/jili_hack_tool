#!/usr/bin/env python3
"""JILI 回應萃取流水線(繞過加密)。

原理:遊戲把每筆「解密後」的回應以 JSON 快取在 renderer heap:
    {"type":N,"ret":0,"error_msg":"","data":[<原始 protobuf 位元組>]}
本工具:全 dump 遊戲 renderer heap → 抓所有這種 JSON blob → 解析 data 的 protobuf
        → 去重 → 輸出 games/<gid>/responses.jsonl(結構化)+ 螢幕摘要。

用法:
    ./.venv/bin/python -u extract_responses.py <gameid>              # 現場 dump + 解析
    ./.venv/bin/python -u extract_responses.py <gameid> --dump-file /tmp/x.bin   # 解析既有 dump
需求:遊戲已用 run_cft.sh 開著、已進真實畫面、已轉過幾把(要驗證欄位就轉到中獎)。
"""
import sys, os, re, json, struct, subprocess, time

# ---------------- Frida: 全 dump 最大 renderer ----------------
DUMP_JS = r"""
rpc.exports={
  info:function(){var rs=Process.enumerateRanges('rw-');var t=0;for(var i=0;i<rs.length;i++)t+=rs[i].size;return Math.round(t/1048576);},
  dump:function(path){var f=new File(path,"wb");var tot=0;var rs=Process.enumerateRanges('rw-');
    for(var i=0;i<rs.length;i++){var r=rs[i];try{var b=r.base.readByteArray(r.size);if(b){f.write(b);tot+=r.size;}}catch(e){}}
    f.close();return Math.round(tot/1048576);}
};
"""

def _attach_biggest():
    import frida
    def rp():
        o = subprocess.check_output(["ps","aux"]).decode()
        return [int(l.split()[1]) for l in o.splitlines()
                if 'type=renderer' in l and 'chrome-mac-arm64' in l]
    best = None
    for pid in rp():
        try:
            s = frida.attach(pid); sc = s.create_script(DUMP_JS); sc.load()
            mb = sc.exports_sync.info()
            if best is None or mb > best[0]:
                if best: best[3].detach()
                best = (mb, pid, sc, s)
            else:
                s.detach()
        except Exception:
            pass
    if not best:
        print("找不到 renderer——先 run_cft.sh 開遊戲並進畫面"); sys.exit(1)
    return best  # (mb, pid, sc, s)

def dump_renderer(binpath):
    mb, pid, sc, s = _attach_biggest()
    print(f"[dump] renderer={pid} ({mb}MB) → {binpath} ...", flush=True)
    t0 = time.time()
    got = sc.exports_sync.dump(binpath)
    print(f"[dump] {got}MB in {time.time()-t0:.1f}s", flush=True)
    s.detach()

def watch_dump(outdir, seconds):
    """連拍模式:對遊戲 renderer 每 ~1.5s dump 一張,連拍 seconds 秒。回傳快照檔清單。"""
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        if f.startswith("w_") and f.endswith(".bin"): os.remove(os.path.join(outdir, f))
    mb, pid, sc, s = _attach_biggest()
    print(f"[watch] renderer={pid} ({mb}MB) 連拍 {seconds}s——現在去觸發免費遊戲/bonus,玩完等它結束", flush=True)
    files = []; t_end = time.time() + seconds; i = 0
    while time.time() < t_end:
        p = os.path.join(outdir, f"w_{i:03d}.bin")
        try:
            sc.exports_sync.dump(p); files.append(p)
            if i % 5 == 0: print(f"  [watch] #{i} ...", flush=True)
        except Exception as e:
            print(f"  [watch] #{i} fail {e}", flush=True)
        i += 1
    s.detach()
    print(f"[watch] 連拍結束,共 {len(files)} 張", flush=True)
    return files

# ---------------- 抓 JSON blob ----------------
def find_blobs(data):
    """回傳 list of dict: {type,ret,error_msg,data:[...]} (只收含 data 陣列的)"""
    out = []
    for m in re.finditer(rb'\{"type":', data):
        st = m.start()
        depth = 0; end = None
        for j in range(st, min(st+65536, len(data))):
            c = data[j]
            if c == 0x7b: depth += 1
            elif c == 0x7d:
                depth -= 1
                if depth == 0: end = j+1; break
            elif c < 9 or c > 126: break
        if end is None: continue
        try:
            obj = json.loads(data[st:end].decode('utf-8'))
        except Exception:
            continue
        if isinstance(obj, dict) and 'data' in obj and isinstance(obj['data'], list):
            out.append(obj)
    return out

# ---------------- protobuf 解析 ----------------
def _rv(b, i):
    v = 0; sh = 0
    while True:
        x = b[i]; i += 1
        v |= (x & 0x7f) << sh
        if not (x & 0x80): break
        sh += 7
    return v, i

def _is_msg(sub):
    if not sub: return False
    j = 0
    try:
        while j < len(sub):
            t = sub[j]; f = t >> 3; w = t & 7; j += 1
            if f == 0 or w in (3,4,6,7): return False
            if w == 0: _, j = _rv(sub, j)
            elif w == 2:
                l, j = _rv(sub, j); j += l
            elif w == 5: j += 4
            elif w == 1: j += 8
        return j == len(sub)
    except Exception:
        return False

def decode_pb(b):
    """回傳 list of {field, kind, value}"""
    out = []; i = 0
    while i < len(b):
        try:
            tag, i = _rv(b, i)
        except Exception:
            break
        fld = tag >> 3; wt = tag & 7
        if wt == 0:
            v, i = _rv(b, i)
            out.append({"f": fld, "k": "varint", "v": v})
        elif wt == 2:
            ln, i = _rv(b, i); sub = b[i:i+ln]; i += ln
            printable = bool(sub) and all(32 <= x < 127 for x in sub)
            if _is_msg(sub) and not printable and sub:
                out.append({"f": fld, "k": "msg", "v": decode_pb(sub)})
            elif printable:
                out.append({"f": fld, "k": "str", "v": sub.decode()})
            else:
                out.append({"f": fld, "k": "bytes", "v": list(sub)})
        elif wt == 1:
            raw = b[i:i+8]; i += 8
            out.append({"f": fld, "k": "f64",
                        "v": struct.unpack("<d", raw)[0],
                        "i64": struct.unpack("<q", raw)[0]})
        elif wt == 5:
            raw = b[i:i+4]; i += 4
            out.append({"f": fld, "k": "f32", "v": struct.unpack("<f", raw)[0]})
        else:
            break
    return out

def pretty(tree, ind=0):
    pad = "  " * ind; lines = []
    for e in tree:
        if e["k"] == "msg":
            lines.append(f"{pad}f{e['f']} msg:")
            lines.append(pretty(e["v"], ind+1))
        elif e["k"] == "f64":
            lines.append(f"{pad}f{e['f']} f64={e['v']}  (i64={e['i64']})")
        else:
            lines.append(f"{pad}f{e['f']} {e['k']}={e['v']!r}")
    return "\n".join(lines)

# ---------------- main ----------------
def main():
    if len(sys.argv) < 2:
        print("用法: extract_responses.py <gameid> [--dump-file PATH]"); return
    gid = sys.argv[1]
    blobs = []
    if "--watch" in sys.argv:
        idx = sys.argv.index("--watch")
        secs = int(sys.argv[idx+1]) if len(sys.argv) > idx+1 and sys.argv[idx+1].isdigit() else 60
        files = watch_dump("/tmp/heaploop", secs)
        print(f"[scan] 掃 {len(files)} 張快照找 JSON 回應 blob ...", flush=True)
        for fp in files:
            blobs += find_blobs(open(fp, "rb").read())
    else:
        binpath = f"/tmp/heap_{gid}.bin"
        if "--dump-file" in sys.argv:
            binpath = sys.argv[sys.argv.index("--dump-file")+1]
        else:
            dump_renderer(binpath)
        data = open(binpath, "rb").read()
        print(f"[scan] {len(data)//1048576}MB, 找 JSON 回應 blob ...", flush=True)
        blobs = find_blobs(data)
    # 去重(同 type+data)
    seen = set(); uniq = []
    for o in blobs:
        key = (o.get("type"), tuple(o["data"]))
        if key in seen: continue
        seen.add(key); uniq.append(o)
    # 只留 data 非空的(有內容的回應)
    uniq = [o for o in uniq if o["data"]]
    print(f"[scan] 去重後 {len(uniq)} 筆有內容的回應\n", flush=True)

    outdir = f"games/{gid}"; os.makedirs(outdir, exist_ok=True)
    fout = open(f"{outdir}/responses.jsonl", "w", encoding="utf-8")
    by_type = {}
    for o in sorted(uniq, key=lambda x: (x.get("type", 0), len(x["data"]))):
        t = o.get("type"); by_type.setdefault(t, 0); by_type[t] += 1
        tree = decode_pb(bytes(o["data"]))
        rec = {"type": t, "ret": o.get("ret"), "len": len(o["data"]),
               "raw": o["data"], "decoded": tree}
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"===== type:{t} ret:{o.get('ret')} len:{len(o['data'])} =====")
        print(pretty(tree))
        print()
    fout.close()
    print(f"[out] {sum(by_type.values())} 筆 → {outdir}/responses.jsonl   分布={by_type}")

if __name__ == "__main__":
    main()
