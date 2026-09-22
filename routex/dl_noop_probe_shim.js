// dl_noop_probe_shim.js — 純隔離探針:【完全不掛任何 hook】(不碰 FPT / createElement / fetch / defineProperty)。
//   目的:乾淨 bundle + 本 shim = vanilla 離線載入。用來分辨 index.22de5.js 的
//   `undefined.random` 是【我們的 FPT accessor shim 造成】還是【harness/遊戲本身就到不了轉盤】。
//   唯一動作:用 window.onerror / unhandledrejection 把 client 端未捕捉錯誤 beacon 出來(不能開 DevTools)。
(function(){
  function rep(m){ try{ (new Image()).src='/__wasmpatch__/'+encodeURIComponent('NOOP '+m); }catch(e){} }
  rep('installed (zero-hook probe)');
  try {
    var errSeen={}, errN=0;
    var onE=function(msg,src,ln,col){ try{ var k=(''+msg).slice(0,90); if(errSeen[k]||errN>=6)return; errSeen[k]=1; errN++;
      rep('JSERR '+k+' @'+((''+(src||'')).slice(-44))+':'+ln+':'+col); }catch(e){} };
    window.addEventListener('error', function(ev){ onE(ev.message||(ev.error&&ev.error.message)||'?', ev.filename, ev.lineno, ev.colno); }, true);
    window.addEventListener('unhandledrejection', function(ev){ onE('PROMISE '+((ev.reason&&(ev.reason.message||ev.reason))||'?'),'',0,0); });
  } catch(e){}
  // 存活里程碑:確認 shim 有跑、頁面沒在更早就死
  try { Promise.resolve().then(function(){ rep('alive microtask'); }); } catch(e){}
  try { setTimeout(function(){ rep('alive t0'); }, 0); } catch(e){}
  try { setTimeout(function(){ rep('alive t3000 (若卡 loading 但無 JSERR = 等 mock 回應)'); }, 3000); } catch(e){}
})();
