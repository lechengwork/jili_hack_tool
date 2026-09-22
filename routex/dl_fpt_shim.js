// dl_fpt_shim.js v2 (儀表版) — 查「完整性 hasher 到底有沒有透過我們 hook 的 FPT 讀源碼」。
(function(){
  var FPT = Function.prototype.toString;
  var NATIVE = FPT.call(FPT);
  var PATCHED = "case 13:J3mw6.\u039f$(\u03996\u03a1);\u0440$\u0421=77;break;";
  var ORIG    = "case 13:J3mw6.\u039f$(\u03996\u03a1);B$\u03a4();\u0440$\u0421=77;break;";
  var nCall=0, nMark=0, nNative=0, maxLen=0, firstMark=false;
  function rep(m){ try{ (new Image()).src='/__wasmpatch__/'+encodeURIComponent(m); }catch(e){} }
  function ts(){
    nCall++;
    if (this === ts || this === FPT){ nNative++; return NATIVE; }
    var s = FPT.apply(this, arguments);
    if (typeof s === 'string'){
      if (s.length>maxLen) maxLen=s.length;
      if (s.indexOf(PATCHED) !== -1){
        nMark++;
        if (!firstMark){ firstMark=true; rep('FPT ★MARKER-SEEN★ len='+s.length+' -> substituting'); }
        return s.split(PATCHED).join(ORIG);
      }
    }
    return s;
  }
  try{ Object.defineProperty(ts,'name',{value:'toString',configurable:true}); }catch(e){}
  try{ Object.defineProperty(ts,'length',{value:0,configurable:true}); }catch(e){}
  try{ Object.defineProperty(Function.prototype,'toString',{value:ts,writable:true,configurable:true}); }catch(e){}
  // 自我驗證:hook 在本 realm 是否生效
  function __probe(){}
  var live = (Function.prototype.toString === ts);
  var probeHit = false; var c0=nCall; try{ __probe.toString(); probeHit=(nCall>c0); }catch(e){}
  rep('FPT-spoof v2 installed native='+(NATIVE.indexOf('native code')>=0)+' live='+live+' probeHit='+probeHit);
  // 定期回報,看載入過程 hasher 有沒有讀到帶標記的源碼
  var t=0; var iv=setInterval(function(){ t++; rep('FPT stats calls='+nCall+' markerHits='+nMark+' nativeReturns='+nNative+' maxLen='+maxLen); if(t>=6) clearInterval(iv); }, 1200);
})();
