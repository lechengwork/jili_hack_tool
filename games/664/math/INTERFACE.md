# 幸運捷豹500 — JILI664／平台1839

逐局結果為本目錄的 `<單號>.json`。定義見 `games/664/math_664.proto`；雙向轉換為 `math_adapter.py` 的 `wire_to_math`／`math_to_wire`。原始請求的結構化輔助為 `request_adapter.py`，逐局輸入及扣款證據見 `live_validation.json` 的 `spins[].input`。

## 本次驗證

兩個獨立IDR session（`20261106-153325`、`20261106-155357`）均已關閉，共627筆回應全部驗章成功，其中438筆為成功SPIN。438筆原始codec交叉驗證、完整應用層payload回編、原始輸入請求回編均通過。438份共享math與各自session math相同，0衝突、0錯誤，無殘缺尾行。兩場金鑰與原包分開保留，只合併已驗證的逐局報告。首場127筆初期暫緩math已由被動watcher補齊，第二場311筆直接由collector即時輸出。

## 一般模式Bonus補抓（第二場）

Session `20261106-155357` 已關閉，共311筆一般SPIN，包含3筆一般Bonus：**2490172819000050664**、**2490173571000020664**、**2490174499000020664**。311筆原始請求皆無購買f23及extra f26，data.Extra=0；驗章、原廠codec、完整請求／回應byte round-trip與共享/session math一致性全通過。完整證據見 `live_validation.json` 與 `normal_bonus_detected.json`。

## 模式與實扣（兩場438局）

金額使用封包原始IDR數值，不乘除1000。438筆皆在各自session內，以連續餘額加回本局TotalWin核對實扣，不跨登入串接餘額。

|模式|SPIN數|本次底注／實扣|Bonus單號|
|---|---:|---|---|
|一般|388|3000／3000|3筆，見上節|
|1.5倍額外下注|27|3000／4500|2490143619000010664|
|8倍額外下注|22|3000／24000|2490146579000000664|
|特色購買|1|1000／45000（45倍）|2490147875000000664|

本款實包：原始請求f26.f1=0對應1.5倍，f26.f1=1對應8倍；回應data.Extra分別為1／2。一般本次無f26且Extra=0。購買原始請求f23={f1:0,f2:0,amount:45000}，回應echo僅保留amount。購買f1/f2、context的f1/f2/f4語意未確認，保留中性名稱。45倍只代表本次UI選項與條件。

## Envelope與輸入

|欄位|格式|依據／限制|
|---|---|---|
|data|SpinAck|本款原廠lj500Proto|
|f2|整數陣列|完整原始表示，本次為空，未猜語意|
|f3|double|本次有值時吻合data.TotalWin，保留原始欄名|
|f6|double|由UI與連續餘額核對的局後餘額|
|roundIndexV2|uint64／JSON十進位字串|完整單號，避免JS大整數失真|
|spinReq|整數陣列|伺服器回應echo的完整原始應用層；結構化原始請求另見live_validation.json|
|_wire|整數陣列|工程sidecar，保留未知欄位、欄位順序、explicit zero及packed表示，勿手改|

原始請求與回應echo的零值存在性可能不同，不能只從echo推測原始模式。`request_adapter.py`提供原始請求雙向轉換，未知欄位同樣保留。`spin_request_664.proto`為此輔助介面。

## 本款原廠資料結構

名字與型別來自本款原始codec，不從其他遊戲搬欄位或enum。完整欄位號見proto及math_schema.json。

|訊息|欄位|
|---|---|
|Column|Row: repeated int32|
|Single|Col: repeated Column|
|AwardData|Symbol:int32、Line:int32、Win:double、Mult:double|
|GameAwardData|ADV: repeated AwardData|
|GameWildOdd|WO: repeated double|
|GemInfo|data:int32|
|SpinAck|PlateSymbol:repeated Single；AwardDataVec:repeated GameAwardData；WildOdd／WildOddDone／SuperMult:repeated GameWildOdd；WildWin／BigMult／GameWin:repeated double；GetBonus／BonusSymbol／Extra／AwardTypeFlag／LID／RID:int32；TotalWin／RTP:double；MaxFlag:bool|

修改已知named欄位會改變編碼；未改欄位保留原始wire，未知欄位也保留。`RTP`是原始欄位值，不能當這批樣本實現RTP或特定模式機率。

## Bonus與覆蓋限制

兩種extra的自然Bonus實包均為GetBonus=2且PlateSymbol有6筆；購買實包GetBonus=2且PlateSymbol有5筆。三筆都通過原廠codec及完整payload回編。GetBonus=2不能解讀為兩次免費局，PlateSymbol長度也不能當免費局數。本款原廠schema沒有461的FreeRemainRound／RoundQueue，不套用其結尾判斷。內部階段對應、重觸發、MaxFlag及罕見獎勵未宣稱窮盡。

## 即時輸出與保護

後續啟動collector直接載入已完成的664 adapter。每筆驗章成功SPIN通過原始codec及完整payload回編後即時寫session/math與共享math；以完整暫存寫入、fsync、RENAME_EXCL原子發布。同單號已被修改時不覆寫，原始結果留session/math並記錄math_conflicts.jsonl。非SPIN、失敗或未驗章回應不發布。

重驗命令：`.venv/bin/python -B games/664/finish_capture.py`。最終摘要見final_capture_summary.json。私有URL、key、GRV、Chrome profile及含憑證原始請求均留在忽略版控的session，不放入機率資料。
