# JILI 124 = 7up7down (7上7下) — 本地離線回放包

自己本地跑的離線回放。**全本機、免 VPN、免 sudo、免改 /etc/hosts、免任何 crypto**
（7up7down 的 WS 是明文 protobuf，回放只要照錄音帶重送即可）。

## 跑
```bash
./run_124.sh          # 起 server + 開 Chrome(自動把所有 jili host 指到本機)
# 玩:進遊戲後下注,會顯示【擷取那場的結果】(依 cmd 配對回放;下注 cmd22 的結果會循環)
./stop.sh             # 收工
```
需求:macOS + Google Chrome + python3(內建即可) + openssl(mac 內建,首次自動產自簽憑證)。

## 原理
`run_124.sh` 用 `chrome --host-resolver-rules="MAP * 127.0.0.1:8443"` 把所有網域指到本機
`ws_replay_server.py`(保留 jili hostname → 過 Jscrambler domain-lock),`--ignore-certificate-errors`
吃自簽憑證。server 一個 port 靠 Host+path 路由:
- 靜態站 → `static/`(擷取的完整 mirror,96 檔)
- `POST /sso-login.api` → `mock/sso.json`(錄到的真回應;遊戲讀它的 token 組 WS 路徑)
- `/webservice/event/*` → 204;`/rankingservice/*` → `mock/ranking.json`;`/subagentservice/*` → 200
- WebSocket `/sudm/ws/*` → 依 `ws_session.jsonl` 回放:連線先送歡迎幀,之後 client 送 cmd X
  就回錄到的同 cmd 回應(心跳 cmd50 即時回;遊戲 cmd22 取完循環);fire-and-forget 的 cmd 略過。

## 內容
- `ws_replay_server.py` 回放 server  ·  `run_124.sh` / `stop.sh` 啟停
- `ws_session.jsonl` 錄音帶(擷取的真實對局 WS frames)  ·  `mock/` sso/ranking 回應
- `static/` 遊戲靜態 mirror  ·  `ws_124.proto` / `WS_PROTOCOL.md` 協定說明(參考)

## 換一場回放
把新的擷取 `traffic.jsonl`(含 ws_msg 行)複製成 `ws_session.jsonl` 即可;或 `SESSION=<檔> ./run_124.sh`。

## 限制
- 結果=**錄到的固定歷史**(伺服器權威 RNG,離線無法產新結果;下注 cmd22 循環重播那 11 局)。
- 餘額/局號顯示為錄音當時的值,不隨你在回放裡的下注即時結算。
- 純本機、無外連;Chrome 自身 telemetry / google 會 404(無害)。★別開 DevTools(Jscrambler)★。
