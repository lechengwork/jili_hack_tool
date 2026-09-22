#!/usr/bin/env python3
# dl_seed_patch.py — Phase 3(b) 取種子:改 bundle.24017.js 的「共用 murmur」(@35198,在未雜湊的 runtime
# 機器區 [0..54288],所有 О_O 都在 54288 之後)加一個 beacon,記錄每次 murmur 的 (len, seed, out)。
# 在真瀏覽器(web.sh)跑,f5j 的自檢解碼會經過這個共用 murmur → beacon 吐出 f5j 那次的種子。
#
# 不 hook 任何原語(不觸 FPT-native 檢查),改的是未雜湊區(不觸 per-О_O murmur 完整性)。
# ⚠ 只改 @35198 那個 return literal,不動 @672156(f5j 內自己的 murmur,那區被雜湊)。
#
# 用法:
#   ./routex/dl_seed_patch.py patch     # 用 .orig 產生帶 beacon 的 bundle.24017.js
#   ./routex/dl_seed_patch.py restore   # 還原成 .orig
# 然後 ./web.sh，看 mock 視窗的  ★★★ [shim-report] MSEED len,seed,out  行貼回來。
import sys, os, shutil

CH = os.path.join(os.path.dirname(__file__), "..", "game_site_backup",
    "uat-wbgame.jlfafafa3.com", "astarte2", "3.6", "web-mobile", "src", "chunks")
BUN  = os.path.join(CH, "bundle.24017.js")
ORIG = os.path.join(CH, "bundle.24017.js.orig")

RET = "return {t_ΟУx$а:х0h}"   # return {t_ΟУx$а:х0h}  (@35198 共用 murmur)
# beacon wrapper:只用「+ 串接 / bracket-index _a[i] / .length / Image / encodeURIComponent」——都不是受守方法原語
# (不觸 FPT-native 檢查)；改的是未雜湊區(不觸 per-О_O murmur 完整性)。
# 回報 (len, seed, out, head16)；head16=輸入前 16 字指紋,用來在眾多被雜湊函式中精準認出 Χ$4ΤΥΕc(len~15473)。
# 濾掉 _b<=1000 的小/priming 呼叫(Χ$4ΤΥΕc 的 len~15473 遠大於此)。
# ★ 只 beacon 目標 Χ$4ΤΥΕc(len 14000..17000),且用旗標保證「只發一次」——避免對數千次 murmur 呼叫
#   狂發 new Image()(loading 階段洪水/timing 自衛→ wedge)。非目標呼叫只做一個整數比較就 return。
WRAP = ("return {t_ΟУx$а:function(_a,_b,_c){var _r=х0h(_a,_b,_c);"
        "try{if(!х0h.__ms&&_b>14000&&_b<17000){х0h.__ms=1;var _h='';for(var _i=0;_i<16&&_i<_a.length;_i++){_h+=_a[_i];}"
        "(new Image()).src='/__wasmpatch__/'+encodeURIComponent('MSEED '+_b+','+(_c>>>0)+','+(_r>>>0)+',h='+_h);}}catch(_e){}"
        "return _r;}}")

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "patch"
    if not os.path.exists(ORIG):
        print("✗ 找不到 .orig:", ORIG); sys.exit(1)
    if cmd == "restore":
        shutil.copyfile(ORIG, BUN); print("✓ 已還原 bundle.24017.js <- .orig"); return
    if cmd != "patch":
        print(__doc__); return
    s = open(ORIG, encoding="utf-8").read()
    i = s.find(RET)
    if i < 0:
        print("✗ 找不到 murmur RET literal（unicode 不符）"); sys.exit(1)
    j = s.find(RET, i + 1)
    print(f"[patch] RET literal 出現位置：first @{i}  second @{j}  （只改 first=@{i} 共用 murmur）")
    if i >= 54288:
        print(f"⚠ first RET @{i} 不在未雜湊區(<54288)，會觸完整性，中止"); sys.exit(1)
    # 只替換第一個
    patched = s[:i] + WRAP + s[i+len(RET):]
    open(BUN, "w", encoding="utf-8").write(patched)
    print(f"[patch] 已寫 bundle.24017.js（+{len(patched)-len(s)} bytes，只改 @{i}）")
    print("[patch] 下一步：./web.sh → 看 mock 視窗 ★★★ [shim-report] MSEED len,seed,out")
    print("[patch] f5j 的種子 = len 最接近 f5j.slice(38) 長度(~84K)那行的 seed。完事 ./routex/dl_seed_patch.py restore")

if __name__ == "__main__":
    main()
