# 幸运草金币 3x3 — JILI 545

本次需求標籤為1836；使用者確認以遊戲名稱為準。原站語系表545／650同名，但實際LoginGame只有545成功：`111000545 → /cc3x3/?gameID=545`，成功局號尾碼亦為545。650回HTTP400/code905。另一專案舊表的1836是chilli/5，本工作沒有修改該平台對照。證據見`mapping.json`。

## 專案內的遊戲資料夾

與696、518、807相同，本遊戲的正式工作目錄為`games/545/`；直接在同一專案內使用，不需要解壓ZIP或切換到另一份專案。

| 路徑（相對於本目錄） | 用途 |
|---|---|
| `math/INTERFACE.md` | 給機率團隊的入口、欄位說明與樣本限制 |
| `math/<單號>.json` | 給機率團隊的逐局輸入／結果 |
| `math_545.proto`、`math_schema.json` | 機率介面規格 |
| `math_adapter.py` | 機率JSON與遊戲線路格式雙向轉換 |
| `math_sources.json`、`coverage.json` | 樣本來源幣別與覆蓋情況 |
| `webcap/<session>/` | 原始擷取與解密資料，金鑰只留本機 |
| `static/`、`analysis/` | 本遊戲素材與原始codec分析 |
| `replay_samples.json`、`mock_server.py`、`replay_pool.py` | 本遊戲mock與replay資料／邏輯 |
| `*_validation*.json`、`verify_*.py` | 驗證紀錄與驗證程式 |

根目錄的`replay_545.py`是啟動入口，`routex/`沿用共用傳輸層。它們直接讀取本目錄，沒有另一份交付目錄。

## 真站擷取（Mac）

沿用RUNBOOK的順序，使用獨立port與session，不修改系統hosts：

1. 關VPN，在專案根目錄執行：
   ```sh
   .venv/bin/python jili_login.py 545 --account thb --json > games/545/login_session.local.json
   chmod 600 games/545/login_session.local.json
   .venv/bin/python games/545/refresh_assets.py
   .venv/bin/python -B -u games/545/capture_server.py
   ```
2. 開VPN至Brazil／São Paulo，確認連線完成，再在另一終端執行：
   ```sh
   .venv/bin/python -B games/545/open_capture.py --seconds 43200
   ```
3. 由操作人員進場、轉局或auto spin；不要開DevTools。server只被動擷取。每次重開新的登入頁，必須重取一次性URL並重開capture_server，避免混用session金鑰。
4. 每次成功且驗章通過的SPIN即時輸出`math/<單號>.json`與`webcap/<session>/math/`。原始請求／密文／GRV／key只在被忽略的本機webcap目錄。
5. 收尾（或對目前完整行取快照）：
   ```sh
   .venv/bin/python -B games/545/finish_capture.py --publish-replay
   .venv/bin/python -B games/545/build_report.py
   ```

目前這次持續擷取的舊程序由`watch_math.py`補即時math，不需中斷瀏覽器；之後新開capture_server已內建相同輸出，不需再開watcher。停止時關閉這個專用Chrome及其capture_server，不要pkill其他Chrome。登入憑證、session key、原始netlog不要交付。

`webcapture.sh 545`／`webcapture_finish.sh 545`會分派到此專用流程。請使用上面的分步命令或`games/545/capture.sh`；不要讓未分派的696 math流程解析545。

## 離線mock／replay

在專案根目錄，Python需安裝`cryptography`：

```sh
python3 replay_545.py                         # 預設math，8546，開專用Chrome
python3 replay_545.py --source wire           # 固定真站應用層封包快照
python3 replay_545.py --rounds 2487517748000020545  # 已觀察的完整重轉局
python3 replay_545.py --math-dir games/545/math
python3 replay_545.py --no-browser            # 只起本機server
```

所有主機在專用mock Chrome內指向127.0.0.1；不需VPN、真站token、sudo或改hosts。mock為合成SSO，周邊VIP／活動服務有明確stub。遊戲協定回應來自545實包；未支援下注／模式回400，不借用696盤面。

依實測的請求欄位分池，僅排除UI context f25；保留f26有無及內容。請在前端選擇有樣本的相同基本下注及模式。math每次SPIN前重讀；修改命名欄位會重新編碼並加密送回。輪播時只為局號單調性重寫f20，保留545尾碼；餘額使用樣本postMoney並回應後續查詢。這是結果重播，不是依下注生成新結果的機率引擎。

## 驗證

```sh
python3 games/545/verify_math.py
python3 games/545/verify_mock.py --source wire
python3 games/545/verify_mock.py --source math
python3 games/545/verify_hot_reload.py
```

Python math codec無額外相依。獨立前端codec驗證需要Node與protobufjs：
`npm install --prefix games/545/runtime --ignore-scripts --no-audit --no-fund protobufjs@7.5.4`。
驗證相依安裝於本遊戲的`runtime/`，不另複製專案。`math_validation.json`、`mock_validation_wire.json`、`mock_validation_math.json`、`hot_reload_validation.json`保存驗證結果。2026-11-24已由操作人員確認Mac普通Chrome可進場轉局，本機log確認兩局成功；Windows實機及長時間／全部特殊演出仍待驗收，詳見`replay_browser_validation.json`。

樣本與缺口見`coverage.json`、`math/INTERFACE.md`；來源幣別見`math_sources.json`。原USD帳號被踢前的2局與後續THB樣本分屬不同session，不能混合計算金額／RTP。

## WebP 全專案批次驗證（2026-11-09）

現行版本已辨識的 WebP 162/162 檔通過格式、尺寸及 loopback HTTP 驗證。含保留歷史版本的完整目標為 162/162。詳見本款 texture_validation.json 與根目錄 artifacts/texture_webp_batch_20261109.json。 未覆蓋的 import packs／binary packs 分別為 0/3，仍列在報告；尚未做 Windows 實機完整畫面驗收。

## Git checkout / local-only files

Login config, authenticated captures, current_session pointers, profiles, logs and ZIPs are local-only. Original archive members and archive_manifest.json are tracked; replay reconstructs its ZIP load bundles locally. Install root npm dependencies and `npm ci --prefix games/545/runtime` before original-codec checks. See the root README for setup.


## 2026-11-24 登入／50%卡住修正

同事以原始126局及新轉入資料都卡在登入／載入後，表示不能只憑加密HTTP測試通過就判定瀏覽器可用。已改用本地同源transport並保留545 crypto hook；補入本款缺少的`smallicon/lang/zh-CN/strings.json`與15個原版圖示，合成SSO補齊id／newNickname／platform等初始化欄位。修正後實際送出握手、初始化與兩筆成功SPIN，操作人員確認可以轉局。

同事須同步`games/545/mock_server.py`、新增的`games/545/replay_transport.js`及`games/545/static/smallicon/`，然後關掉舊545 replay程序再重新執行`python -B replay_545.py`。保留原有math資料與其他資料匯入工具；不用重抓真站、換帳號或VPN。

診斷入口為本機`https://127.0.0.1:8546/__replay_status`（服務自簽測試憑證）；包含轉局數、最近錯誤／請求及缺資源路徑。只記錄本地測試資訊，不記錄真站token。用一般Chrome測試，勿開DevTools；除錯連線本身可能觸發Jscrambler防護，不能把該防護回報當作普通瀏覽器的根因。

本輪回歸：wire124局／130次回放，math126局／四池／134次回放，熱更新及錯誤JSON恢復通過；WebP162/162通過檔頭、尺寸與實際mock HTTPS的MIME／完整bytes檢查，三個binary import packs仍列於texture報告，非Windows實機完整驗證。


## 2026-11-24 素材驗證範圍補充

先前162/162 WebP與兩局成功SPIN不代表完整素材驗收。後續唯讀核對發現原始清單另有301個`9926e`音效／native資源（game50、other200、extra51），本機當時皆缺少。機率團隊回報已在其環境補齊；本次僅確認缺口，未在此處下載或補檔，也未獨立重驗對方的14輪結果。後續每款須依`AGENTS.md`及RUNBOOK「完整素材清單核對」檢查所有引用資源，特別包含隨機／延遲音效；WebP報告只代表貼圖檢查範圍。


## 2026-11-24 唯讀素材盤點

本款`asset_validation.json`已依原始config/native/import清單核對，包含`9926e`隨機音效的原始名稱／副檔名與內容檢查，並以本款真正的本地replay server核對現有素材HTTP回應。報告也另列WebP結果。本份checkout仍有清單缺項／未解析packs，不能視為完整素材驗收通過；可選或歷史清單的缺項也不等同已證實的本模式請求失敗。本輪未下載或補檔，沒有修改math資料或重跑Windows實機。重查：`python3 -B routex/asset_batch_audit.py 545`；exit 1時查看報告中的缺口。總表見根目錄RUNBOOK。


### 2026-11-24 來源確認補檔後重驗

本輪累計補回 1658 個有原始 UUID／版本／副檔名或已驗證同檔來源的素材；未覆寫既有檔案。來源、SHA256及下載失敗記錄見 `asset_repairs.json`，剩餘逐檔清單見 `asset_unresolved.json`。原始清單仍缺 26 項；包含可選／歷史 bundle，不能直接視為當前模式必然會觸發的錯誤。

實際 replay HTTP：2056 項有效、0 項錯誤；WebP 162/162 通過格式、尺寸與 HTTP 核對。另有 29 筆未覆蓋項目（含未解析 binary packs／副檔名），所以未宣稱完整素材或 Windows 實機驗收。本輪未重跑瀏覽器長時間演出。
