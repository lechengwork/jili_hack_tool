// service worker：把攔截記錄 POST 到本地 listener
const ENDPOINT = "http://127.0.0.1:8099/hooklog";
chrome.runtime.onMessage.addListener(function (rec) {
  try {
    fetch(ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" },
                      body: JSON.stringify(rec) }).catch(function () {});
  } catch (e) {}
});
