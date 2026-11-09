# 幸運金幣2 — JILI 573／需求平台標籤 1837

2026-11-06 在 Joyfun CMS 以「幸运金币2」精確查詢，唯一結果為 `111000573`；新 LoginGame 回傳 `/rc2/?gameID=573`。證據見 mapping.json。平台標籤 1837 來自本次需求，不能把其他同名 ID 714 視為本款。

所有程式、素材與擷取都在本目錄。原始 codec 為本款 `rc2/assets/main/index.ade01.js` 的 `rcProto2`，不是 545 或 696 的盤面 schema。分析工具只共用第三方 protobufjs runtime，不載入其他遊戲 schema。

## 擷取

1. 關 VPN，確認 Taiwan 出口，執行 `.venv/bin/python -B games/573/login_capture.py`，取得新的一次性 URL。
2. 執行 `.venv/bin/python -B -u games/573/capture_server.py`。新登入建立獨立 webcap/session，不恢復其他登入的 key。
3. 連 Brazil／São Paulo 並確認出口，再執行 `.venv/bin/python -B games/573/open_capture.py`。
4. 操作人員轉局。每筆成功 SPIN 即時解密、驗章，經原始 rcProto2 codec 與完整 payload byte round-trip，寫入 session/math 及 math/單號.json。不要開 DevTools。
5. `.venv/bin/python -B games/573/finish_capture.py` 只重驗完整行、補轉與彙整，不是第一次產生 math 的必要步驟。

本機服務只聽 127.0.0.1:8573，不改 hosts；Chrome 保留憑證驗證。只關本 session 記錄的 server.pid／chrome.pid，不中斷其他遊戲。素材首次載入會逐項從原 CDN 補齊，可能在 99% 停留，應先查 capture.log。

初次執行的 collector 已內建即時輸出；watch_math.py 補上原子不覆寫發布及重驗，無須中斷視窗。後續啟動已直接使用相同的專用 exporter。

## 帳號與隱私

本次沿用本專案已保留的擷取帳號 tryplayer003idr／IDR。登入工具讀既有 private config 的憑證，不修改共用 config.json；每款的新登入 URL、GRV、key、封包與 profile 各自保存在其 session。初始化實包 f1 已觀察到 IDR 幣別，不能混算幣別或 RTP。原始資料與憑證均排除版本控制。

## 驗證現況

187 局成功 SPIN 已通過簽章、原始 rcProto2、完整請求／回應 byte round-trip。涵蓋一般 109 局、extra bet 76 局、50 倍內購 1 局、100 倍內購 1 局。來源與限制見 coverage.json。

## 本地 replay

在專案根目錄執行：

```sh
.venv/bin/python -B replay_573.py                 # 預設 math，每局前檢查變更
.venv/bin/python -B replay_573.py --bonus-first   # extra bet 與內購先播 Bonus
.venv/bin/python -B replay_573.py --source wire   # 固定原始結果
.venv/bin/python -B replay_573.py --no-browser    # 僅起本機 server
.venv/bin/python -B replay_573.py --rounds 2489894627000010573
```

預設本機 port 8574，與 capture 8573 分開。所有遊戲請求映到 127.0.0.1，server 不讀 live config、登入 URL 或 session key，也不向上游補資源；不需 VPN、sudo 或改 hosts。Chrome 使用獨立 profile，保留瀏覽器憑證驗證，不使用略過 TLS 檢查的旗標。周邊 VIP／排名等服務是明確的本地 stub。

請將基本注設成 **3,000 IDR**：一般／extra bet／兩種內購各有獨立樣本池。內購兩種實扣分別 150,000、300,000。`--bonus-first` 不會強行把一般局變成 Bonus；它將已有的 Bonus 移到各自池首。只指定某個內購單號時，其他下注／模式沒有樣本會回錯誤。不可用未擷取下注推導新結果。

math 模式每筆 SPIN 前檢查檔案變化，從 `math_adapter.py` 重新編碼。修改具名盤面、贏分、餘額、基本注與 purchase 會生效；首次新增的非零欄位按原 codec 的欄位順序編碼。`data.TotalWin` 與傳輸容器 `totalWin` 原本相同，單改其中一份會同步另一份；若兩份被改成互相矛盾的值則拒絕回放。JSON 損壞或不支援的請求不偷偷沿用舊結果。

extra bet 原始請求 f26 的有無與內容來自 replay_samples.json 的對應單號。真站回應沒有完整回填 f26，不能只依回應 echo 分池。已觀察的 UI context f25 零值可忽略，其餘未知欄位保留並參與匹配。內購 selector=0 的明確零／省略零可匹配；不同模式、旗標或未知值不混池。

這是「已擷取結果」回放，不是機率引擎：保留原局結果與 postMoney，餘額輪詢回同一餘額；只在循環／跨池需要時重寫單號使其單調，並保留 573 尾碼，不按目前餘額重算輸贏。修改 math 不改原始 wire 快照。停止時關閉專用視窗或啟動終端按 Ctrl-C；不會關其他 Chrome。

## replay 驗證

```sh
.venv/bin/python -B games/573/verify_replay.py --source wire
.venv/bin/python -B games/573/verify_replay.py --source math
.venv/bin/python -B games/573/verify_reload.py
```

wire 與 math 各驗 187 局及四池 wraparound，共各 191 次加密 SPIN，驗證 Ed25519、AES-GCM、完整 payload（只容許單號重寫）、餘額、兩個客戶端隔離與未知模式拒絕。熱載入測試只改暫存副本，驗證盤面／雙份總贏分／餘額／下注的變動、損壞 JSON 拒絕與恢復。報告見 replay_validation_wire.json、replay_validation_math.json、replay_math_reload_validation.json。

replay_sources.json 記錄兩次獨立 session 的簽章重驗與原包 SHA256；replay_samples.json 只含應用層 action／payload，不含原傳輸 token、公開金鑰、session key、GRV 或真站 URL。replay_asset_sources.json 記錄實際缺漏的共用語系／選單圖原 CDN 雜湊，不以假素材回 200。

2026-11-09 操作人員已確認進場、可轉局及 extra bet Bonus 演出與最後結算正常。兩種內購完整 payload 已通過加密回放測試，內購畫面未分別確認。紀錄見 replay_browser_validation.json；不能以後端加密測試通過代替畫面驗收。

## 貼圖格式與非 ASTC 裝置

2026-11-09 已補齊並驗證 2,444 個原始版本化貼圖：WebP 325、ASTC 325、PNG 1,768、JPG 26。涵蓋 gameLite 與當前共用 bundle；完整本地掃描 0 錯誤，全部經 replay HTTP 回 200，Content-Type／SHA256 一致。已確認排除 ASTC 的 WebP 偏好只修改回應、原始引擎未改；實體 Windows 畫面尚未驗收。

素材補齊工具會依原始版本化 bundle config、import metadata 的 `fmt` 與 native version，下載實際宣告的 ASTC／WebP／PNG／JPG。範圍包含 rc2 的 main、game、gameLite，以及已載入的共用 bundle。不能把 ASTC 改副檔名當 WebP，也不以轉檔或透明圖取代缺少的原始素材。

```sh
.venv/bin/python -B games/573/complete_texture_variants.py --download
.venv/bin/python -B games/573/complete_texture_variants.py  # 僅本地完整性／格式／雜湊檢查
.venv/bin/python -B games/573/verify_texture_variants.py    # 所有變體經本機 HTTP 驗證
```

`texture_variants.json` 列出每個檔案、來源 config/import、格式、SHA256 和失敗清單；只有失敗數為零才標記 complete。`texture_validation.json` 是本機 HTTP 全量驗證結果。原始圖檔以檔頭檢查實際格式，下載過程不覆蓋不同內容的既有檔案。補材階段可連原 CDN，replay 本身仍禁止上游 fallback。

一般啟動維持 Cocos 自動選格式。關閉既有專用 replay 後，可模擬不支援 ASTC 的路徑：

```sh
.venv/bin/python -B replay_573.py --bonus-first --texture-format webp
```

此選項只在本地 HTTP 回應中將 Cocos 貼圖偏好設為 WebP／一般圖片、排除 ASTC／PVR／PKM；磁碟上的原始引擎與素材不改動。也可選 `--texture-format png` 優先測 PNG／JPG。`/__replay_status` 的 texture_policy_applied 與 texture_requests 可核對實際路徑。這是 fallback 路徑測試，不代表已在實體 Windows 裝置完成畫面驗收。

## WebP 全專案批次驗證（2026-11-09）

現行版本已辨識的 WebP 325/325 檔通過格式、尺寸及 loopback HTTP 驗證。含保留歷史版本的完整目標為 325/325。詳見本款 texture_validation.json 與根目錄 artifacts/texture_webp_batch_20261109.json。 未覆蓋的 import packs／binary packs 分別為 210/3，仍列在報告；尚未做 Windows 實機完整畫面驗收。

## Git checkout / local-only files

Login config, authenticated captures, current_session pointers, profiles, logs and ZIPs are local-only. Original archive members and archive_manifest.json are tracked; replay reconstructs its ZIP load bundles locally. Install root npm dependencies and `npm ci --prefix games/545/runtime` before original-codec checks. See the root README for setup.
