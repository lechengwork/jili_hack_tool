// main-world，document_start：在遊戲 bundle 載入前包住 WebCrypto。
// 攔到的東西用 window.postMessage 丟給 isolated-world 的 relay.js。
(function () {
  "use strict";
  try { fetch("http://127.0.0.1:8099/hooklog",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({op:"TOP-BEACON",href:location.href})}).catch(function(){}); } catch(e){}
  function hex(buf) {
    try {
      var b = buf instanceof ArrayBuffer ? new Uint8Array(buf)
            : (ArrayBuffer.isView(buf) ? new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength) : null);
      if (!b) return null;
      var s = ""; for (var i = 0; i < b.length; i++) s += b[i].toString(16).padStart(2, "0");
      return s;
    } catch (e) { return null; }
  }
  function send(rec) {
    try { window.postMessage({ __jiliHook: true, rec: rec }, "*"); } catch (e) {}
    try { fetch("http://127.0.0.1:8099/hooklog", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(Object.assign({via:"direct"},rec))}).catch(function(){}); } catch (e) {}
  }
  function algInfo(a) {
    if (!a) return a;
    if (typeof a === "string") return { name: a };
    var o = { name: a.name };
    if (a.iv) o.iv = hex(a.iv);
    if (a.counter) o.counter = hex(a.counter);
    if (a.nonce) o.nonce = hex(a.nonce);
    if (a.additionalData) o.aad = hex(a.additionalData);
    if (a.tagLength) o.tagLength = a.tagLength;
    if (a.length) o.length = a.length;
    if (a.public) o.public = "<CryptoKey>";
    if (a.info) o.info = hex(a.info);
    if (a.salt) o.salt = hex(a.salt);
    if (a.hash) o.hash = (a.hash.name || a.hash);
    if (a.namedCurve) o.namedCurve = a.namedCurve;
    return o;
  }

  var C = window.crypto, S = C && C.subtle;

  // getRandomValues：私鑰種子多半從這來
  if (C && C.getRandomValues) {
    var grv = C.getRandomValues.bind(C);
    C.getRandomValues = function (arr) {
      var r = grv(arr);
      send({ op: "getRandomValues", out: hex(r), len: r && r.length, stack: (new Error()).stack });
      return r;
    };
  }

  if (S) {
    var methods = ["decrypt", "encrypt", "deriveBits", "deriveKey", "importKey",
                   "exportKey", "generateKey", "digest", "sign", "verify", "wrapKey", "unwrapKey"];
    methods.forEach(function (m) {
      if (typeof S[m] !== "function") return;
      var orig = S[m].bind(S);
      S[m] = function () {
        var args = arguments;
        var rec = { op: "subtle." + m, alg: algInfo(args[0]), stack: (new Error()).stack };
        // 常見簽名：decrypt/encrypt(alg,key,data)；digest(alg,data)；deriveBits(alg,key,len)
        if (m === "decrypt" || m === "encrypt") rec.in = hex(args[2]);
        if (m === "digest") rec.in = hex(args[1]);
        if (m === "importKey") { rec.format = args[0]; rec.alg = algInfo(args[2]); if (args[0] === "raw") rec.rawKey = hex(args[1]); }
        if (m === "unwrapKey") { rec.wrapped = hex(args[1]); rec.alg = algInfo(args[3]); }
        var p;
        try { p = orig.apply(S, args); } catch (e) { rec.err = String(e); send(rec); throw e; }
        return p.then(function (out) {
          if (out instanceof ArrayBuffer) rec.out = hex(out);
          else rec.out = "<" + (out && out.constructor && out.constructor.name) + ">";
          send(rec);
          return out;
        }, function (e) { rec.err = String(e); send(rec); throw e; });
      };
      // 讓 toString 看起來像原生，躲偵測
      try { S[m].toString = function () { return "function " + m + "() { [native code] }"; }; } catch (e) {}
    });
  }
  send({ op: "hook-installed", hasSubtle: !!S, ua: navigator.userAgent });
})();
