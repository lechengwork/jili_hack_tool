# 幸運捷豹500 — 平台1839／JILI664

## 本地 replay

在專案根目錄執行 `.venv/bin/python -B replay_664.py`。預設從438份math讀取，每次SPIN前偵測檔案變更；機率團隊改動的named欄位會重新編碼後送回前端。原始math不被replay覆寫。

- 快速試四種模式的Bonus：`.venv/bin/python -B replay_664.py --bonus-first`。
- 原始實包來源：`.venv/bin/python -B replay_664.py --source wire`。
- 指定局序：`--rounds 2490172819000050664,2490143619000010664`。
- 其他math目錄：`--math-dir /absolute/path/to/math`；固定啟動快照：`--no-watch-math`。
- 只開服務：`--no-browser`；換port：`--port 8666`。Ctrl+C會停止replay服務；專用Chrome程序結束時，啟動器也會停止服務。

一般／1.5倍／8倍樣本使用底注3000；特色購買樣本使用底注1000、單次45000。下注與模式分池，未擷取條件會明確拒絕，不把其他模式的盤面混入。`--bonus-first`只選四個代表局，各模式循環同一局；完整438局請用預設啟動。

顯示的是來源局的結果及餘額，切換樣本時餘額可能跳動，不是新生成的機率結果或真錢帳戶。循環或跨模式後如單號倒退，只調整送給前端的局號以保持遞增，保留末三碼664；原始來源單號記在replay log。

replay使用HTTP loopback與專用Chrome profile，所有該視窗DNS導向本地，API／素材請求轉送本地origin，無上游fallback、無真站登入或金鑰；不需VPN、不改hosts、不關閉瀏覽器憑證驗證。原始WASM的mock公開金鑰替換沿用共用傳輸工具，664封包仍由本款adapter負責。

首次啟動若沒有replay_samples.json，啟動器會從兩場已驗章的應用層資料建立；不匯出transport的token、ephemeral key或session key。`build_replay_samples.py`可以明確重建來源。

後端驗證：`.venv/bin/python -B games/664/verify_replay.py --source math`及`--source wire`。各438局／4池、442次加密SPIN回應、循環、餘額、client隔離及未支援下注拒絕均通過。math修改熱載入與壞檔拒絕見replay_math_reload_validation.json；瀏覽器試轉驗收另記replay_validation_*.json，不把後端通過當成畫面已驗收。

對照：CMS 111000664、新 LoginGame /lj500/?gameID=664、原始 HTML Lucky Jaguar 500。擷取帳號 tryplayer003idr 為保留帳號，初始化與UI已確認來源幣別IDR。機率入口為math/INTERFACE.md、math_664.proto及math/<單號>.json，不另建ZIP或dist。

關 VPN → login_capture.py 取得新 URL → capture_server.py 建新獨立 session → Brazil／São Paulo VPN 確認連線 → open_capture.py。僅操作人員轉局或購買功能。不要開 DevTools。

collector 監聽127.0.0.1:8664，使用專用 Chrome profile、不改 hosts、保留憑證驗證。每次新登入不重用 key。原始封包、GRV、key、URL 存在忽略版控的 webcap/session。

即時 math 必須通過簽章、本款原始 codec 與完整應用層 byte round-trip。math_adapter.py已由本款lj500Proto建立並逐筆交叉驗證；127筆初期暫緩輸出全由watch_live_math.py被動補齊，未中斷使用者擷取。後續啟動直接載入完成版adapter。live_math_664.py使用完整暫存寫入、fsync、RENAME_EXCL原子更名與衝突保存，不覆蓋機率團隊修改檔。finish_capture.py只重驗與補轉，不是首次產生math的必要步驟。

初次 session 20261106-152813：1筆 type1 ret0 初始化，簽章OK，0 SPIN。因 lang/annin 與 astarte-aeon 路徑漏列而404，出現數字24/43/25提示，語系原文為消息／連接已斷開請重新啟動遊戲／確認。已修正素材允許路徑並補齊原始語系與版本表，重新登入，不把舊 session 算成功擷取。

Session 20261106-153325已關閉：215筆回應簽章全過；127筆成功SPIN、127份math，原始codec、完整payload回編、原始輸入回編及共享/session math一致性全部通過。0錯誤、0衝突、無殘缺尾行。一般77，1.5倍27，8倍22，特色購買1；兩種extra與購買各有Bonus，127筆實扣全部吻合UI。詳見final_capture_summary.json、coverage.json及live_validation.json。

GetBonus／BonusSymbol保留原始整數語意，內部獎勵階段、重觸發及罕見旗標未宣稱窮盡；首場未取得一般模式Bonus，第二場已補齊單號2490172819000050664。重驗：`.venv/bin/python -B games/664/finish_capture.py`。

背景檢查：本聊天heartbeat 500於擷取期間每10分鐘一次，完成後停用。

補抓session 20261106-155357已關閉：311筆一般SPIN，包含3筆Bonus（2490172819000050664、2490173571000020664、2490174499000020664）。311筆原始請求皆無f23／f26，data.Extra=0。原廠codec、完整請求／回應回編、驗章及共享/session math一致性全部通過。背景檢查已刪除。

兩場合計438局／438份math：一般388、1.5倍27、8倍22、特色購買1；627筆回應驗章全過，0錯誤、0衝突、無殘缺尾行。原始session與金鑰獨立保留，根目錄final_capture_summary.json、coverage.json與live_validation.json為兩場彙整。summarize_sessions.py可從各session已驗證報告重建彙整，不修改逐局math。

2026-11-09瀏覽器驗收：使用者確認已正常進入並轉完一般模式；本地服務實收單號2490172819000050664，Extra=0、GetBonus=2、TotalWin=45000、PlateSymbol長度6。修正重建SSO Request轉送後，握手與初始化正常。額外下注與購買的畫面尚未另行確認，四模式完整加密後端測試均通過。活動landingpage與gtag分析服務不提供真站內容，不計作遊戲核心封包樣本。

## WebP 全專案批次驗證（2026-11-09）

現行版本已辨識的 WebP 271/271 檔通過格式、尺寸及 loopback HTTP 驗證。含保留歷史版本的完整目標為 271/271。詳見本款 texture_validation.json 與根目錄 artifacts/texture_webp_batch_20261109.json。 未覆蓋的 import packs／binary packs 分別為 116/9，仍列在報告；尚未做 Windows 實機完整畫面驗收。

## Git checkout / local-only files

Login config, authenticated captures, current_session pointers, profiles, logs and ZIPs are local-only. Original archive members and archive_manifest.json are tracked; replay reconstructs its ZIP load bundles locally. Install root npm dependencies and `npm ci --prefix games/545/runtime` before original-codec checks. See the root README for setup.
