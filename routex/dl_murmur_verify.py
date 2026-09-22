#!/usr/bin/env python3
# dl_murmur_verify.py — Phase 3(a) 離線驗證器。
#
# 重現 dl_murmur_trace_shim.js 在瀏覽器算的 FNV-1a checksum,以及 code-integrity 用的
# MurmurHash3_x86_32,好把 runtime 撈回來的 f0Ο(=О_O.toString())對上「本地原始 bundle 的某段函式源碼」。
#
# 靜態已確認(bundle.24017.js):
#   • 每位元組 = charCodeAt(i) & 0xff(取 UTF-16 code unit 低位元組)
#   • MurmurHash3_x86_32,c1=0xcc9e2d51 c2=0x1b873593 fmix=0x85ebca6b/0xc2b2ae35 mix=0xe6546b64
#   • 鏈式:H_9 初值 = 96582,視窗 25000
#
# 用法:
#   1) 定位 runtime 回報的長字串是本地檔哪一段:
#        ./dl_murmur_verify.py locate '<BIGSTR-head 的頭 48 字(去掉 \\uXXXX 還原)>'
#      (實務上直接把 head 的可見部分當 grep pattern:見 --grep)
#   2) 驗證某段 [off:off+len] 的 fnv 是否等於 runtime 的 fnv=...:
#        ./dl_murmur_verify.py fnv <off> <len>
#   3) 對某視窗算 murmur3(bytes, seed):
#        ./dl_murmur_verify.py murmur <off> <len> <seed_int>
import sys, os

BUNDLE = os.path.join(os.path.dirname(__file__),
    "..", "game_site_backup", "uat-wbgame.jlfafafa3.com",
    "astarte2", "3.6", "web-mobile", "src", "chunks", "bundle.24017.js.orig")

def load_units():
    # 以 UTF-16 code unit 序列還原 JS 的 charCodeAt。假設無 astral(>0xFFFF)字元。
    with open(BUNDLE, "r", encoding="utf-8") as f:
        text = f.read()
    astral = [c for c in text if ord(c) > 0xFFFF]
    if astral:
        print(f"⚠ 檔內有 {len(astral)} 個 astral 字元,JS charCodeAt 會拆 surrogate,需改逐 code-unit 處理", file=sys.stderr)
    return text  # BMP-only 時 len(text)/ord 與 JS length/charCodeAt 一致

def fnv1a_bytes(units, off=0, length=None):
    if length is None:
        length = len(units) - off
    h = 0x811c9dc5
    end = off + length
    for i in range(off, end):
        h ^= (ord(units[i]) & 0xff)
        h = (h * 0x01000193) & 0xffffffff
    return h

def murmur3_x86_32(units, off, length, seed):
    c1 = 0xcc9e2d51; c2 = 0x1b873593
    def rotl(x, r): return ((x << r) | (x >> (32 - r))) & 0xffffffff
    def mul(a, b): return (a * b) & 0xffffffff
    h1 = seed & 0xffffffff
    nblocks = length // 4
    for b in range(nblocks):
        i = off + b * 4
        k1 = ((ord(units[i])   & 0xff)
             | (ord(units[i+1]) & 0xff) << 8
             | (ord(units[i+2]) & 0xff) << 16
             | (ord(units[i+3]) & 0xff) << 24) & 0xffffffff
        k1 = mul(k1, c1); k1 = rotl(k1, 15); k1 = mul(k1, c2)
        h1 ^= k1; h1 = rotl(h1, 13); h1 = (mul(h1, 5) + 0xe6546b64) & 0xffffffff
    # tail
    tail = off + nblocks * 4
    rem = length & 3
    k1 = 0
    if rem == 3: k1 ^= (ord(units[tail+2]) & 0xff) << 16
    if rem >= 2: k1 ^= (ord(units[tail+1]) & 0xff) << 8
    if rem >= 1:
        k1 ^= (ord(units[tail]) & 0xff)
        k1 = mul(k1, c1); k1 = rotl(k1, 15); k1 = mul(k1, c2); h1 ^= k1
    # fmix
    h1 ^= length
    h1 ^= h1 >> 16; h1 = mul(h1, 0x85ebca6b)
    h1 ^= h1 >> 13; h1 = mul(h1, 0xc2b2ae35)
    h1 ^= h1 >> 16
    return h1 & 0xffffffff

def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    units = load_units()
    print(f"[bundle] .orig length(code units)={len(units)}", file=sys.stderr)
    cmd = sys.argv[1]
    if cmd == "fnv":
        off = int(sys.argv[2]); length = int(sys.argv[3])
        print(f"fnv1a[{off}:{off+length}] = {fnv1a_bytes(units, off, length):08x}")
    elif cmd == "murmur":
        off = int(sys.argv[2]); length = int(sys.argv[3]); seed = int(sys.argv[4], 0)
        print(f"murmur3[{off}:{off+length}] seed={seed} = {murmur3_x86_32(units, off, length, seed):08x}")
    elif cmd == "locate":
        needle = sys.argv[2]
        idx = units.find(needle)
        print(f"first occurrence of head at code-unit offset: {idx}")
        if idx >= 0:
            print(f"context: ...{units[max(0,idx-20):idx+80]}...")
    elif cmd == "grep":
        # 用可見片段找 О_O 源碼起點
        needle = sys.argv[2]
        start = 0; hits = []
        while True:
            i = units.find(needle, start)
            if i < 0: break
            hits.append(i); start = i + 1
            if len(hits) > 20: break
        print(f"{len(hits)} hit(s): {hits[:20]}")
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
