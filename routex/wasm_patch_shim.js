// wasm_patch_shim.js — 【Test C2】完整 compile-hook byte-patch,經「塞進 polyfills.bundle」送進去(INJECT_BUNDLE=1)。
// C1 已證實:改現有 bundle 內容(不加新 <script>)= Jscrambler 沒抓 → 遊戲活到 /fg5/req。
// 本版:hook WebAssembly.compile / compileStreaming,在編譯前的 bytes 換掉 8 個內建 server pub chunk → mock pub。
//   最小化:不換 Function.prototype.toString、不用 MutationObserver、不做 toString 偽裝(先驗 22de5 有沒有查 compile 原生性)。
//   不碰 Module(靜態方法保住)、不碰 instantiate/instantiateStreaming/Instance。
//   若通:pub 在編譯前就換好 → 遊戲導的 X25519 shared 自然對 → seq=2,免 Frida/FIX_SHARED。
(function(){
  var REPLS = [{"o": [200, 95, 203, 243, 223, 4, 213, 0], "n": [39, 17, 22, 224, 3, 107, 27, 160]}, {"o": [140, 0, 220, 164, 51, 112, 48, 234], "n": [186, 249, 42, 70, 61, 181, 190, 196]}, {"o": [89, 1, 58, 213, 167, 209, 173, 75], "n": [192, 214, 200, 84, 36, 71, 70, 225]}, {"o": [209, 156, 76, 11, 51, 66, 234, 160], "n": [223, 171, 164, 238, 138, 183, 75, 50]}, {"o": [23, 76, 176, 90, 176, 162, 112, 189], "n": [127, 77, 226, 178, 233, 128, 67, 184]}, {"o": [43, 109, 47, 98, 252, 249, 76], "n": [225, 198, 9, 226, 8, 99, 78]}, {"o": [67, 134, 57, 243, 206, 196, 137, 92], "n": [55, 100, 243, 48, 196, 165, 57, 181]}, {"o": [192, 253, 139, 159, 42, 178, 85, 38], "n": [154, 226, 76, 46, 131, 242, 21, 30]}];
  function rep(m){ try{ (new Image()).src='/__wasmpatch__/'+encodeURIComponent(m); }catch(e){} }
  function nameLen(fn, orig){
    try{ Object.defineProperty(fn,'name',{value:orig.name,configurable:true}); }catch(e){}
    try{ Object.defineProperty(fn,'length',{value:orig.length,configurable:true}); }catch(e){}
    return fn;
  }
  function toU8copy(src){
    try{
      if(src instanceof ArrayBuffer) return new Uint8Array(src.slice(0));
      if(ArrayBuffer.isView(src)) return new Uint8Array(new Uint8Array(src.buffer, src.byteOffset, src.byteLength));
    }catch(e){}
    return null;
  }
  function patchBytes(u8){
    var done=0;
    for(var k=0;k<REPLS.length;k++){
      var o=REPLS[k].o, n=REPLS[k].n, L=o.length, lim=u8.length-L;
      for(var i=0;i<=lim;i++){
        var ok=true; for(var j=0;j<L;j++){ if(u8[i+j]!==o[j]){ok=false;break;} }
        if(ok){ u8.set(n,i); done++; break; }
      }
    }
    if(done){ try{ window.__mockPatch=(window.__mockPatch||0)+done; }catch(e){} }
    return done;
  }
  var oCo = WebAssembly.compile;
  if(oCo){
    var wCo = ({ compile(bytes){
      var cp = toU8copy(bytes);
      if(cp){ var d=patchBytes(cp); rep('compile d='+d); return oCo.call(WebAssembly, cp); }
      rep('compile nobytes');
      return oCo.apply(WebAssembly, arguments);
    } }).compile;
    WebAssembly.compile = nameLen(wCo, oCo);
  }
  if(WebAssembly.compileStreaming){
    var oCs = WebAssembly.compileStreaming;
    var wCs = ({ compileStreaming(source){
      return Promise.resolve(source).then(function(r){
        if(!r || typeof r.arrayBuffer!=='function'){ rep('cs noresp'); return oCs.call(WebAssembly, r); }
        return r.arrayBuffer().then(function(buf){ var d=patchBytes(new Uint8Array(buf)); rep('cs d='+d); return (oCo||oCs).call(WebAssembly, buf); });
      });
    } }).compileStreaming;
    WebAssembly.compileStreaming = nameLen(wCs, oCs);
  }
  rep('installed C2 compile-hook via polyfills');
})();
