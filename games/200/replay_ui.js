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
