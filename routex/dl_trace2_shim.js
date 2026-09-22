// dl_trace2_shim.js — 【Phase 1+:動態追值 · 含 hash-gate 偵測】
//
// 舊 dl_trace_shim 的盲點:(a) 只 log「值是 domainish 的呼叫」——hash gate 是 hash(x)===bakedHash,
// 兩邊都是數字,天生被濾掉;(b) 完全沒 hook charCodeAt——JS 實作的 hash 一定逐字元 charCodeAt 讀網域,
// 那是唯一藏不住的執行期指紋。所以「舊 trace 沒抓到」不是 hash 的證據,只是沒往 hash 經過的地方看。
//
// 本版補三個缺口,一跑就能證實/證偽 hash 猜想:
//   (B) ★hash 指紋★ charCodeAt/codePointAt 逐字元讀 domain 字串 → 抓 stack(= hash function 位置)
//   (C) 可攔截的 location/document 讀取點(domain/URL/referrer/baseURI…)passthrough + log(誰在讀網域)
//   (D) crypto.subtle.digest(非同步 hash)
//   (A) 保留舊的 String/RegExp/Array 比對方法 hook + (E) SendJscramblerLog 時間對齊。
//
// 判讀(看 mock 視窗 ★★★ [shim-report] TRACE …):
//   • 若看到 `S.indexOf a0="...jlfafafa..."` / `RE.test a0="...jlfafafa..."` → 明文(runtime 解出),不是 hash
//        → Phase 2:直接 hook 那個 method,漂亮收工。
//   • 若看到 `CHARCODE.charCodeAt FULL-PASS on "myslot.test" = 疑似 hash 逐字元` + stack
//        → ★你的 hash 猜想成立★;stack 指出 hash fn → Phase 2:wrap 它,x==="我的域"時改算真允許域。
//   • 若 4 秒收尾印 `CHARCODE summary: 無 domain 字串被逐字元讀` 且比對側也沒 domainish 命中
//        → 不是 JS-charCodeAt hash;可能 ===/includes/bracket-index[i],或鎖讀的是不可攔截的 location(看 READ 有沒有命中)。
(function(){
  function rep(m){ try{ (new Image()).src='/__wasmpatch__/'+encodeURIComponent('TRACE '+m); }catch(e){} }
  var RX = /myslot|jlfafafa/i;
  function domainish(v){
    try{ return typeof v==='string' && v.length>=3 && v.length<=260 && RX.test(v); }catch(e){ return false; }
  }
  function shortStack(){
    try{
      var lines=(new Error()).stack.split('\n'), out=[];
      for (var i=1;i<lines.length && out.length<5;i++){
        var l=lines[i].trim().replace(/^at\s+/,'');
        if (l.indexOf('dl_trace')>=0 || l.indexOf('polyfills.bundle')>=0) continue;
        out.push(l.slice(0,120));
      }
      return out.join('  <-  ');
    }catch(e){ return '(no stack)'; }
  }
  function q(s){ try{ return JSON.stringify(String(s)).slice(0,100); }catch(e){ return '?'; } }

  // 分類配額:避免資產 URL / 熱路徑洗版把訊號擠掉。
  var GLOBAL=450, sent=0, caps={M:250,CHAR:90,READ:25,DIG:20,SJL:20,INFO:10}, cc={};
  function beacon(cat,m){ cc[cat]=(cc[cat]||0)+1; if (cc[cat]>(caps[cat]||50)) return; if (sent>=GLOBAL) return; sent++; rep(m); }

  // ── (A) 比對方法(String/RegExp/Array)——保留舊行為,dedup ──
  var seen={};
  function logCall(kind,thisv,args){
    var parts=[];
    if (domainish(thisv)) parts.push('this='+q(thisv));
    for (var i=0;i<args.length;i++){
      if (domainish(args[i])) parts.push('a'+i+'='+q(args[i]));
      else if (args[i] instanceof RegExp) parts.push('a'+i+'=RE'+String(args[i]).slice(0,90));
    }
    if (!parts.length) return;
    var msg=kind+' '+parts.join(' '), key=msg.slice(0,80);
    if (seen[key]) return; seen[key]=1;
    beacon('M', msg+'  @@ '+shortStack());
  }
  function hook(proto,name,kind){
    try{
      var orig=proto[name]; if (typeof orig!=='function') return;
      proto[name]=function(){ try{ logCall(kind,this,arguments); }catch(e){} return orig.apply(this,arguments); };
      try{ proto[name].toString=function(){ return orig.toString(); }; }catch(e){}
    }catch(e){}
  }
  ['indexOf','lastIndexOf','includes','startsWith','endsWith','search','match','matchAll','split','replace','localeCompare']
    .forEach(function(n){ hook(String.prototype,n,'S.'+n); });
  ['test','exec'].forEach(function(n){ hook(RegExp.prototype,n,'RE.'+n); });
  ['includes','indexOf','find','findIndex','some','filter','join'].forEach(function(n){ hook(Array.prototype,n,'A.'+n); });

  // ── (B) ★hash 指紋★ charCodeAt/codePointAt 逐字元讀取 ──
  //  guard 極省:先看長度(domain 落在 ~3..40),再看有沒有 '.',最後才 RX。單字元/長 JSON 立刻短路。
  var ccMap=Object.create(null);
  function ccGuard(t){
    try{
      var len=t.length|0; if (len<3||len>40) return null;
      var s=(typeof t==='string')?t:(''+t);
      if (s.indexOf('.')<0) return null;
      return RX.test(s)?s:null;
    }catch(e){ return null; }
  }
  function hookChar(name){
    try{
      var orig=String.prototype[name]; if (typeof orig!=='function') return;
      String.prototype[name]=function(){
        try{
          var s=ccGuard(this);
          if (s){
            var e=ccMap[s]||(ccMap[s]={n:0,len:s.length,stack:null});
            e.n++;
            if (e.n===1){ e.stack=shortStack(); beacon('CHAR','CHARCODE.'+name+' first-touch on '+q(s)+'  @@ '+e.stack); }
            else if (e.n===e.len){ beacon('CHAR','CHARCODE.'+name+' FULL-PASS('+e.len+'/'+e.len+') on '+q(s)+' = 疑似 hash 逐字元  @@ '+e.stack); }
            else if (e.n===e.len*2){ beacon('CHAR','CHARCODE.'+name+' 2nd-PASS on '+q(s)+'  @@ '+shortStack()); }
          }
        }catch(_){}
        return orig.apply(this,arguments);
      };
      try{ String.prototype[name].toString=function(){ return orig.toString(); }; }catch(_){}
    }catch(e){}
  }
  hookChar('charCodeAt'); hookChar('codePointAt');

  // ── (C) 可攔截的網域讀取點(passthrough + log;只記「裸主機名」讀取,濾掉資產 URL 洗版)──
  function traceGetter(obj,prop,label){
    try{
      var d=Object.getOwnPropertyDescriptor(obj,prop);
      if (!d || typeof d.get!=='function' || d.configurable===false) return;   // unforgeable(configurable:false)自動跳過
      var origGet=d.get;
      Object.defineProperty(obj,prop,{configurable:true,set:d.set,get:function(){
        var v=origGet.call(this);
        try{ if (domainish(v) && String(v).indexOf('/')<0) beacon('READ','READ '+label+' -> '+q(v)+'  @@ '+shortStack()); }catch(_){}
        return v;
      }});
    }catch(e){}
  }
  traceGetter(Document.prototype,'domain','document.domain');
  traceGetter(Document.prototype,'URL','document.URL');
  traceGetter(Document.prototype,'documentURI','document.documentURI');
  traceGetter(Document.prototype,'baseURI','document.baseURI');
  traceGetter(Document.prototype,'referrer','document.referrer');
  ['hostname','host','href','origin','pathname'].forEach(function(p){ traceGetter(Location.prototype,p,'location.'+p); });
  // location.hostname/href 多半是 instance own + unforgeable → traceGetter 自動跳過;
  // 那種「讀取點看不到」是預期的,靠 (B) charCodeAt 指紋補位。

  // ── (D) crypto.subtle.digest(非同步 hash)──
  try{
    var cs=window.crypto&&window.crypto.subtle;
    if (cs&&cs.digest){
      var od=cs.digest.bind(cs);
      cs.digest=function(algo,buf){
        try{ var s=''; try{ s=new TextDecoder().decode(buf); }catch(_){}
          beacon('DIG','crypto.subtle.digest algo='+q(algo&&(algo.name||algo))+' in='+q(s).slice(0,60)+'  @@ '+shortStack()); }catch(_){}
        return od(algo,buf);
      };
    }
  }catch(e){}

  // ── (E) SendJscramblerLog 時間對齊(此刻之前的比對/charcode=檢查;之後 call=反制)──
  try{
    var real=null;
    function wrapSJL(fn){ return function(){ try{ beacon('SJL','>>> SendJscramblerLog("'+(arguments[0])+'") <<<  (之前的比對/charcode=檢查;之後 call=反制)'); }catch(e){} try{ return fn.apply(this,arguments); }catch(e){} }; }
    var pre=window.SendJscramblerLog;
    Object.defineProperty(window,'SendJscramblerLog',{configurable:true,get:function(){return real;},set:function(v){ real=(typeof v==='function')?wrapSJL(v):v; }});
    if (typeof pre==='function') real=wrapSJL(pre);
  }catch(e){}

  // 收尾:4 秒後 dump「被逐字讀但沒觸發 full-pass」的殘留(hash 可能只讀部分),或明確報「沒有逐字讀」。
  try{
    setTimeout(function(){
      var any=false;
      for (var k in ccMap){ var e=ccMap[k]; if (e.n>1){ any=true; beacon('CHAR','CHARCODE summary '+q(k)+' n='+e.n+'/len='+e.len+'  @@ '+e.stack); } }
      if (!any) beacon('INFO','CHARCODE summary:無 domain 字串被逐字元讀 → 不是 JS-charCodeAt hash(可能 ===/includes/bracket-index,或看 READ 是否命中)');
    },4000);
  }catch(e){}

  beacon('INFO','Phase1+ trace armed: methods + charCodeAt(hash指紋) + location-read + crypto.subtle + SJL');
})();
