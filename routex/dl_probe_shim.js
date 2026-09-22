// dl_probe_shim.js — 【Jscrambler Domain Lock 破解 PoC / 探路】只做「location 網域偽裝」。
//
// 情境:document 在自訂網域(如 myslot.test)時,22de5 的 Domain Lock 讀 window.location 比對允許清單→
//       不合就自毀/卡 loading。本 shim 從 polyfills 最先跑,逐一嘗試把「可攔截、且與讀參數無關」的
//       網域讀取點覆寫成「看起來是 jili」——含 query 的點(URL/href)用「jili host + 真 path + 真 query」
//       偽裝,確保遊戲/wasm 讀 ssoKey/be/gs 不會壞。
//
// 判讀(看 mock log 的 ★★★ [shim-report] DLPROBE …):
//   • 每個覆寫點回報 OK/FAIL(哪些能攔、哪些被瀏覽器擋)。
//   • 若遊戲衝過 loading → 出現 [sso]/[fg5] kind=handshake → init  = ★Lock 讀的是可攔截屬性 = 可破★。
//   • 若仍卡在 loading、且全是 FAIL 或 OK 了還是卡 → Lock 讀不可偽造的 location.hostname/href → 需更深 RE。
(function(){
  var FQDN='uat-wbgame.jlfafafa3.com', ORIGIN='https://'+FQDN;
  var P='/fg5/', S='';
  try{ P=location.pathname||P; S=location.search||''; }catch(e){}
  var HREF=ORIGIN+P+S;                       // 只換 host,保留真 path + 真 query
  function rep(m){ try{ (new Image()).src='/__wasmpatch__/'+encodeURIComponent('DLPROBE '+m); }catch(e){} }
  function tryDef(obj,prop,val,label){
    try{ Object.defineProperty(obj,prop,{configurable:true,get:function(){return val;}}); rep('OK '+label); return true; }
    catch(e){ rep('FAIL '+label+' :: '+((e&&e.message)||String(e)).slice(0,60)); return false; }
  }
  // ── 與「讀參數」無關的網域讀取點(安全偽裝) ──
  tryDef(Document.prototype,'domain',   FQDN,     'document.domain');
  tryDef(Document.prototype,'referrer', ORIGIN+'/','document.referrer');
  try{ Object.defineProperty(window,'origin',{configurable:true,get:function(){return ORIGIN;}}); rep('OK window.origin'); }
  catch(e){ rep('FAIL window.origin :: '+((e&&e.message)||String(e)).slice(0,60)); }
  // ── 含 query 的點:jili host + 真 path + 真 query(讀參數不壞) ──
  tryDef(Document.prototype,'URL',        HREF, 'document.URL');
  tryDef(Document.prototype,'documentURI',HREF, 'document.documentURI');
  tryDef(Document.prototype,'baseURI',    HREF, 'document.baseURI');
  // ── Location.prototype 網域屬性(多半 unforgeable → FAIL,但要試);href 保留 query ──
  tryDef(Location.prototype,'hostname', FQDN,  'Location.hostname');
  tryDef(Location.prototype,'host',     FQDN,  'Location.host');
  tryDef(Location.prototype,'origin',   ORIGIN,'Location.origin');
  tryDef(Location.prototype,'href',     HREF,  'Location.href');
  // ── 最後補:有些 build 用 (''+location) / location.toString() / location.valueOf() 讀 ──
  try{ Location.prototype.toString=function(){return HREF;}; rep('OK Location.toString'); }catch(e){ rep('FAIL Location.toString :: '+((e&&e.message)||String(e)).slice(0,60)); }
  try{ Location.prototype.valueOf =function(){return HREF;}; rep('OK Location.valueOf'); }catch(e){ rep('FAIL Location.valueOf :: '+((e&&e.message)||String(e)).slice(0,60)); }
  // 再明確測 document.domain / document.location(instance)
  try{ Object.defineProperty(document,'domain',{configurable:true,get:function(){return FQDN;}}); rep('OK document(instance).domain'); }catch(e){ rep('FAIL document(instance).domain :: '+((e&&e.message)||String(e)).slice(0,60)); }
  // 驗證有沒有真的生效:讀回來看是 jili 還是 myslot
  try{ rep('VERIFY location.hostname='+location.hostname+' href.host='+(new URL(location.href).host)+' doc.domain='+document.domain); }catch(e){ rep('VERIFY err '+e); }
  // ── 有些 Jscrambler build 用 ancestorOrigins / top.location;試 top ──
  try{ if(window.top && window.top!==window){ /* 跨 realm,通常擋 */ } rep('top '+(window.top===window?'self':'framed')); }catch(e){}
  rep('installed (spoof host='+FQDN+', kept search len='+S.length+')');
})();
