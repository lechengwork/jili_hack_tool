// isolated-world：收 main-world 的訊息，轉給 background（background 才能無視 CSP 送 localhost）
window.addEventListener("message", function (e) {
  if (e.source === window && e.data && e.data.__jiliHook) {
    try { chrome.runtime.sendMessage(e.data.rec); } catch (err) {}
  }
});
