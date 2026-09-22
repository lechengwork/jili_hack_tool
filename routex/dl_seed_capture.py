#!/usr/bin/env python3
# dl_seed_capture.py — 直取 f5j murmur 種子(murmur-wrap runtime capture)。
#
# 原理:在 bundle.24017 內把 `return {t_ΟУx$а:х0h}` 換成側錄 wrapper:
#   - 呼叫【真】х0h、回【真】結果 → 不改任何 murmur 輸出、不破壞解碼、不 hook FPT/String(不觸 native 守衛)。
#   - 對 _b(len) > THRESH 的呼叫 beacon `SEED len=.. seed=.. out=.. head=..` 到 mock server(/__wasmpatch__/)。
#     f5j.slice(38) 的視窗 ~84K(單片,case88);25000-視窗(М4F)被 THRESH 濾掉、F_a(~19K)也濾掉 → 低雜訊、鎖定 f5j。
#   - 種子(_c)直接印出,免逆推。唯一副作用:bundle byte 變 → [0..54288] 自檢最終噴 GameTampering,
#     但賭 f5j(region 頂端、早解碼)的 murmur 在炸掉前就先 beacon 出來。
#
# 用法:
#   ./routex/dl_seed_capture.py patch     # 改 bundle(從 .orig)
#   ./routex/dl_seed_capture.py restore   # 還原
#   然後跑 vanilla harness(掛任何 shim 皆可,建議 no-op 探針看 JSERR):
#     SHIM=dl_noop_probe_shim.js ./dl_murmur_trace.sh
#   看 mock 視窗的 ★★★ [shim-report] SEED ... 行,把含 head(f5j 源頭)的那筆貼回來。
import sys, os, shutil, re

CH   = os.path.join(os.path.dirname(__file__), "..", "game_site_backup",
    "uat-wbgame.jlfafafa3.com", "astarte2", "3.6", "web-mobile", "src", "chunks")
BUN  = os.path.join(CH, "bundle.24017.js")
ORIG = os.path.join(CH, "bundle.24017.js.orig")
THRESH = int(os.environ.get("THRESH", "50000"))

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
    # 精確取 murmur 回傳 literal:`return {t_...:<fnname>}`(unicode 從檔案抓,免手抄)
    i = s.find("return {t_")
    if i < 0:
        print("✗ 找不到 'return {t_' — murmur 回傳結構變了"); sys.exit(1)
    close = s.find("}", i)
    RET = s[i:close+1]                       # e.g. return {t_ΟУx$а:х0h}
    if s.count(RET) != 1:
        print(f"⚠ RET 出現 {s.count(RET)} 次(預期 1)——中止"); sys.exit(1)
    colon = RET.find(":")
    key = RET[len("return {"):colon]         # t_ΟУx$а(property key)
    fn  = RET[colon+1:-1]                     # х0h(真 murmur 函式名)
    print(f"[seed] RET @{i}: {esc(RET)!r}")
    print(f"[seed]   key={esc(key)!r}  fn={esc(fn)!r}  THRESH={THRESH}")

    # wrapper 帶閉包計數器:beacon 前 8 次呼叫(確認 murmur 有在跑)+ 所有 len>THRESH(鎖 f5j)。
    WRAP = ("return {" + key + ":(function(){var _n=0;return function(_a,_b,_c){var _r=" + fn + "(_a,_b,_c);"
            "try{_n++;if(_n<=8||_b>" + str(THRESH) + "){(new Image()).src='/__wasmpatch__/'+encodeURIComponent("
            "'SEED#'+_n+' len='+_b+' seed='+((_c>>>0))+' out='+((_r>>>0))+' head='+String(_a).slice(0,24));}}"
            "catch(e){}return _r;};})()}")
    patched = s.replace(RET, WRAP, 1)
    open(BUN, "w", encoding="utf-8").write(patched)
    print(f"[seed] 已寫 bundle.24017.js（{len(patched)-len(s):+d} bytes）")
    print("[seed] 下一步:SHIM=dl_noop_probe_shim.js ./dl_murmur_trace.sh")
    print("[seed] 看 mock 視窗 ★★★ [shim-report] SEED ...;把含 head 的那筆(f5j 源頭)貼回來 → 離線解 tuning bytes。")

if __name__ == "__main__":
    main()
