# JILI 擷取專案長期規則

帳號與操作入口請先查根目錄 `account_registry.json`（來源試算表與 CMS、已觀察的帳號清單及使用註記）；可用連線工具直接重讀來源，不必每次請使用者開表。索引不存憑證，也不代表帳號即時空閒。

以下是使用者已確認、適用於後續每款新遊戲的固定需求。每次開始抓新款時先讀本檔與RUNBOOK.md，不要要求使用者逐款重申。

## 專案與遊戲資料夾

- 所有遊戲都放在同一個jili_hack_tool專案，以`games/<JILI原始gameID>/`區分。
- 每款的程式、素材、擷取資料、mock、replay及驗證結果都放在該遊戲目錄；共用傳輸層可留在`routex/`，根目錄可保留既有慣例的啟動入口。
- 給機率團隊的逐局資料放在`games/<gameID>/math/<單號>.json`，介面說明放在`math/INTERFACE.md`，並提供該遊戲專用math proto及雙向adapter。
- 預設直接使用專案內的遊戲資料夾；除非使用者另行要求，不建立獨立交付ZIP、dist專案或額外完整複本。
- 靜態資源不能只保留 Mac 當次請求的 ASTC。每款交付／replay 驗證前，執行 `python3 -B routex/texture_variants.py games/<gameID>/static --report games/<gameID>/texture_validation.json`，依原始 metadata 檢查 WebP 替代檔；缺檔時準備階段用 `--fetch` 補原站同版本檔案並重驗。須檢查真實 WebP 檔頭、尺寸與本機 HTTP；不得改副檔名假裝格式，也不得把此檢查當作 Windows 實機完整驗證。報告中的未覆蓋 import packs 要保留說明。

## 每筆SPIN即時輸出math

- 每筆成功SPIN完成解密與簽章驗證後，立即用該遊戲專用adapter轉成math JSON並寫入math資料夾，不必關遊戲，也不必等finish才匯出。
- 即時輸出前須確認完整應用層payload可byte round-trip，不能只驗盤面。
- math輸出採完整寫好後原子更名；已被機率團隊修改的同單號檔案不可直接覆蓋，原始結果保留在該次session中並回報衝突。
- 握手、心跳、餘額輪詢、失敗SPIN與未驗章回應不得充作成功math樣本。
- 解碼／schema／round-trip失敗時保留原始封包並記錄錯誤，不可靜默遺失欄位或產出看似成功的math。
- finish只負責工作階段的重驗、補轉、快照與彙整；不能成為首次產生math的必要步驟。
- 若正在執行的舊capture程序尚未載入即時匯出修正，可以用被動watcher補即時輸出，避免為更新而中斷使用者抓包；下次啟動應直接內建即時輸出。

## 新遊戲與真站流程

- 先核對平台代碼、遊戲名稱與JILI原始gameID，不可只憑平台編號建立錯誤對照。
- 沿用順序：關VPN → 取得新的一次性遊戲URL → 開Brazil／São Paulo VPN並確認連線 → 用新URL開啟專用抓包視窗。
- 每次新登入使用獨立session保存請求、隨機值與金鑰；不可混用不同登入或帳號的金鑰。來源幣別須記錄，不能混合幣別推導金額或RTP。
- 可以沿用已驗證的共用傳輸工具，但每款封包結構、schema及特殊模式都須以該款實包與原始codec確認，不可直接套用696或其他遊戲的欄位／倍率／enum語意。
- 保留未知欄位及原始表示；未確認的語意維持中性名稱並列出證據與缺口。
- 不把真站token、session key、GRV或含憑證原始請求放入交付資料或版本控制。
