// ws_capture_shim.js — 【124 (7up7down) CAPTURE 模式】純網頁側錄【真伺服器】WebSocket 封包。
//
// 124 的遊戲後端走【明文 protobuf over WebSocket】(wss://uat-fish.../sudm/ws/…，見 WS_PROTOCOL.md)，
// 完全沒有加密 —— 所以側錄比 696 route-X 簡單非常多:不用撈 key、不用碰 WASM、不用解密。
//   ● 唯一 hook = WebSocket:攔每個 binary frame(SEND=下注/開骰, RECV=開獎含 extra 倍率)。
//   ● 每筆 POST 到本地 /__wscap(同源 = document host = 被 hosts 導到本機 server 的 jili doc host)。
//   ● 診斷用 Image().src = '/__wsreport__/…'(和 696 shim 同一招,server 端會印出來)。
//   ● 載體 = prepend 進 sudm/src/system.bundle.543e6.js(index.html 唯一直接載的 script，SystemJS，
//     最早、WebSocket 尚未建立)。★不加新 <script>、不改既有函式源碼★ → 過 Jscrambler self-defending。
//
// 側錄格式(每筆一行 JSON，server append 進 games/124/webcap_ws.jsonl)刻意沿用現有 session 的形狀:
//   {"kind":"ws_msg","seq":N,"ts":epoch_ms,"dir":"SEND"|"RECV","hex":"…","url":"wss://…"}
// → ws_math_view.py 能直接解、ws_replay_server.py 能直接回放，三邊同一個契約。
(function(){
  var CAP = '/__wscap', W = (typeof self !== 'undefined') ? self : window;
  if (W.__ws124_installed__) { return; }         // 只裝一次(system.bundle 可能被 eval 兩次)
  W.__ws124_installed__ = true;

  var ofetch = (W && W.fetch) ? W.fetch.bind(W) : null;
  var seq = 0, sockN = 0, beaconFail = 0;

  function report(m){ try{ (new Image()).src = '/__wsreport__/' + encodeURIComponent(m); }catch(e){} }
  function toHex(u){ var s=''; for(var i=0;i<u.length;i++) s += ('0'+u[i].toString(16)).slice(-2); return s; }

  // ★不要用 keepalive★(696 教訓):它有 64KiB 在途配額，autoplay 連轉會滿→靜默丟資料。
  // 一律補 .catch 回報，寧可吵也不要靜默掉資料。
  function beacon(dir, hex, url){
    if(!hex) return;
    var rec = { kind:'ws_msg', seq:(++seq), ts:Date.now(), dir:dir, hex:hex, url:url||'' };
    try{
      if(!ofetch){ report('NO-FETCH'); return; }
      ofetch(CAP, { method:'POST', body:JSON.stringify(rec),
                    headers:{'Content-Type':'application/json'} })
        .catch(function(e){ if(++beaconFail <= 20) report('BEACON-FAIL#'+beaconFail+' '+e); });
    }catch(e){ report('BEACON-THROW '+e); }
  }

  // data → hex(非同步:Blob 要 await;string 跳過，124 遊戲 frame 都是 binary)
  function dump(dir, data, url){
    try{
      if(data == null) return;
      if(typeof data === 'string') return;                       // 控制字串(非遊戲 frame)，略過
      if(data instanceof ArrayBuffer){ beacon(dir, toHex(new Uint8Array(data)), url); return; }
      if(ArrayBuffer.isView(data)){                              // TypedArray / DataView
        beacon(dir, toHex(new Uint8Array(data.buffer, data.byteOffset, data.byteLength)), url); return;
      }
      if(typeof Blob !== 'undefined' && data instanceof Blob){   // onmessage 預設給 Blob
        data.arrayBuffer().then(function(buf){ beacon(dir, toHex(new Uint8Array(buf)), url); })
                          .catch(function(e){ report('BLOB-ERR '+e); });
        return;
      }
    }catch(e){ report('DUMP-THROW '+e); }
  }

  var OWS = W.WebSocket;
  if(!OWS){ report('NO-WEBSOCKET'); return; }

  function WS(url, protos){
    var ws = (protos === undefined) ? new OWS(url) : new OWS(url, protos);
    var myUrl = ''; try{ myUrl = ws.url || (''+url); }catch(e){ myUrl = ''+url; }
    var id = (++sockN);
    report('ws#'+id+' open '+myUrl);

    // SEND: 包住 send()
    try{
      var osend = ws.send;
      ws.send = function(d){ try{ dump('SEND', d, myUrl); }catch(e){} return osend.apply(ws, arguments); };
    }catch(e){ report('SEND-HOOK-ERR '+e); }

    // RECV: 用 capture 階段的 message 監聽器。addEventListener('message') 會收到【所有】
    // 進來的訊息，不論遊戲是用 ws.onmessage= 還是 ws.addEventListener 註冊(同一套事件分派)，
    // 所以這一條就夠，不需要再攔 onmessage setter。capture:true = 比遊戲的 handler 早收到。
    try{
      ws.addEventListener('message', function(ev){ try{ dump('RECV', ev.data, myUrl); }catch(e){} }, true);
    }catch(e){ report('RECV-HOOK-ERR '+e); }
    return ws;
  }
  try{
    WS.prototype = OWS.prototype;
    WS.CONNECTING = OWS.CONNECTING; WS.OPEN = OWS.OPEN;
    WS.CLOSING = OWS.CLOSING; WS.CLOSED = OWS.CLOSED;
    W.WebSocket = WS;
    report('ws-capture-shim installed (WebSocket hook; plaintext, no key needed)');
  }catch(e){ report('INSTALL-ERR '+e); }
})();
