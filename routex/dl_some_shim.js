// dl_some_shim.js v3 — 純診斷:不強制、不還原。記錄載入全程每個「每項 .length===6」的 Array 迭代呼叫,
// 看真 domain 表(應是 6 元素陣列、含大 hash)在 bundle.24017 載入時走哪個方法、長什麼樣。
// 上一版證明檢查走 Array.prototype(filter/find 類),但 one-shot 被早期誤中(2 個 6 字元字串)用掉了。
// 這版全程掛著、每個 distinct 簽名記一次(附第一項 JSON 預覽),看到真表就能精準強制。
(function(){
  function rep(m){ try{ (new Image()).src='/__wasmpatch__/'+encodeURIComponent(m); }catch(e){} }
  var A=Array.prototype;
  var names=['some','every','find','findIndex','filter','map','findLast','findLastIndex','flatMap'];
  var seen={}, cap=0;
  function tableLike(arr){
    try{
      if(!Array.isArray(arr)) return false;
      var n=arr.length; if(n<2||n>5000) return false;
      for(var i=0;i<n;i++){ var e=arr[i]; if(e==null || e.length!==6) return false; }
      return true;
    }catch(e){ return false; }
  }
  function prev(e0){ try{ return JSON.stringify(e0).slice(0,90); }catch(e){ return String(e0).slice(0,90); } }
  names.forEach(function(name){
    var orig=A[name]; if(typeof orig!=='function') return;
    A[name]=function(cb){
      try{
        if(cap<30 && typeof cb==='function' && tableLike(this)){
          var e0=this[0];
          var sig=name+'|'+this.length+'|'+(typeof e0)+'|'+Array.isArray(e0)+'|'+(e0&&e0.length);
          if(!seen[sig]){ seen[sig]=1; cap++; rep('DLSOME '+name+' len='+this.length+' e0type='+(typeof e0)+' isArr='+Array.isArray(e0)+' e0='+prev(e0)); }
        }
      }catch(e){}
      return orig.apply(this, arguments);
    };
    try{ A[name].toString=function(){return orig.toString();}; }catch(e){}
  });
  rep('DLSOME v3 diag armed (log-only, no force)');
})();
