/* err_probe_shim.js — 把前端沒被接住的錯誤送回 mock 的 log。
 *
 * 為什麼要這支:index4(重轉一軸)那局,轉軸停住後前端就不動了,而且【沒有再發任何請求】
 * ——代表它是在 JS 裡爆掉,不是在等網路。不能開 DevTools(會觸發 Jscrambler self-defending),
 * 所以改用最溫和的方式:只加 error / unhandledrejection 兩個 listener。
 *
 * ★刻意不碰★ Function.prototype.toString、eval、Object.defineProperty ——
 *   那三個是 Jscrambler 在守的原語,碰了整個 bundle 會炸(見 jili-integrity-murmur-re)。
 */
(function () {
  if (window.__errProbe) return;
  window.__errProbe = 1;
  var F = window.fetch.bind(window);          // 先抓原生 fetch,免得之後被別人換掉
  var sent = 0, busy = 0;

  function report(kind, msg, extra) {
    if (busy || sent > 40) return;            // 防遞迴 + 防洗版
    busy = 1; sent++;
    try {
      F('/__err__', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kind: kind, msg: String(msg).slice(0, 600),
                               extra: extra ? String(extra).slice(0, 1500) : '',
                               t: Date.now() })
      }).catch(function () {}).then(function () { busy = 0; });
    } catch (e) { busy = 0; }
  }

  window.addEventListener('error', function (ev) {
    report('error',
           (ev && ev.message) || 'error',
           ev && ev.error && ev.error.stack ? ev.error.stack
             : (ev && ev.filename ? ev.filename + ':' + ev.lineno + ':' + ev.colno : ''));
  }, true);

  window.addEventListener('unhandledrejection', function (ev) {
    var r = ev && ev.reason;
    report('reject', (r && r.message) || r, r && r.stack);
  });

  report('alive', 'err_probe installed');
})();
