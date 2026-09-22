#!/usr/bin/env python3
# dl_domlock_edit.py — 乾淨測「Χ$4ТΥΕc 有沒有被完整性保護」。
#   等長編輯 domain-lock:`return a$u?Η5Τ:!Η5Τ;` → `return Η5Τ;/*domLK*/`(同長,只改內容、不動長度/區塊對齊)。
#   配 no-op shim 跑(零 FPT 干擾):
#     - 到轉盤     = Χ$4ТΥΕc 沒被保護 → 直接編輯就繞 domain-lock,不需 seed/forge。
#     - GameTampering/random = 被保護 → 需 seed(Frida)。
# 用法:./routex/dl_domlock_edit.py patch|restore
#   然後:SHIM=dl_noop_probe_shim.js ./dl_murmur_trace.sh
import sys, os, shutil

CH   = os.path.join(os.path.dirname(__file__), "..", "game_site_backup",
    "uat-wbgame.jlfafafa3.com", "astarte2", "3.6", "web-mobile", "src", "chunks")
BUN  = os.path.join(CH, "bundle.24017.js")
ORIG = os.path.join(CH, "bundle.24017.js.orig")

def esc(t): return ''.join(c if 0x20 <= ord(c) < 0x7f else f'\\u{ord(c):04x}' for c in t)

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "patch"
    if not os.path.exists(ORIG):
        print("✗ 找不到 .orig:", ORIG); sys.exit(1)
    if cmd == "restore":
        shutil.copyfile(ORIG, BUN); print("✓ 已還原 bundle.24017.js <- .orig"); return
    if cmd != "patch":
        print(__doc__); return

    s = open(ORIG, encoding="utf-8").read()
    i = s.find("return a$u?")
    if i < 0:
        print("✗ 找不到 'return a$u?'"); sys.exit(1)
    semi = s.find(";", i)
    ORIGINAL = s[i:semi+1]                       # return a$u?Η5Τ:!Η5Τ;
    q = ORIGINAL.find("?"); c = ORIGINAL.find(":")
    H5T = ORIGINAL[q+1:c]                         # Η5Τ
    core = f"return {H5T};"                       # return Η5Τ;
    pad = len(ORIGINAL) - len(core)              # 需補到等長
    if pad < 4:
        print(f"✗ 無法等長補足(pad={pad})"); sys.exit(1)
    filler = "domLK_forge_test"[:pad-4]          # 註解內文(不含 /* */)
    MODIFIED = f"{core}/*{filler}{'_'*(pad-4-len(filler))}*/"
    assert len(MODIFIED) == len(ORIGINAL), (len(MODIFIED), len(ORIGINAL))
    if s.count(ORIGINAL) != 1:
        print(f"⚠ ORIGINAL 出現 {s.count(ORIGINAL)} 次,中止"); sys.exit(1)
    print(f"[domlock] ORIGINAL @{i}: {esc(ORIGINAL)!r} (len {len(ORIGINAL)})")
    print(f"[domlock] MODIFIED   : {esc(MODIFIED)!r} (len {len(MODIFIED)})  ← 等長")
    patched = s.replace(ORIGINAL, MODIFIED, 1)
    assert len(patched) == len(s)
    open(BUN, "w", encoding="utf-8").write(patched)
    print(f"[domlock] 已寫 bundle.24017.js（長度不變 {len(patched)}）")
    print("[domlock] 下一步:SHIM=dl_noop_probe_shim.js ./dl_murmur_trace.sh")
    print("[domlock] 判讀:到轉盤=沒保護(直接繞了!);GameTampering/random=被保護(需 seed)。")

if __name__ == "__main__":
    main()
