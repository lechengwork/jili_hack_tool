// capture_shim.js — 【CAPTURE 模式】純網頁擷取【真伺服器】封包(免 Frida、免 netlog)。
//
// 不 patch 公鑰。讓遊戲照常用內建真公鑰、打真站;shim 只旁路側錄。三條 hook,兩條拿 key(哪條中都行):
//   ★ 主要拿 key:hook getRandomValues → 側錄 client 臨時私鑰候選(首 32B)。decrypt_capture --grv
//     會用 req 的 f4 反查對上的 priv → 導 key。最穩:不吃記憶體佈局/時序。
//   ◆ 備援拿 key:hook instantiate/instantiateStreaming/new Instance + 掃 importObject → 收集所有
//     WASM linear memory,用「內建 server pub chunk#0 在 +1048576」錨認出 crypto 記憶體 → 讀 @1108480 shared。
//   ● 拿封包:hook fetch → 側錄每筆 /fg5/req 的 req+resp bytes。
//   全部 POST 到本地 /__capture__(同源=document host=localhost)。載體 prepend 進 polyfills.bundle(不加新 <script>)。
// __ORIG0__ 由 server 載入時代入(wasm_pub_patches.json[0].orig 的 byte 陣列)= 內建真 server pub chunk#0。
(function(){
  var CAP = '/__capture__', SH_OFF = 1108480, PUB_OFF = 1048576;
  var ORIG0 = __ORIG0__;
  var W = (typeof self !== 'undefined') ? self : window;
  var ofetch = (W && W.fetch) ? W.fetch.bind(W) : null;
  var mems = [], keySent = false, seq = 0, grvCount = 0, keyMissReported = false;

  function report(m){ try{ (new Image()).src='/__wasmpatch__/'+encodeURIComponent(m); }catch(e){} }
  function toHex(a){ var s=''; for(var i=0;i<a.length;i++) s+=('0'+a[i].toString(16)).slice(-2); return s; }
  function eqAt(a,i,arr){ if(!arr.length) return false; for(var j=0;j<arr.length;j++) if(a[i+j]!==arr[j]) return false; return true; }
  // ★不要用 keepalive★:它有 64KiB 的「在途總量」配額(瀏覽器規範),autoplay 連轉時
  // 配額一滿,後續 POST 會被瀏覽器直接拒絕。而且 promise rejection 外層 try/catch 接不到,
  // 失敗會完全靜默 —— 症狀就是 [shim-report] 還在印、資料卻沒進來。
  // 一律補 .catch 回報,寧可吵也不要靜默掉資料。
  var beaconFail = 0;
  function beacon(obj){
    try{
      if(!ofetch) return;
      ofetch(CAP, {method:'POST', body:JSON.stringify(obj),
        headers:{'Content-Type':'application/json'}})
        .catch(function(e){ if(++beaconFail <= 20) report('BEACON-FAIL#'+beaconFail+' '+e); });
    }catch(e){ report('BEACON-THROW '+e); }
  }

  // ── ★ getRandomValues:側錄 client 臨時私鑰候選 ──
  try{
    if(W.crypto && typeof W.crypto.getRandomValues === 'function'){
      var ogrv = W.crypto.getRandomValues.bind(W.crypto);
      W.crypto.getRandomValues = function(arr){
        var r = ogrv(arr);
        try{
          if(arr && arr.byteLength >= 32 && grvCount < 12){
            var u = new Uint8Array(arr.buffer, arr.byteOffset||0, arr.byteLength);
            beacon({grv: toHex(u.subarray(0,32))}); grvCount++;
            report('grv#'+grvCount+' '+arr.byteLength+'B');
          }
        }catch(e){}
        return r;
      };
      report('getRandomValues hooked');
    }
  }catch(e){ report('grv hook err '+e); }

  // ── ◆ 收集所有 WASM linear memory ──
  function addMem(m){
    try{
      if(!m || typeof WebAssembly==='undefined' || !(m instanceof WebAssembly.Memory)) return;
      if(mems.indexOf(m) >= 0) return;
      mems.push(m);
      var a = new Uint8Array(m.buffer);
      var anchor = (a.length >= PUB_OFF+ORIG0.length) ? (eqAt(a,PUB_OFF,ORIG0)?1:0) : -1;
      report('mem#'+mems.length+' '+a.length+'B anchor='+anchor);
    }catch(e){}
  }
  function scanImports(imp){                 // memory 可能是 import 進去的,淺掃 importObject
    try{
      if(!imp || typeof imp!=='object') return;
      for(var k in imp){ var g=imp[k]; if(g&&typeof g==='object'){ for(var k2 in g){ addMem(g[k2]); } addMem(g); } }
    }catch(e){}
  }
  function grabFromInstance(inst, imp){
    try{ if(inst && inst.exports) addMem(inst.exports.memory); }catch(e){}
    scanImports(imp);
  }
  if(typeof WebAssembly !== 'undefined'){
    if(WebAssembly.instantiate){
      var oi = WebAssembly.instantiate;
      WebAssembly.instantiate = function(a, b){
        return Promise.resolve(oi.apply(WebAssembly, arguments)).then(function(res){
          grabFromInstance(res && res.instance ? res.instance : res, b); return res;
        });
      };
    }
    if(WebAssembly.instantiateStreaming){
      var ois = WebAssembly.instantiateStreaming;
      WebAssembly.instantiateStreaming = function(a, b){
        return Promise.resolve(ois.apply(WebAssembly, arguments)).then(function(res){
          grabFromInstance(res && res.instance ? res.instance : res, b); return res;
        });
      };
    }
    if(WebAssembly.Instance){                 // 同步建構子路徑(SystemJS 可能走這條)
      var OInst = WebAssembly.Instance;
      var WInst = function(mod, imp){ var i = new OInst(mod, imp); grabFromInstance(i, imp); return i; };
      WInst.prototype = OInst.prototype;
      try{ WebAssembly.Instance = WInst; }catch(e){}
    }
  }
  function readKey(){                          // 掃所有收集到的 memory 找 shared@1108480
    for(var i=0;i<mems.length;i++){
      try{
        var a = new Uint8Array(mems[i].buffer);   // grow 會換 buffer,每次重取
        if(a.length < SH_OFF+32 || !eqAt(a,PUB_OFF,ORIG0)) continue;
        var z=true; for(var j=0;j<32;j++){ if(a[SH_OFF+j]!==0){ z=false; break; } }
        if(z) continue;
        return toHex(a.subarray(SH_OFF, SH_OFF+32));
      }catch(e){}
    }
    return null;
  }

  // ── ● fetch:側錄 /fg5/req ──
  function isReq(url){ return url && url.indexOf('/fg5/req') >= 0; }
  function reqBodyHexP(input, init){
    try{
      if(init && init.body !== undefined && init.body !== null){
        var b = init.body;
        if(b instanceof ArrayBuffer) return Promise.resolve(toHex(new Uint8Array(b)));
        if(ArrayBuffer.isView(b)) return Promise.resolve(toHex(new Uint8Array(b.buffer, b.byteOffset, b.byteLength)));
        if(typeof Blob!=='undefined' && b instanceof Blob) return b.arrayBuffer().then(function(x){return toHex(new Uint8Array(x));});
        return Promise.resolve('');
      }
      if(input && typeof input.clone === 'function')
        return input.clone().arrayBuffer().then(function(x){return toHex(new Uint8Array(x));}).catch(function(){return '';});
    }catch(e){}
    return Promise.resolve('');
  }
  if(ofetch){
    W.fetch = function(input, init){
      var url = (typeof input === 'string') ? input : (input && input.url) || '';
      if(url.indexOf(CAP) >= 0 || !isReq(url)) return ofetch.apply(this, arguments);
      var myseq = ++seq;
      var reqP = reqBodyHexP(input, init);
      return ofetch.apply(this, arguments).then(function(resp){
        try{
          resp.clone().arrayBuffer().then(function(buf){
            reqP.then(function(rq){
              var rec = {seq:myseq, req_body_hex:rq, resp_body_hex:toHex(new Uint8Array(buf))};
              if(!keySent){ var k = readKey(); if(k){ rec.key = k; keySent = true; } }
              beacon(rec);
              var tag = rec.key ? ' +KEY' : '';
              report('capture seq='+myseq+' req='+(rq.length/2)+'B resp='+buf.byteLength+'B'+tag);
              if(!rec.key && !keyMissReported && myseq>=3){          // 診斷:key 還沒撈到
                keyMissReported = true;
                report('KEYMISS mems='+mems.length+' grv='+grvCount+' (用 --grv 退路)');
              }
            });
          }).catch(function(){});
        }catch(e){}
        return resp;
      });
    };
  }
  report('capture-shim installed (grv+mem+fetch hooks; NO pubkey patch)');
})();
