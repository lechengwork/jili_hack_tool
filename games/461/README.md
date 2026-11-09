# 海盜女王2 — JILI 461／使用者平台標籤 1838

對照證據見 mapping.json：新 LoginGame `111000461` 回傳 `/pirate2/index.html?gameID=461`；原始 game bundle 為 `0461-Pirate2`、codec 為 `pirate2Proto`。574 及 CMS 同名 1330010461 未通過本次登入核對，不使用。

## 新登入擷取

1. 關 VPN 並確認 TW 出口。
2. `.venv/bin/python -B games/461/login_capture.py` 取得新的一次性 URL。
3. `.venv/bin/python -B -u games/461/capture_server.py` 建立獨立 session，監聽 127.0.0.1:8461。
4. 開 Brazil／São Paulo VPN，確認連線與 BR 出口。
5. `.venv/bin/python -B games/461/open_capture.py` 開專用 Chrome profile。保留憑證驗證；不要開 DevTools。
6. 由操作人員執行轉局及模式切換。capture 不自動下注或購買功能。
7. `.venv/bin/python -B games/461/finish_capture.py` 重驗、補轉及更新該 session 的 validation.json。

不得混用其他款或舊登入的 URL、隨機值、key。沿用已保留的 tryplayer003idr 擷取帳號；來源幣別預期 IDR，仍須以初始化實包確認，不混算幣別。服務不修改 hosts，只用此 Chrome 的 host resolver；不可停止其他遊戲的 collector。

## 即時 math

每筆 type=0、ret=0、簽章成功的回應經本款原始 codec 交叉驗證及完整應用層 payload byte round-trip 後，即時寫入 session/math 及 math/<單號>.json。不需關遊戲或 finish。完整暫存寫入、fsync 後以 macOS RENAME_EXCL 原子更名，不覆蓋修改檔；衝突原始結果保留於 session/math 並記錄 math_conflicts.jsonl。

失敗／未驗章／非 SPIN 不當成功樣本。schema、decode、round-trip 失敗保留原始 exchanges 並記錄 decode_errors.jsonl 或 math_errors.jsonl。

## 覆蓋與限制

coverage.json 分別追蹤一般、extra bet、自然 Bonus／免費局及內購。初始化已驗章並確認 IDR；首局 2490005372000000461 已即時發布及通過完整 byte round-trip。實包明細與當次驗證見 live_validation.json，覆蓋摘要見 coverage.json。adapter_validation.json 另為合成 fixture 驗證，不計入實包數。原廠 codec 顯示 FreeRemainRound／FreeNowRound／FreeTotalRound；模式可用性、觸發條件、額外下注扣款倍率、內購 selector 與價格都必須由本款 UI、原始 codec 與實包共同核對，不能套用 573。

本機鎖定時不能操作 VPN／開啟遊戲；解鎖後如 URL 已失效，必須重新走關 VPN → 新 URL → São Paulo → 開視窗流程。

461 已停用共用 shared 素材回退，動態版本表與 bundle 由本款 static 直接從原 CDN 補齊，避免讀到其他遊戲留下的舊版本。

## 本次已核對模式（2026-11-06）

- 一般：已取得實包，逐局 math 即時發布；實際數量讀 coverage.json。
- 特色購買：單號 2490007724000000461，底注 IDR 1,000，UI 價格／請求金額／連續餘額實扣皆為 39,500（本選項 39.5 倍）。請求 f23 明確傳 f1=0、f2=0、f3=39500；回應 echo f23 僅保留 f3，原始表示皆保留，不將 573 的 selector 語意套入。
- 購買後免費局：同筆回應完整包含 10 局及 remaining=0 結尾；TotalWin=93,300，FreeTotalWin=90,300；原始 codec 與完整應用層 byte round-trip 均通過。
- 額外下注：使用者確認本版介面沒有此入口，標為不適用；初始化 GameInfoData 原廠 codec 確認 ShowExtra=true、Mul=[1,1.5]，此設定不當作 UI 已開放或實扣倍率的證據。
- 自然觸發免費局：單號 2490024636000020461，原始請求不含購買 f23，回應含完整 10 次免費局與 remaining=0 結尾；TotalWin=134,400、FreeTotalWin=125,400，簽章、原始 codec 與完整 payload byte round-trip 通過，共享 math 與 session 原始 math 相同。
- 罕見旗標、重觸發及其他購買選項：不宣稱窮盡覆蓋。

原始輸入與回應 echo 的欄位存在性可能不同；math 的 spinReq 目前保留回應 echo 原始整數陣列，原始請求逐局記在 live_validation.json（明文 SPIN 應用層，無登入 token 或 key），不得用空的回應 context 推測原始下注模式。

## 本次收尾

Session `20261106-131323` 已關閉 collector；共 385 筆成功 SPIN，全數完成簽章、原始 codec 及完整 payload byte round-trip 重驗，385 份共享 math 與 session math 一致，0 錯誤、0 衝突、沒有殘缺尾行。來源 IDR。原始下注請求另有 385 筆完整 byte round-trip 驗證，見 verified_input_examples.json；最終摘要見 final_capture_summary.json。沒有另建 ZIP 或 dist 專案。

## 本機 replay（2026-11-09 完成）

從同一專案根目錄執行：

```sh
.venv/bin/python -B replay_461.py
# 優先播自然免費局／特色購買免費局，方便驗收：
.venv/bin/python -B replay_461.py --bonus-first
# 直接使用已驗證的原始應用層封包：
.venv/bin/python -B replay_461.py --source wire --bonus-first
# 只播指定單號（自然／購買分開匹配下注）：
.venv/bin/python -B replay_461.py --rounds 2490024636000020461,2490007724000000461
```

預設監聽 127.0.0.1:8462，開獨立 Chrome profile；`--port` 可換埠。Chrome 的所有 host 僅映射到本機，API、SSO、靜態素材與加密協定均在本機，不登入、不讀 capture key、不需要 VPN，也不修改系統 hosts。沒有素材上游 fallback，不會向真站下注。SSO 使用合成的 local-replay-461。不要開 DevTools。關閉專用 Chrome 或在啟動終端按 Ctrl+C 結束這個 replay；不影響其他遊戲。

### 下注與模式

一般樣本底注為 IDR 3,000，特色購買樣本底注為 IDR 1,000、價格 39,500。兩種輸入各有獨立循環池，不做跨下注縮放或模式替換。UI 顯示原局餘額與原局結果，並非連續計算的模擬錢包。自然免費局及特色購買回應都保留完整觸發局與 10 次免費局；重複播放時只調整回傳單號以保持遞增，其餘 payload 原樣。沒有擷取的下注／未知模式會回明確錯誤，不拿其他模式頂替。

`--bonus-first` 只選自然免費局與購買免費局兩筆，仍按上述下注分池。未指定時 math 模式讀取全部 385 局。

### math 修改即時重讀

預設 source=math，每次 SPIN 前檢查 numeric math JSON 的新增、修改或刪除，經本款 adapter 驗證、重新編碼後加入對應下注／購買池；無須重啟。

- `--math-dir /absolute/path`：讀另一個 math 目錄，適合測試修改；不會覆蓋原始擷取資料。
- `--no-watch-math`：固定啟動時的 math 快照。
- `--rounds`：只讀指定單號；不會把其他新增單號混入。
- `--no-browser`：只開本機 server。

修改 `data` 命名欄位會重新編碼；`_wire` 保留未改欄位、存在性與未知欄位。根層 spinReq 是 461 原始回應 echo 的整數陣列，需要修改輸入時先用 request_adapter.request_to_math 解碼，修改後以 math_to_request 編碼成整數陣列放回。replay 依該 echo 匹配下注；實際原始請求仍可查 verified_input_examples.json。其他未確認的 context 值不會當成既有一般模式接受。

JSON 不合法或 schema 不符會回錯誤並記錄原因；修正後下一次 SPIN 可恢復。新增檔名須為合法數字單號，與 roundIndexV2 相同，且結尾為 461。

### 驗證

- `replay_validation_math.json`／`replay_validation_wire.json`：兩種來源各 385 筆 payload，387 次加密 SPIN（含各池循環），簽章、AES-GCM、原內容保留、餘額輪詢、多 client 隔離、未知下注／模式拒絕均通過；自然與購買免費局皆涵蓋。
- `replay_math_reload_validation.json`：在暫存檔驗證命名欄位修改、新增局、錯誤 JSON 拒絕與修復、未知 context 拒絕，沒有修改原始 math。
- `replay_browser_validation.json`：使用者確認自然免費局能正常進入並完整播完；購買畫面未另外逐步驗收，但加密後端與完整購買結果 payload 已通過。
- `/zh-CN/landingpage` 是未提供的離線活動附頁；自然免費局播放已確認不受影響。

重跑後端驗證：

```sh
.venv/bin/python -B games/461/verify_replay.py --source math
.venv/bin/python -B games/461/verify_replay.py --source wire
.venv/bin/python -B games/461/verify_math_reload.py
```

replay_samples.json 只含已驗章的應用層請求／回應；建置時解密讀取私有 session，但回放時完全不需要私有 session、token、GRV 或 key。runtime profile、log、PID 均在本款 replay/，已排除版本控制。

## WebP 替代貼圖補齊（2026-11-09）

先前的 Mac 擷取只保存 63 個 ASTC，沒有 WebP；Mac 上回放成功不代表其他 GPU 的貼圖已齊。現在依本款及共用 bundle 的原始 Cocos metadata，加上已擷取 ASTC 對應檔，從原 CDN 補齊同版本 WebP 共 140 個。每檔檢查 RIFF/WEBP 容器、尺寸與 metadata／ASTC 對應，並透過實際 461 replay HTTP handler 確認 HTTP 200、image/webp MIME 及完整內容相同；沒有使用改副檔名或透明佔位圖。

驗證報告：texture_validation.json，140/140 格式與尺寸有效，140/140 本機 HTTP 通過。報告仍列出 58 個未涵蓋 import packs；這是可讀 metadata 與已擷取 ASTC 的替代格式驗證，不是 Windows 實機完整畫面驗證。Windows／其他 GPU 的最終載入畫面仍須實機確認。

準備新素材時執行：

```sh
python3 -B routex/texture_variants.py games/461/static --report games/461/texture_validation.json
# 需要補原站檔案時：
python3 -B routex/texture_variants.py games/461/static --fetch --report games/461/texture_validation.json
# replay 已運行時，同時驗證本機 HTTP：
python3 -B routex/texture_variants.py games/461/static --base-url http://127.0.0.1:8462 --report games/461/texture_validation.json
```

離線 replay 直接讀取已補齊的本地檔案；更新素材後不需啟用真站 fallback。

## WebP 全專案批次驗證（2026-11-09）

現行版本已辨識的 WebP 140/140 檔通過格式、尺寸及 loopback HTTP 驗證。含保留歷史版本的完整目標為 140/140。詳見本款 texture_validation.json 與根目錄 artifacts/texture_webp_batch_20261109.json。 未覆蓋的 import packs／binary packs 分別為 58/0，仍列在報告；尚未做 Windows 實機完整畫面驗收。

## Git checkout / local-only files

Login config, authenticated captures, current_session pointers, profiles, logs and ZIPs are local-only. Original archive members and archive_manifest.json are tracked; replay reconstructs its ZIP load bundles locally. Install root npm dependencies and `npm ci --prefix games/545/runtime` before original-codec checks. See the root README for setup.
