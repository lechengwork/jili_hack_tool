// dl_eval_shim.js v2 — 強制 bundle.24017 走 SystemJS 的 (0,eval) 路徑 + 在 eval 前拔掉 B$Τ 反制。
// system.bundle 的 shouldFetch 只對 css/html/json/wasm 回 true → .js 走 <script src>(攔不到)。
// 我們在 System 出現後把 shouldFetch 覆寫成「bundle.24017 也 fetch」→ 改走 (0,eval)(源碼) → eval hook 轉換。
// 伺服器服務原始 bundle(integrity 讀原始 → 不炸 GameTampering);執行的是 patched(反制沒了 → 不炸 DomainLock)。
(function(){
  function rep(m){ try{ (new Image()).src='/__wasmpatch__/'+encodeURIComponent(m); }catch(e){} }
  var ORIG    = "case 13:J3mw6.\u039f$(\u03996\u03a1);B$\u03a4();\u0440$\u0421=77;break;";
  var PATCHED = "case 13:J3mw6.\u039f$(\u03996\u03a1);\u0440$\u0421=77;break;";
  // ── (1) eval hook:bundle.24017 源碼在 eval 前拔掉 B$Τ() ──
  var realEval = window.eval;
  function hooked(src){
    try{
      if (typeof src==='string' && src.indexOf(ORIG)!==-1){
        var out = src.split(ORIG).join(PATCHED);
        rep('EVAL-HOOK ★patched bundle.24017 pre-eval★ ('+src.length+' -> '+out.length+')');
        return realEval.call(this, out);
      }
    }catch(e){ rep('EVAL-HOOK err '+((e&&e.message)||e)); }
    return realEval.apply(this, arguments);
  }
  try{ hooked.toString=function(){ return realEval.toString(); }; }catch(e){}
  try{ Object.defineProperty(hooked,'name',{value:'eval',configurable:true}); }catch(e){}
  try{ window.eval = hooked; }catch(e){ rep('EVAL-HOOK set-fail '+e); }
  // ── (2) 等 System 出現,覆寫 shouldFetch 讓 bundle.24017 改走 fetch+eval ──
  var tries=0;
  var iv=setInterval(function(){
    tries++;
    try{
      var S=window.System;
      if (S && typeof S.shouldFetch==='function'){
        var orig=S.shouldFetch.bind(S);
        S.shouldFetch=function(u){ try{ if(typeof u==='string' && u.indexOf('bundle.24017')>=0) return true; }catch(e){} return orig(u); };
        try{ var P=Object.getPrototypeOf(S); if(P&&P.shouldFetch){ var op=P.shouldFetch; P.shouldFetch=function(u){ try{ if(typeof u==='string'&&u.indexOf('bundle.24017')>=0) return true; }catch(e){} return op.call(this,u); }; } }catch(e){}
        rep('SHOULDFETCH forced for bundle.24017 (tries='+tries+')');
        clearInterval(iv);
      }
    }catch(e){}
    if(tries>400){ clearInterval(iv); rep('SHOULDFETCH gave up (System never appeared)'); }
  }, 15);
  rep('EVAL-HOOK v2 armed (eval===hooked:'+(window.eval===hooked)+')');
})();
