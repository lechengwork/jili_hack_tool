// dl_node_probe.js — Route A:把 bundle.24017.js 灌進 Node 自我執行,讀出 code-integrity murmur 的
// 實際 (seed, output),好離線 forge。純離線,不碰真站/瀏覽器。
// 已證:bundle 會清掉 console/JSON/Array.prototype 方法(self-defending)→ 所有 built-in 在 eval 前存好、
//       用低階 fs.writeSync(fd) 輸出、eval 後還原原型。J3mw6 需 prepend bootstrap 當 global binding。
'use strict';
const fs = require('fs');
const path = require('path');

// ---- eval 前存好所有原生工具(bundle 會竄改全域) ----
const _writeSync = fs.writeSync, _openSync = fs.openSync;
const _stringify = JSON.stringify, _String = String;
const _getOPN = Object.getOwnPropertyNames, _getOPD = Object.getOwnPropertyDescriptor, _defP = Object.defineProperty, _keys = Object.keys;
const BUN = path.join(__dirname, '..', 'game_site_backup', 'uat-wbgame.jlfafafa3.com',
  'astarte2', '3.6', 'web-mobile', 'src', 'chunks', 'bundle.24017.js.orig');
const OUT = path.join(__dirname, 'dl_node_probe_out.json');
const fdOut = _openSync(OUT, 'w');
function log(s){ try{ _writeSync(2, String(s)+'\n'); }catch(e){} }   // stderr heartbeat

// ---- 最小瀏覽器 stub ----
const g = globalThis;
function def(n,v){ try{ g[n]=v; }catch(e){ try{ _defP(g,n,{value:v,configurable:true,writable:true}); }catch(e2){} } }
function noop(){ return noop; }
def('window', g); def('self', g); def('z6OAA', undefined);
const loc = { hostname:'uat-wbgame.jlfafafa3.com', host:'uat-wbgame.jlfafafa3.com',
  href:'https://uat-wbgame.jlfafafa3.com/fg5/', protocol:'https:', origin:'https://uat-wbgame.jlfafafa3.com',
  pathname:'/fg5/', search:'', hash:'', toString(){ return this.href; } };
def('location', loc);
def('document', { location:loc, createElement:()=>({style:{},setAttribute:noop,appendChild:noop,getContext:()=>null}),
  documentElement:{}, addEventListener:noop, removeEventListener:noop, getElementsByTagName:()=>[], querySelector:()=>null, cookie:'', referrer:'' });
def('navigator', { userAgent:'Mozilla/5.0', platform:'Win32', language:'zh-CN', languages:['zh-CN'] });
def('screen', { width:1920, height:1080 });
def('history', { pushState:noop, replaceState:noop });
def('localStorage', { getItem:()=>null, setItem:noop, removeItem:noop });
def('setInterval', ()=>0); def('clearInterval', noop); def('clearTimeout', noop); def('requestAnimationFrame', ()=>0);
def('addEventListener', noop); def('removeEventListener', noop);
def('WebSocket', function(){}); def('XMLHttpRequest', function(){ this.open=noop; this.send=noop; this.setRequestHeader=noop; });
def('Image', function(){}); def('fetch', ()=>({ then:()=>({catch:noop}), catch:noop }));
def('SendJscramblerLog', function(){ const L=g.__SJL||(g.__SJL=[]); L[L.length]=[].slice.call(arguments); });

// ---- J3mw6:定義成不可刪、set 被吃掉的 getter 全域(bundle 會試圖刪/覆寫它做 anti-tamper) ----
let _J3 = {};
const J3MODE = process.env.J3MODE || 'none';   // none | getterT | getterF | data
if (J3MODE==='getterT') { try { _defP(g,'J3mw6',{get(){return _J3;},set(v){if(v&&typeof v==='object')_J3=v;},configurable:true}); }catch(e){log('J3 def:'+e);} }
else if (J3MODE==='getterF') { try { _defP(g,'J3mw6',{get(){return _J3;},set(v){if(v&&typeof v==='object')_J3=v;},configurable:false}); }catch(e){log('J3 def:'+e);} }
else if (J3MODE==='data') { def('J3mw6', _J3); }
// 'none' = 不預先定義,讓 bundle 自宣告

// ---- 讀 bundle + 包 murmur ----
let src = fs.readFileSync(BUN, 'utf8');
const RET = 'return {t_ΟУx$а:х0h}';
const WRAP = 'return {t_ΟУx$а:function(_a,_b,_c){var _r=х0h(_a,_b,_c);' +
  'var _L=globalThis.__mlog||(globalThis.__mlog=[]);_L[_L.length]=[_b,(_c>>>0),(_r>>>0)];return _r;}}';
const hit = src.indexOf(RET);
log('[probe] murmur return literal @ '+hit+'  bundle code-units='+src.length);
if (process.env.NOWRAP) { log('[probe] NOWRAP=1 → 不注入 murmur wrapper(跑未改版)'); }
else if (hit >= 0) src = src.split(RET).join(WRAP);
else log('[probe] ⚠ murmur RET literal NOT matched — check unicode');

// ★ STUBREG=1:把 w6 的 body 改成回「全回 null 的 Proxy 註冊表」,繞過有狀態 opaque-predicate 洋蔥。
//   保持 h===J3mw6.w6 自檢通過(只改 body、函式身分不變)。賭 predicate 都回常數(post-crash 取樣=null)。
if (process.env.STUBREG) {
  const W6DEF = "J3mw6.w6=function h(){var u=J3mw6[435135],C=u.d8LsvFP;return h === J3mw6.w6 && (typeof C === 'function'?C.apply(u,arguments):C);};";
  const W6STUB = "J3mw6.w6=function h(){return (h===J3mw6.w6)&&(J3mw6.__rs||(J3mw6.__rs=new Proxy(function(){},{get:function(t,k){return function(){return null;};},apply:function(){return null;}})));};";
  if (src.indexOf(W6DEF) >= 0) { src = src.split(W6DEF).join(W6STUB); log('[probe] STUBREG=1 → w6 body 換成 all-null Proxy 註冊表'); }
  else log('[probe] ⚠ STUBREG: w6 定義字串沒對上(unicode/結構變了)');
}
// ★ 用 function 包裝(bundle 是模組體語義:內含的 function J3mw6(){} hoist 到此包裝頂端)
// 並在最前面注入 __cap 捕捉內部 J3mw6(閉包),eval 後可檢查其註冊表
if (!process.env.NOFNWRAP) src = '(function(){try{globalThis.__grab(J3mw6);globalThis.__caphit=1;}catch(e){globalThis.__caperr=(""+e);}\n' + src + '\n});';

// ---- 快照原型 ----
function snapshot(proto){ const d={}; const ks=_getOPN(proto); for (let i=0;i<ks.length;i++){ try{ d[ks[i]]=_getOPD(proto,ks[i]); }catch(e){} } return d; }
function restore(proto, snap){ for (const k in snap){ try{ _defP(proto,k,snap[k]); }catch(e){} } }
const SNAPS = [[Array.prototype,snapshot(Array.prototype)],[String.prototype,snapshot(String.prototype)],
  [Object.prototype,snapshot(Object.prototype)],[Function.prototype,snapshot(Function.prototype)]];

// ---- 攔 process.exit(bundle 可能主動退出) ----
const _exit = process.exit;
try { process.exit = function(c){ throw new Error('__exit('+c+')__'); }; } catch(e){}

// ---- 跑 ----
// Node 端捕捉(即使 bundle 清 globalThis 也留得住)
let capturedJ = null, grabCalled = false;
g.__premarker = 42;
g.__grab = function(x){ grabCalled = true; capturedJ = x; };
let errObj = null, fnType = null;
try { const _fn = (0, eval)(src); fnType = typeof _fn; if (typeof _fn === 'function') _fn.call(g); }
catch (e) { errObj = e; }

// ---- 先還原原型(bundle 清了 String/Array 方法),之後才能安全做字串處理 ----
for (let i=0;i<SNAPS.length;i++) restore(SNAPS[i][0], SNAPS[i][1]);
try { process.exit = _exit; } catch(e){}
let threw = null, stack = null;
if (errObj) { try { threw = errObj.message || _String(errObj); } catch(e){ threw='(err)'; }
  try { stack = errObj.stack ? _String(errObj.stack).split('\n').slice(0,8).join(' || ') : null; } catch(e){} }

const mlog = g.__mlog; const n = (mlog && typeof mlog.length==='number') ? mlog.length : 0;
let jkeys=-1; try{ jkeys=_keys(g.J3mw6).length; }catch(e){}
const rows=[]; for (let i=0;i<n;i++){ const m=mlog[i]; if(m) rows.push({i:i,len:m[0],seed:(m[1]>>>0),out:(m[2]>>>0)}); }
let sjl=-1; try{ sjl=(g.__SJL&&g.__SJL.length)||0; }catch(e){}
// ---- 檢查內部 J3mw6 的 opaque-predicate 註冊表(w6 = J3mw6[435135].d8LsvFP) ----
let reg = { captured:false };
try {
  const J = capturedJ;
  if (J) {
    reg.captured = true;
    reg.internal_j3_keys = _keys(J).length;
    reg.all_keys = _keys(J);
    ['S2','f8'].forEach(function(k){
      reg['type_'+k] = typeof J[k];
      if (typeof J[k]==='function'){ try{ const r=J[k](); reg['call_'+k+'_ret']=typeof r; }catch(e){ reg['call_'+k+'_err']=(e&&e.message)||_String(e); } }
    });
    reg.has_435135 = (typeof J[435135] !== 'undefined');
    if (J[435135]) {
      reg.k435135 = _keys(J[435135]);
      try { reg.d8_type = typeof J[435135].d8LsvFP; reg.d8_val = _String(J[435135].d8LsvFP).slice(0,120); }catch(e){}
      try { const opd=_getOPD(J[435135],'d8LsvFP'); reg.d8_desc = opd?{get:typeof opd.get,set:typeof opd.set,value:typeof opd.value,writable:opd.writable}:null; }catch(e){}
      // ★ d8LsvFP post-crash 是物件(=註冊表本身?) → dump keys + 取樣幾個 present index 的回傳
      try {
        const D = J[435135].d8LsvFP;
        if (D && typeof D === 'object') {
          const dk = _keys(D);
          reg.d8obj_keycount = dk.length;
          reg.d8obj_keys_head = dk.slice(0,20);
          reg.d8obj_keys_tail = dk.slice(-8);
          reg.d8obj_has = { '0':(0 in D), '670':(670 in D), '801':(801 in D), '612':(612 in D) };
          const samp = {};
          [0,670,612,67,41,5,6,801].forEach(function(idx){
            try { const v=D[idx]; samp[idx] = typeof v + (typeof v==='function' ? (' ret='+_String((function(){try{return v();}catch(e){return 'ERR:'+((e&&e.message)||e);}})())) : ''); }
            catch(e){ samp[idx]='ACCESS_ERR:'+((e&&e.message)||e); }
          });
          reg.d8obj_sample = samp;
        }
      } catch(e){ reg.d8obj_err = (e&&e.message)||_String(e); }
      let arr = null;
      try { arr = J[435135].d8LsvFP(); } catch(e){ reg.d8_err = (e&&e.message)||_String(e); }
      if (arr) {
        reg.reg_type = (typeof arr) + (arr && arr.length!=null?(' len='+arr.length):'');
        // 哪些 index 有值 / 是 function
        const present=[]; const missing=[];
        [0,801,670,612,67,41,956,76,1,33,15].forEach(function(idx){
          const v = arr[idx]; const t = (typeof v);
          (t==='function'?present:missing).push(idx+':'+t);
        });
        reg.probe_indices_present = present;
        reg.probe_indices_missing = missing;
        // 若是陣列,列出實際 defined index 數
        try { let c=0; for (const k in arr){ c++; } reg.reg_defined_count = c; } catch(e){}
      }
    }
  }
} catch(e){ reg.err = (e&&e.message)||_String(e); }
let js='';
let caphit=null,caperr=null,premark=null; try{caphit=g.__caphit;}catch(e){} try{caperr=g.__caperr;}catch(e){} try{premark=g.__premarker;}catch(e){}
try { js = _stringify({ threw:threw, stack:stack, fnType:fnType, grabCalled:grabCalled, caphit:caphit, caperr:caperr, premarker_survived:(premark===42), j3mw6_keys:jkeys, murmur_calls:n, sjl:sjl, reg:reg, rows:rows }, null, 1); }
catch(e){ js = '{"stringify_failed":"'+(e&&e.message||e)+'","murmur_calls":'+n+'}'; }
try { _writeSync(fdOut, js); } catch(e){ log('writeSync failed: '+(e&&e.message||e)); }
log('[probe] DONE threw='+threw+' murmur_calls='+n+' __caphit='+(g.__caphit)+' __caperr='+(g.__caperr)+' typeof __cap='+(typeof g.__cap)+' -> '+OUT);
