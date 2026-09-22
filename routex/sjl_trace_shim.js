// sjl_trace_shim.js — 定位 Domain Lock 檢查點(純網頁,不用 Frida)。
// 原理:22de5 的檢查碼違規時會呼叫 window.SendJscramblerLog("DomainLock")。我們從 polyfills 搶先在
//       window.SendJscramblerLog 上裝 getter/setter:等 index.html 賦值它時包一層,等 22de5 呼叫時
//       抓 new Error().stack —— stack 的第 1 幀就是「22de5 裡呼叫它的那一行(index.22de5.js:行:列)」
//       = 檢查碼位置。逐行 beacon 回 mock log。
(function(){
  function rep(m){ try{ (new Image()).src='/__wasmpatch__/'+encodeURIComponent('SJL '+m); }catch(e){} }
  var real = null;
  function wrap(fn){
    return function(){
      try{
        var type = arguments && arguments[0];
        rep('CALL type='+type);
        var st = (new Error('sjl-trace')).stack || '(no stack)';
        var lines = st.split('\n');
        for (var i=0;i<lines.length && i<14;i++){ rep('stack['+i+'] '+String(lines[i]).trim().slice(0,190)); }
      }catch(e){ rep('trace-err '+((e&&e.message)||e)); }
      try{ return fn.apply(this, arguments); }catch(e){ return undefined; }
    };
  }
  try{
    var pre = window.SendJscramblerLog;
    Object.defineProperty(window, 'SendJscramblerLog', {
      configurable:true,
      get:function(){ return real; },
      set:function(v){ real = (typeof v==='function') ? wrap(v) : v; rep('index.html assigned SJL -> wrapped'); }
    });
    if (typeof pre==='function'){ real = wrap(pre); rep('wrapped pre-existing SJL'); }
    rep('setter armed (等 22de5 呼叫)');
  }catch(e){ rep('arm-err '+((e&&e.message)||e)); }
})();
