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
  // CfT 152 / 新 Chrome 常走 instantiateStreaming 載 wasm,compile-hook 抓不到 → 補這條(jade shim 已驗安全)。
  if(WebAssembly.instantiateStreaming){
    var oIs = WebAssembly.instantiateStreaming;
    var wIs = ({ instantiateStreaming(source, imports){
      return Promise.resolve(source).then(function(r){
        if(!r || typeof r.arrayBuffer!=='function'){ rep('is noresp'); return oIs.call(WebAssembly, r, imports); }
        return r.arrayBuffer().then(function(buf){ var cp=new Uint8Array(buf); var d=patchBytes(cp); rep('is d='+d); return WebAssembly.instantiate(cp, imports); });
      });
    } }).instantiateStreaming;
    WebAssembly.instantiateStreaming = nameLen(wIs, oIs);
  }
  rep('installed C2 compile-hook via polyfills');
})();

// Replay-only UI override: disable IconBox_Side and its Btn_Main TIP tab.
// Keep the 100 ms startup/fallback scan, and also scan before every Cocos draw
// so a spin/tween reactivating the nodes cannot render between timer ticks.
(function(){
  var report = function(message){
    try { (new Image()).src = '/__wasmpatch__/' + encodeURIComponent(message); } catch(e) {}
  };
  var engineReported = false;
  var sceneReported = false;
  var cocosEngine = null;
  var importingEngine = false;
  var sideReported = false;
  var missingMainReported = false;
  var sideHiddenReported = false;
  var mainHiddenReported = false;
  var drawGuardDirector = null;
  var drawGuardEvent = null;
  var updateGuardEvent = null;
  var drawGuardErrorReported = false;
  var sideRehiddenCount = 0;
  var mainRehiddenCount = 0;
  var webPageReports = new WeakMap();
  var closingWebPages = new WeakSet();
  function inspectWebPage(node, engine) {
    if (!node.activeInHierarchy) {
      closingWebPages.delete(node);
      return;
    }
    var components = engine.Component && node.getComponents ? node.getComponents(engine.Component) : [];
    var title = '';
    var hasClose = false;
    var closeController = null;
    for (var i = 0; i < components.length; i++) {
      var component = components[i];
      if (typeof component.OnClose === 'function') {
        hasClose = true;
        closeController = component;
      }
      if (component.m_titleLabel && typeof component.m_titleLabel.string === 'string') {
        title = component.m_titleLabel.string;
      }
    }
    var views = engine.WebView && node.getComponentsInChildren ? node.getComponentsInChildren(engine.WebView) : [];
    var urls = [];
    var landingPage = false;
    function inspectUrl(value) {
      if (!value) return;
      // Keep SSO/session/query values out of replay diagnostics.
      try {
        var url = new URL(value, location.href);
        var visibleUrl = url.origin + url.pathname;
        if (urls.indexOf(visibleUrl) === -1) urls.push(visibleUrl);
        if (/\/landingpage(?:[/.]|$)/i.test(url.pathname)) landingPage = true;
      } catch(e) {}
    }
    for (var j = 0; j < views.length; j++) {
      inspectUrl(views[j].url);
    }
    // This build's Events page uses a separately created DOM iframe; it is
    // absent from Common_WebPage.getComponentsInChildren(cc.WebView).
    var frames = document.querySelectorAll('iframe');
    for (var k = 0; k < frames.length; k++) {
      var frameUrl = frames[k].getAttribute('src');
      if (frameUrl && /\/landingpage(?:[/?#.]|$)/i.test(frameUrl)) inspectUrl(frameUrl);
    }
    var signature = JSON.stringify({title: title, urls: urls, onClose: hasClose});
    if (webPageReports.get(node) !== signature) {
      webPageReports.set(node, signature);
      report('WEBPAGE Common_WebPage visible ' + signature);
    }
    if (landingPage && /^(events?|eventos|活動|活动)$/i.test(title.trim())
        && closeController && !closingWebPages.has(node)) {
      closingWebPages.add(node);
      try {
        // Use the exact callback bound to Btn_X. Keep its iframe cleanup and
        // initialization callbacks instead of deactivating the modal ourselves.
        closeController.OnClose();
        report('WEBPAGE activity OnClose called ' + JSON.stringify({title: title, urls: urls}));
      } catch(e) {
        report('WEBPAGE activity OnClose error: ' + String(e).slice(0, 160));
      }
    }
  }
  function hideMainUnder(node) {
    if (!node) return false;
    var found = false;
    if (node.name === 'Btn_Main') {
      found = true;
      if (node.active) {
        node.active = false;
        if (!mainHiddenReported) { mainHiddenReported = true; report('TIP Btn_Main active=false'); }
        else if (++mainRehiddenCount <= 3) { report('TIP Btn_Main re-enabled; active=false again #' + mainRehiddenCount); }
      }
    }
    var children = node.children || [];
    for (var i = 0; i < children.length; i++) {
      if (hideMainUnder(children[i])) found = true;
    }
    return found;
  }
  var scan = function(){
    try {
      var engine = window.cc || cocosEngine;
      if (!engine && window.System && System.import && !importingEngine) {
        importingEngine = true;
        System.import('cc').then(function(module){ cocosEngine = module; importingEngine = false; scan(); })
          .catch(function(){ importingEngine = false; });
      }
      if (engine && !engineReported) { engineReported = true; report('TIP shim cc ready'); }
      var director = engine && engine.director;
      var beforeDraw = engine && engine.Director && engine.Director.EVENT_BEFORE_DRAW;
      var afterUpdate = engine && engine.Director && engine.Director.EVENT_AFTER_UPDATE;
      if (director && beforeDraw && director.on && drawGuardDirector !== director) {
        if (drawGuardDirector && drawGuardDirector.off) {
          drawGuardDirector.off(drawGuardEvent, scan);
          if (updateGuardEvent) drawGuardDirector.off(updateGuardEvent, scan);
        }
        director.on(beforeDraw, scan);
        // AFTER_UPDATE runs before Cocos processes deferred node destruction.
        // A normal OnClose can therefore finish before the modal is drawn.
        if (afterUpdate) director.on(afterUpdate, scan);
        drawGuardDirector = director;
        drawGuardEvent = beforeDraw;
        updateGuardEvent = afterUpdate;
        report('TIP before-draw guard installed');
        if (afterUpdate) report('WEBPAGE after-update activity guard installed');
      }
      var scene = director && director.getScene && director.getScene();
      if (scene) {
        if (!sceneReported) { sceneReported = true; report('TIP shim scene ready'); }
        var stack = [scene];
        while (stack.length) {
          var node = stack.pop();
          if (node && node.name === 'Common_WebPage') inspectWebPage(node, engine);
          if (node && node.name === 'IconBox_Side') {
            if (!sideReported) { sideReported = true; report('TIP IconBox_Side found'); }
            if (node.active) {
              node.active = false;
              if (!sideHiddenReported) { sideHiddenReported = true; report('TIP IconBox_Side active=false'); }
              else if (++sideRehiddenCount <= 3) { report('TIP IconBox_Side re-enabled; active=false again #' + sideRehiddenCount); }
            }
            var found = false;
            var children = node.children || [];
            for (var i = 0; i < children.length; i++) {
              if (hideMainUnder(children[i])) found = true;
            }
            if (!found && !missingMainReported) {
              missingMainReported = true;
              report('TIP Btn_Main not found under IconBox_Side');
            }
          }
          if (node && node.children) {
            for (var j = 0; j < node.children.length; j++) stack.push(node.children[j]);
          }
        }
      }
    } catch(e) {
      if (!drawGuardErrorReported) {
        drawGuardErrorReported = true;
        report('TIP guard error: ' + String(e).slice(0, 120));
      }
    }
  };
  // The draw callback must not schedule timers: that would add a new polling
  // loop on every rendered frame. Only this fallback loop owns the timer.
  var poll = function(){
    scan();
    setTimeout(poll, 100);
  };
  poll();
})();
