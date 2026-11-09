# 518 — 馬戲團小丑 4096 / Circus Joker 4096

## 機率團隊交付包

專案根目錄的 `jili_518_math_test_20261102.zip` 是獨立交付包，解壓內容同 `dist518_math/`。
操作手冊為根目錄 `README_ForMath_518.md`，機率規格為 `math/INTERFACE.md`、`math_518.proto`。
包含 151 筆完整數字樣本、雙向 adapter、原始測試向量、原始／修改後 math 的一鍵回放、共用素材與 WebP 版本。

在專案根目錄快速驗證／回放：

```bash
.venv/bin/python -B games/518/math_adapter.py --selftest
.venv/bin/python -B replay_518.py --source math
```

零相依 Python adapter 的 151 筆完整信封 byte round-trip 與獨立編譯 protobuf codec 驗證皆通過。
修改 math 的 HTTP 整合測試亦通過（1.05 → 2.10）；Windows 啟動程式已準備，尚未在 Windows 主機實測。
重建交付包：`.venv/bin/python -B build_518_math_package.py`。打包器使用明確檔案清單，排除真站登入 token、擷取私鑰與 AES session key；只包含本地 mock 專用金鑰。

## 已確認（2026-11-02）

- LoginGame 完整 `game_id` 是 `111000518`；4096 是名稱中的數字，不能當成擷取目錄編號。
- 登入回傳的入口路徑是 `/cj/`，HTML title 是 `Circus Joker 4096`。
- 初次探測使用現有設定的測試帳號 `tryplayer002usd`，不是截圖中的 `streamerusd011`。
- 目前擷取工作階段已改用截圖帳號 `streamerusd011`。
- 真實通道是 HTTP/2 `/cj/req`。回應使用與 696 相同的 Ed25519 簽章公鑰，且已用實際工作階段金鑰成功解密；並非未加密的協定。
- 2026-11-02 已擷取 151 筆成功轉局回應（type=0、ret=0），全部解密且驗章通過。首次成功握手的回應為 347 bytes、payload 243 bytes。
- 起初保存 123 個靜態資產（約 32 MB），後續由 518 專用 fallback 持續補齊音效等資源，全部放在本目錄的 `static/`。
- 遊戲主 bundle 採字串表混淆，已還原為 `analysis/game.decoded.js`；共用 astarte2 bundle 仍有 Jscrambler 防護。
- 已從前端 decoder 抽出 `cj_518.proto`，五個 message、31 個欄位已逐欄比對型別、欄號及 repeated。再以原始前端 codec 對 151 筆實局 payload decode → encode，151/151 byte 完全相同。這份只描述內層 SpinAck，不包含外層 service／餘額／單號／下注信封。

## 2026-11-02 樣本結果

- 151 筆轉局：基礎下注 0.3 共 150 筆，0.1 共 1 筆。
- 31 筆 TotalWin > 0，31 筆包含多個連消階段；單一 RoundInfo 最多 5 個階段。
- 1 筆帶免費遊戲相關欄位。這是樣本覆蓋情況，不代表所有免費遊戲規則已確認。
- BuyType、AckType 在這批樣本均為 0，不推定 enum 其他值的意義。
- 1 筆下注信封帶非空 f23，暫保留為 `spinReq.special.f23_hex`，語意尚未命名。
- 外層 f1 是 SpinAck、f2 在本批恆空、f3 與內層 TotalWin 全部相符、f6 是餘額、f20 是單號（以字串保存）、f23 是下注資訊。
- `export/spins_named/<單號>.json` 保留 `data/service/postMoney/roundIndexV2/spinReq` 五格；資料層欄名沿用原始前端。未知特殊請求尚未標準化，這是工程可讀樣本，非已定案的機率介面。

## 尚待完成

- 特殊請求 f23 語意及更多玩法情境。
- 正式機率介面與新結果產生器尚未實作；不可套用 696 的遊戲欄位映射。

## 本地 mocker（2026-11-02 已實際進場、連轉確認）

518 與 696 共用 `routex/fg5.py` 的 X25519／AES-GCM／Ed25519 底層及 mock 金鑰。
遊戲資料改接 518 的 `/cj/req` 和 `cjProto.SpinAck`。不需要再次破解加密，也不能直接拿 696 的盤面或初始化資料充作 518 回應。

在專案根目錄開兩個終端：

```bash
.venv/bin/python -B -u games/518/mock_server.py
```

```bash
.venv/bin/python -B -u games/518/open_mock.py
```

- 本地 server 使用 `127.0.0.1:8519`，僅專用 Chrome 的所有主機映射至此；不用 VPN、sudo 或修改系統 hosts。
- 來源為 `current_session.txt` 指向那輪的 `export/exchanges_ordered.jsonl` 和 `exchanges.jsonl`；可用 `REPLAY_SESSION=<資料夾>` 指定其他完整擷取輪次。
- `mock_sso.json` 為擷取的 SSO 設定（登入 token 已換成本地假 token）。`auxiliary_responses.json` 是已追蹤的周邊 API replay fixture，僅保留信箱、收藏、VIP、排行榜的回應內容與 Content-Type；不含瀏覽器更新流量及原始傳輸 headers。這些檔案供本機 replay 使用，不代表真站登入資訊。
- 使用原有 compile hook，實際前端回報 `compile d=8`，並成功完成本地 SSO、握手及初始化。僅沿用 crypto hook，不注入 696 專用側欄 UI 改動。
- 已確認請求 f1 就是要求的 message type，並非流水號。518 adapter 依 type 和 action 對應擷取回應，避免併發初始化時拿錯回應。
- 轉局依下注金額回放：0.3 有 150 筆、0.1 有 1 筆；其他下注尚無樣本。循環回放時只調整單號使其遞增，SpinAck 內容保持原樣；餘額輪詢回傳剛播出樣本的 postMoney。
- 可選推薦／活動等未擷取的 protobuf 服務目前是空訊息 stub，並非完整業務實作。這套是封包回放，尚未接新機率結果產生器。
- `MOCK_VERBOSE=1` 可開啟詳細靜態資源路由記錄；一般只需看 `[518 mock] spin=...` 和 `[fg5]`。

驗證紀錄：獨立 HTTP 客戶端通過本地簽章、X25519／AES-GCM 解密、連續轉局與餘額比對；151 次回放選樣（含循環邊界）均維持內層 payload、不重複倒退單號，且每次餘額相符。使用者已確認實際前端進場、連轉正常；server 同時記錄到 3 筆連續 spin 及後續餘額輪詢。

載入修正包括：將本地連線佇列由預設 5 調至 128，避免所有 mock 主機共用 listener 時出現腳本連線重置；補齊 smallicon 和共用 astarte2 素材；周邊 protobuf API 不再套用通用 JSON 回應。

## 本次擷取

第一輪 `IncludeSensitive` 只記到本文長度，沒有 `SSL_SOCKET_BYTES_*` 的 `bytes`。
其 netlog 與 TLS key log 已保留在 `raw_sessions/20261102_initial_probe/`。
第二輪使用 `Everything`，記錄在 `netlog.json` 和 `sslkeys.log`，已結束探測。
正式擷取使用 `capture_server.py`，改接 `/cj/req`，讀取 wasm shared key／getRandomValues 候選，並驗證每筆回應簽章。此 adapter 沒有修改 696 的 server、shim 或資料。
登入網址及原始記錄可能包含短效憑證，勿貼到文件或提交版本庫。

`current_session.txt` 指向當輪的 `webcap/<時間>/`，其中：

- `exchanges.jsonl`：原始請求／回應本文。
- `grv.jsonl`、`key.json`：本輪解密材料。
- `exchanges_ordered.jsonl`：即時解密紀錄，依回應完成順序寫入；需按 `idx` 排序。
- `export/exchanges_ordered.jsonl`：由收尾腳本逐筆重新驗章／解密、按 request seq 排序的正式快照。
- `export/summary.json`：筆數、type 分布、spin request 數及驗章結果。
- `export/spins_named/`：逐筆可讀 JSON 與 `all.jsonl`。
- `export/spin_wire_vectors.jsonl`：每筆原始遊戲 payload 及完整回應 payload，供回歸／回放開發。
- `export/spin_summary.json`：中獎／連消／免費特徵等樣本覆蓋，以及原 codec 的 byte round-trip 結果。

當輪轉完後，關閉專用 Chrome，執行：

```bash
.venv/bin/python -B games/518/finish_capture.py
```

也可以在擷取中執行以匯出當下的快照；`spin_requests: 0` 表示尚未收到轉局請求。有轉局時會自動呼叫 `export_spins.cjs`，以原始前端 codec 解析並逐筆重新編碼驗證，全部通過才輸出可讀樣本。

目前 Surfshark 的實際 GUI 連線無法由舊 `VPN_UUID` 可靠控制。
使用既有 WireGuard 協定及 Brazil / Sao Paulo 節點；不要套用腳本輸出的國家假設。
已實測巴西出口呼叫 LoginGame 會回 403，需先斷 VPN 取新網址，再連巴西開遊戲。

重新執行時，在專案根目錄操作。先於台灣出口取新的單次入口：

```bash
.venv/bin/python -B jili_login.py 518 --player-id streamerusd011 --json > /tmp/jili518_login.json
chmod 600 /tmp/jili518_login.json
```

再連巴西 VPN。在兩個終端分別執行（server 已開著時勿重開）：

```bash
.venv/bin/python -B -u games/518/capture_server.py
```

```bash
.venv/bin/python -B -u games/518/open_capture.py
```

不用 sudo 或修改系統 hosts。僅專用 Chrome 的 document host 導向本機 8518，其餘 API 走真測試站。每次 server 啟動建立獨立 session 目錄；不要把不同登入的工作階段混入同一個 server session。
使用獨立 Chrome profile，僅被動錄製。轉局由操作人員自行操作；不要開 DevTools。關閉專用 Chrome 後，以 Ctrl+C 停止本次擷取 server。
`parse_netlog.py` 的判定文字是為 696 `/fg5/req` 寫的，不能用其「fg5 次數為 0」判定 518 失敗。

## WebP 全專案批次驗證（2026-11-09）

現行版本已辨識的 WebP 137/137 檔通過格式、尺寸及 loopback HTTP 驗證。含保留歷史版本的完整目標為 138/141。詳見本款 texture_validation.json 與根目錄 artifacts/texture_webp_batch_20261109.json。 歷史 config 引用的 3 個舊檔已無原站來源，保留為明確缺口；不影響本款現行 versions.json 的驗證結果。 未覆蓋的 import packs／binary packs 分別為 2/0，仍列在報告；尚未做 Windows 實機完整畫面驗收。
