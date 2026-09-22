// dl_trace_shim.js — 【Phase 1:動態追值】定位 Domain Lock 的「比對」與「反制」(純網頁,不用 Frida)。
//
// 從 polyfills 最先跑,hook 比對用的標準原語,只記「涉及網域(myslot/jlfafafa 這種裸主機名)」的呼叫 + stack;
// 同時包住 window.SendJscramblerLog(違規回報)以做時間對齊——出現在 DomainLock 之前的那筆比對 = 檢查本身,
// 之後緊接著 call 的 = 反制。混淆藏得住程式結構,藏不住流過標準方法的「值」。
(function(){
  function rep(m){ try{ (new Image()).src='/__wasmpatch__/'+encodeURIComponent('TRACE '+m); }catch(e){} }

  // domain-ish 過濾:含 myslot(本場 location 主機名) 或 jlfafafa(允許值),排掉一看就是完整資產 URL 的長字串
  var RX = /myslot|jlfafafa/i;
  function domainish(v){
    try{
      if (typeof v !== 'string') return false;
      if (v.length < 3 || v.length > 260) return false;
      if (!RX.test(v)) return false;
      return true;
    }catch(e){ return false; }
  }
  function shortStack(){
    try{
      var lines = (new Error()).stack.split('\n');
      // 跳過 Error 行與我們自己的 wrapper 幾行,取最先進入遊戲碼的幾幀
      var out = [];
      for (var i=1;i<lines.length && out.length<4;i++){
        var l = lines[i].trim().replace(/^at\s+/,'');
        if (l.indexOf('dl_trace')>=0 || l.indexOf('polyfills.bundle')>=0) continue;   // 略過本 shim/載體幀
        out.push(l.slice(0,110));
      }
      return out.join('  <-  ');
    }catch(e){ return '(no stack)'; }
  }

  var seen = {}, count = 0, CAP = 250;
  function q(s){ try{ return JSON.stringify(String(s)).slice(0,90); }catch(e){ return '?'; } }
  function logCall(kind, thisv, args){
    if (count >= CAP) return;
    var parts = [];
    if (domainish(thisv)) parts.push('this='+q(thisv));
    for (var i=0;i<args.length;i++){
      if (domainish(args[i])) parts.push('a'+i+'='+q(args[i]));
      else if (args[i] instanceof RegExp) parts.push('a'+i+'=RE'+String(args[i]).slice(0,90));
    }
    if (!parts.length) return;                 // 只留「涉及網域」的呼叫
    var msg = kind+' '+parts.join(' ');
    var key = msg.slice(0,80);
    if (seen[key]) return; seen[key] = 1;       // 去重(資產 URL 重複處理會被收斂)
    count++;
    rep(msg + '  @@ ' + shortStack());
  }
  function hook(proto, name, kind){
    try{
      var orig = proto[name];
      if (typeof orig !== 'function') return;
      proto[name] = function(){ try{ logCall(kind, this, arguments); }catch(e){} return orig.apply(this, arguments); };
      try{ proto[name].toString = function(){ return orig.toString(); }; }catch(e){}
    }catch(e){}
  }
  ['indexOf','lastIndexOf','includes','startsWith','endsWith','search','match','matchAll','split','replace','localeCompare']
    .forEach(function(n){ hook(String.prototype, n, 'S.'+n); });
  ['test','exec'].forEach(function(n){ hook(RegExp.prototype, n, 'RE.'+n); });
  ['includes','indexOf','find','findIndex','some','filter','join'].forEach(function(n){ hook(Array.prototype, n, 'A.'+n); });

  // 同時包 SendJscramblerLog(時間對齊:DomainLock 前一筆比對=檢查;之後的 call=反制)
  try{
    var real = null;
    function wrapSJL(fn){ return function(){ try{ rep('>>> SendJscramblerLog("'+(arguments[0])+'") <<< (前一筆比對=檢查,之後=反制)'); }catch(e){} try{ return fn.apply(this, arguments); }catch(e){} }; }
    var pre = window.SendJscramblerLog;
    Object.defineProperty(window, 'SendJscramblerLog', {
      configurable:true, get:function(){ return real; },
      set:function(v){ real = (typeof v==='function') ? wrapSJL(v) : v; }
    });
    if (typeof pre==='function') real = wrapSJL(pre);
  }catch(e){}

  rep('Phase1 trace armed (String/RegExp/Array hooks, filter=myslot|jlfafafa)');
})();
