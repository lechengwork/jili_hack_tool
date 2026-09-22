#!/usr/bin/env python3
# dl_fpt_forge.py — Phase 3(b) 正解:FPT-spoof forge(免種子)。
#
# 原理:
#   integrity = murmur(О_O.toString())，透過 case86 快照的 F2Р=Function.prototype.toString 取源。
#   我們在 polyfills(比 bundle.24017 早)hook FPT:
#     (a) 被要求 toString 自己 → 回傳真 native 字串(騙過 case86 А5 原生性檢查)
#     (b) 被要求 toString 任何函式 → 若源碼含我們的「唯一標記」，把標記還原成原句 → integrity 算到原 hash → 過
#   而 bundle.24017.js 的 Χ$4ΤΥΕc(domain-lock 判斷)已被改成永遠允許。
#   → 不需要種子、不需要 preserve murmur;直接讓 hasher「看到原始碼」。
#
# 編輯:Χ$4ΤΥΕc @700529 的 `return a$u?Η5Τ:!Η5Τ;` → `return Η5Τ;/*<MARK>*/`
#   MARK 唯一，hook 用 `split(MODIFIED).join(ORIGINAL)` 精確還原(不嵌 15511 字全源)。
#
# 用法:
#   ./routex/dl_fpt_forge.py patch     # 改 bundle + 產 routex/dl_fpt_spoof_shim.js
#   ./routex/dl_fpt_forge.py restore   # 還原 bundle
# 然後:SHIM=dl_fpt_spoof_shim.js EXTRA_SHIM 跑；用 ./web.sh 但要掛這個 shim → 見下方 dl_fpt_run.sh
import sys, os, json, shutil

CH = os.path.join(os.path.dirname(__file__), "..", "game_site_backup",
    "uat-wbgame.jlfafafa3.com", "astarte2", "3.6", "web-mobile", "src", "chunks")
BUN  = os.path.join(CH, "bundle.24017.js")
ORIG = os.path.join(CH, "bundle.24017.js.orig")
SHIM = os.path.join(os.path.dirname(__file__), "dl_fpt_spoof_shim.js")

MARK = "X9QdomZ"   # 唯一標記

def esc(t): return ''.join(c if 0x20<=ord(c)<0x7f else f'\\u{ord(c):04x}' for c in t)

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "patch"
    if not os.path.exists(ORIG):
        print("✗ 找不到 .orig:", ORIG); sys.exit(1)
    if cmd == "restore":
        shutil.copyfile(ORIG, BUN); print("✓ 已還原 bundle.24017.js <- .orig"); return
    if cmd != "patch":
        print(__doc__); return

    s = open(ORIG, encoding="utf-8").read()
    # 精確取原句(從檔案，免手抄 unicode)
    i = s.find("return a$u?")
    if i < 0:
        print("✗ 找不到 'return a$u?' — Χ$4ΤΥΕc 結構變了"); sys.exit(1)
    semi = s.find(";", i)
    ORIGINAL = s[i:semi+1]                 # e.g. return a$u?Η5Τ:!Η5Τ;
    print(f"[forge] ORIGINAL @{i}: {esc(ORIGINAL)!r}  (len {len(ORIGINAL)})")
    # 取出 Η5Τ（? 與 : 之間）
    q = ORIGINAL.find("?"); c = ORIGINAL.find(":")
    H5T = ORIGINAL[q+1:c]                   # Η5Τ
    MODIFIED = f"return {H5T};/*{MARK}*/"
    print(f"[forge] MODIFIED  : {esc(MODIFIED)!r}")
    if s.count(ORIGINAL) != 1:
        print(f"⚠ ORIGINAL 出現 {s.count(ORIGINAL)} 次(預期 1)——標記還原可能誤傷,中止"); sys.exit(1)

    patched = s.replace(ORIGINAL, MODIFIED, 1)
    open(BUN, "w", encoding="utf-8").write(patched)
    print(f"[forge] 已寫 bundle.24017.js（{len(patched)-len(s):+d} bytes）")

    # 產 FPT-spoof shim。ORIGINAL/MODIFIED 用 json.dumps 產生安全 JS 字串字面量。
    # ★ hook 用 concise method(無 .prototype,與原生特徵一致)+ 診斷計數。
    shim = """// dl_fpt_spoof_shim.js — 【自動產生 by dl_fpt_forge.py】FPT-spoof v2:
//  (a) 騙過 case86 原生性檢查(self→native、無 .prototype、name/length 偽裝)
//  (b) 讓 hasher 透過 F2Р 取源時把標記還原成原始 Χ$4ΤΥΕc → 算到原 hash
//  (c) 診斷:計 total/revert/self,還原第一次觸發時回報 → 區分「沒走我們 hook」vs「第二層 integrity」
// 必須比 bundle.24017 早(prepend 進 polyfills)。
(function(){
  var realFPT = Function.prototype.toString;
  var NATIVE_SELF = realFPT.call(realFPT);      // 真 "function toString() { [native code] }"
  var passTS = realFPT;   // ★ pass-through 用:arm() 在 core-js redefine 後會更新成 core-js 版(對齊 index.22de5 decode 期待)
  var MOD  = %s;   // 改過的片段(含唯一標記)
  var ORIGN = %s;  // 原始片段
  var nCall=0, nRevert=0, nSelf=0, firstRevert=false, firstCall=false, firstBig=false;
  function rep(m){ try{ (new Image()).src='/__wasmpatch__/'+encodeURIComponent('FPTSPOOF '+m); }catch(e){} }
  // ★探針(6):抓 client-side 未捕捉錯誤/promise rejection(不能開 DevTools,用 beacon 當眼睛)。去重、最多 5 個。
  try {
    var errSeen={}, errN=0;
    var onE=function(msg,src,ln,col){ try{ var k=(''+msg).slice(0,90); if(errSeen[k]||errN>=5)return; errSeen[k]=1; errN++;
      rep('JSERR '+k+' @'+((''+(src||'')).slice(-44))+':'+ln+':'+col); }catch(e){} };
    window.addEventListener('error', function(ev){ onE(ev.message||(ev.error&&ev.error.message)||'?', ev.filename, ev.lineno, ev.colno); }, true);
    window.addEventListener('unhandledrejection', function(ev){ onE('PROMISE '+((ev.reason&&(ev.reason.message||ev.reason))||'?'),'',0,0); });
  } catch(e){}
  // ★ concise method syntax `m(){}`(非 `m:function(){}`)→ 無 own 'prototype' 屬性(原生特徵);dynamic this
  var _holder = { m(){
    nCall++;
    if (!firstCall){ firstCall=true; rep('HOOK-CALL-1 (hook 確實被用)'); }   // ★同步:第一次被呼叫
    if (this === hooked) { nSelf++; return NATIVE_SELF; }
    var s;
    try { s = passTS.apply(this, arguments); } catch(e){ try{ return realFPT.apply(this, arguments); }catch(e2){ return NATIVE_SELF; } }
    if (typeof s === 'string'){
      if (!firstBig && s.length>5000){ firstBig=true; rep('BIG-TS len='+s.length+' hasMOD='+(s.indexOf(MOD)!==-1)); } // ★大源碼經過我們?
      if (s.indexOf(MOD) !== -1) {
        nRevert++;
        if (!firstRevert){ firstRevert=true; rep('REVERT-FIRED len='+s.length); }
        return s.split(MOD).join(ORIGN);
      }
    }
    return s;
  } };
  var hooked = _holder.m;
  try{ Object.defineProperty(hooked,'name',{value:'toString',configurable:true}); }catch(e){}
  try{ Object.defineProperty(hooked,'length',{value:0,configurable:true}); }catch(e){}
  // ★ 抗自癒安裝:accessor + 吞 setter + non-configurable。
  //   getter 永遠回我們的 hook;`FPT.toString = native` 這種自癒指派會走 setter → 吞掉 → 仍是我們的。
  //   configurable:false 讓別人無法 delete/redefine(若自癒用 defineProperty,會在【它的】程式碼裡丟例外 → 也是情報)。
  var nSet=0, firstSet=false, nArm=0, passUpdated=false;
  // ★ DATA property(非 accessor)+ configurable/writable:TRUE:
  //   - descriptor 形狀正常(.value=函式)→ 避開「檢查是不是 accessor」的偵測。
  //   - configurable:true 讓 core-js 的 `delete Function.prototype.toString`(@polyfills~4724)成功(不丟例外)。
  //   - 但 core-js delete+重指派會拿掉 hook,故 arm() 反覆重裝;重裝前先把「當前底層 toString」存進 passTS
  //     → 我們 pass-through 用 core-js redefine 後的版本,對齊 index.22de5 的 decode 期待(修 `random`)。
  function arm(){
    try{
      var cur = Function.prototype.toString;
      if (cur !== hooked && typeof cur === 'function'){ passTS = cur; passUpdated = true; }  // 抓 core-js 版
      Object.defineProperty(Function.prototype,'toString',{
        value:hooked, writable:true, configurable:true, enumerable:false
      });
      nArm++; return true;
    }catch(e){ rep('ARM-FAILED '+e); return false; }
  }
  var installedLock=arm();
  try{ Promise.resolve().then(arm); }catch(e){}   // ★關鍵:polyfills 跑完(core-js 已 redefine)後、bundle.24017 前重裝
  try{ setTimeout(arm,0); }catch(e){}
  try{ setTimeout(arm,30); }catch(e){}
  try{ setTimeout(arm,150); }catch(e){}
  var live=(Function.prototype.toString===hooked);
  var selfNative=(hooked.call(hooked).indexOf('native code')>=0);
  var hasProto=('prototype' in hooked);
  rep('installed lock='+installedLock+' live='+live+' selfNative='+selfNative+' hasProto='+hasProto+' natlen='+NATIVE_SELF.length+' nArm='+nArm);
  // ★探針(3):self-defending 是否建 iframe 拿乾淨 intrinsics
  try {
    var _ce = document.createElement;
    document.createElement = function(t){
      try{ if((''+t).toLowerCase()==='iframe') rep('IFRAME-CREATED (疑似拿乾淨 realm)'); }catch(e){}
      return _ce.apply(this, arguments);
    };
  } catch(e){}
  // ★探針(4):它是否用 fetch/XHR 重抓 bundle.24017 原文去 hash(完全繞開 FPT)?
  //   只報含 '24017' 的請求 → 低雜訊;若載入後又出現一次 = 疑似讀原始檔文而非 live 函式。
  try {
    if (window.fetch){
      var _f = window.fetch;
      window.fetch = function(u){ try{ var us=''+((u&&u.url)||u); if(us.indexOf('24017')!==-1) rep('FETCH-24017 '+us.slice(-70)); }catch(e){} return _f.apply(this, arguments); };
    }
  } catch(e){}
  try {
    var _open = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(m,u){ try{ var us=''+u; if(us.indexOf('24017')!==-1) rep('XHR-24017 '+us.slice(-70)); }catch(e){} return _open.apply(this, arguments); };
  } catch(e){}
  // ★探針(5):有人重新指派 Function.prototype.toString(self-healing)? 微任務+短逾時各查一次
  //   (GameTampering 噴太快時微任務可能來不及,兩個時點各報一次以防漏)
  try { Promise.resolve().then(function(){ rep('microtask FPT-still-ours='+(Function.prototype.toString===hooked)); }); } catch(e){}
  try { setTimeout(function(){ rep('t0 FPT-still-ours='+(Function.prototype.toString===hooked)+' calls='+nCall+' big='+firstBig+' revert='+nRevert+' nArm='+nArm+' passUpdated='+passUpdated); }, 0); } catch(e){}
})();
""" % (json.dumps(MODIFIED), json.dumps(ORIGINAL))
    open(SHIM, "w", encoding="utf-8").write(shim)
    print(f"[forge] 已產 {SHIM}")
    print("[forge] 下一步:./routex/dl_fpt_run.sh （合法域完整載入 + 掛此 shim）")
    print("[forge] 判讀:載到轉盤 + 無 GameTampering = ★成功★;之後就能換任意域測 domain-lock 是否真的被繞。")

if __name__ == "__main__":
    main()
