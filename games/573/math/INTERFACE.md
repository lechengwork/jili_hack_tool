# 573 幸運金幣2：逐局介面

## 本地回放與修改

根目錄 `.venv/bin/python -B replay_573.py --bonus-first` 預設讀本資料夾並熱載入；基本注選 3,000。一般、extra bet、50 倍與 100 倍內購分池，原始請求 f26 由對應單號索引補回，不從稀疏回應猜測。

具名欄位的修改會重新編碼，不僅讀 `_wire`。原本相同的 `data.TotalWin`／`totalWin`，只改一份會同步另一份；兩份同時改成矛盾值會拒絕。原始 payload 未改時保持完整 byte round-trip，未知欄位與原始出現表示保留。這是結果重播與原局餘額展示，不按當前注額生成新盤面或重算賠付。詳細操作與驗證見 ../README.md。

## 內購參數與實測

`spinReq.purchase` 對應下注內容 f23；未內購時省略。`purchase.f1` 是原始 int32 旗標，兩筆內購皆為 1，其他值語意未確認。`purchase.selector` 對應 f2：實測 0 為 50 倍方案、1 為 100 倍方案。`purchase.amount` 對應 f3 double，為本次購買金額；基本 `spinReq.bet` 仍為 3,000，不能把它誤當內購實扣。JSON 的 `_wire` 保留 f2=0 明確出現／被省略等原始差異。

50 倍方案單號 2489894627000010573，扣 150,000 IDR，總回收 198,000，RoundQueue 19 段；100 倍方案單號 2489896611000040573，扣 300,000 IDR，總回收 252,000，RoundQueue 5 段。兩筆都以相鄰餘額核對實扣，最後 BonusRemainRound=0，完整 payload byte round-trip、簽章與原始 rcProto2 資料 codec 比對通過。兩筆的 Extra 都為 0，不能只憑 Extra 判斷內購模式。

使用者提供的玩法圖說明：50 倍方案觸發 1 或 2 個財富錢幣堆；100 倍觸發 2 個財富錢幣堆。此為規則來源，尚未據此推斷所有盤面旗標與 enum 的對應。修改 purchase 具名欄位會重新編碼，已驗證不會只沿用舊 sidecar。

本次核對已覆蓋一般、extra bet、50 倍內購及 100 倍內購。下方早期 179 局／75 局記錄是原批次快照；第二個 session 後續已混入一般與內購，最新分組快照見 ../coverage.json 及 ../math_sources.json。

逐局檔為 `<單號>.json`，規格見 `../math_573.proto`，雙向 adapter 為 `../math_adapter.py`。成功 SPIN 驗章、原始 rcProto2 codec 比對及完整應用層 payload byte round-trip 全通過才發布。握手、輪詢、心跳、失敗或未驗章回應不算樣本。

`data` 使用原始 rcProto2.SpinAck 名稱，包含 RoundQueue、BonusTotalWin、TotalWin、RTP、LID、RID、AckType、Extra。RoundInfo 包含 Symbol、Mul、FinalSymbol、FinalMul、AwardDataVec、RoundWin、PotList、BonusRemainRound、BonusTotalRound、GetBonus、AwardTypeFlag、MaxFlag、PlateChangeFlag、ScatterMultiplier。名稱直接取自 codec，不自創 enum 或倍率語意。

傳輸容器保留 data(f1)、service(f2)、totalWin(f3)、postMoney(f6)、roundIndexV2(f20)、spinReq(f23)。f26 保持中性名稱與原始 integer array，不假設其他遊戲的 feature enum。roundIndexV2 以十進位字串保護 uint64 精度。spinReq.bet 為共用傳輸層欄位，573 的實扣與特殊模式倍率仍待實包及餘額關聯核對。

`_wire` 是工程還原 sidecar，保留完整原始表示、欄位出現與未知欄位；修改具名欄位會重新編碼，其餘保留原樣。service/context/f26 暫保留 integer array，尚未確認的語意不偽裝成已知欄位。這些資料沒有 token、key 或 GRV。

已有同單號且內容不同的檔案不覆寫；session/math 保存原始輸出，math_conflicts.jsonl 或初次 collector 的 math_errors.jsonl 記錄衝突。schema／解碼／round-trip 失敗保留原包並記錄錯誤。

目前先完成結構與合成資料驗證；真實成功 SPIN 已完成完整 byte round-trip 與原始 codec 驗證，數量見 ../adapter_validation.json；特殊模式完整覆蓋仍待更多樣本。初始化實包 f1 已觀察到 IDR，與擷取設定一致；未確認特殊模式與實扣前不計算 RTP。

## 2026-11-06 extra bet 樣本

第一批 104 局 `SpinAck.Extra=0`。第二個獨立 session 20261106-110729 有 75 局成功 SPIN，操作人員確認全為 extra bet，且每局原始 codec 欄位 `SpinAck.Extra=1`；兩批共 179 局。第二批皆經完整 payload byte round-trip、原始 rcProto2 codec 及簽章驗證，無失敗 SPIN、匯出錯誤或同單號衝突。來源單號索引見 ../math_sources.json。這建立本次 Extra=1 與 extra bet 的實測對應，不推論其他值或特殊模式倍率。

## 實扣與 Bonus 覆蓋

104 局一般下注中，103 組相鄰餘額核對均為基本 bet 的 1 倍；75 局 extra bet 中，74 組相鄰餘額核對均為基本 bet 的 1.5 倍。核對式為前局 postMoney + 本局 data.TotalWin - 本局 postMoney；各 session 首局未納入。extra bet 計算實扣與 RTP 分母不可只使用基本 bet。第二批有一筆多段 RoundQueue／GetBonus／BonusTotalRound／BonusTotalWin 樣本，具體末段狀態與局號見 ../coverage.json。這是有限樣本的實測，不代表所有特殊模式或理論機率已覆蓋。
