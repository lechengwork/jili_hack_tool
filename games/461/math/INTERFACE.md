# 461 海盜女王2 機率介面（一般、特色購買及自然免費局已驗證）

逐局檔案：`games/461/math/<單號>.json`。專用 schema：`math_461.proto`。雙向 adapter：`math_adapter.py` 的 `wire_to_math`／`math_to_wire`。

`data` 使用本款原始 `pirate2Proto.SpinAck` 名稱與欄位號：RoundQueue、FreeTotalWin、TotalWin、ShowIndex、NowMoney、AckType、RTP。RoundQueue 中保留 ComboStageData、RoundWin、RoundMult、AddMult、AwardTypeFlag、FreeRemainRound、FreeNowRound、FreeTotalRound、MaxFlag。連消階段保留原始盤面、倍率、補落與獎項；不自行推導或刪除。

通用應用層外框的 f2、f3、f6 先維持中性名稱，f23（spinReq）先保留完整整數陣列；未有 461 自己的實包前，不套其他遊戲的 purchase／context 語意或倍率。roundIndexV2 保留 uint64 十進位字串，避免精度損失。一般模式實包已確認 f20 為本款單號、f23.f1 為 3000 底注；f6 與連續餘額／TotalWin 對帳見 coverage.json。f23 的模式 context 在回應中為空，但原始請求 f25 含 f1=0、f2=0、f4=0，已在 live_validation.json 保留，不能只憑回應的空 context 區分 extra／內購。尚待特殊模式實包完成對照。

每層 `_wire` 整數陣列保存原始位元組、欄位存在性及未知欄位；修改命名欄位會重新編碼，未改欄位沿用原始表示。完整 payload 必須 byte round-trip，並交叉比對原始 pirate2Proto，否則不發布看似成功的 math。

每筆驗章成功 SPIN 即時原子發布，不等 finish。若共用 math 已有不同內容，不覆蓋；原始結果留在該次 session/math，衝突記於 math_conflicts.jsonl。只有成功驗證的逐局 JSON 才能計入 coverage，合成 fixture 不計。

一般模式已取得真實樣本；特色購買及自然免費局均已取得實包，extra bet 依使用者確認為介面不提供；來源幣別、扣款倍率、獎項旗標及 RTP 欄位含義未確認，不用跨款假設計算金額或 RTP。

## 已觀察的特色購買

單號 2490007724000000461：底注 IDR 1,000；請求 f23.f1=0、f23.f2=0、f23.f3=39,500；UI 與連續餘額實扣同為 39,500。原始回應的 spinReq.f23 只編碼 f3=39,500，明確傳入的零值不能與回應省略表示混為一談。整筆回應含 10 次免費局，最後 FreeRemainRound=0、FreeNowRound=10、FreeTotalRound=10。TotalWin=93,300，FreeTotalWin=90,300；完整 payload 已通過原始 codec 比對及 byte round-trip。

本次 UI 無額外下注入口（使用者確認），extra bet 標為不適用。自然觸發免費局已獨立取得，見下方單號；購買後免費局與自然觸發分別列證。未知 flag／enum 保持原始名稱與值。

原始下注輸入另有 `spin_request_461.proto` 與 `request_adapter.py`（`request_to_math`／`math_to_request`）；`verified_input_examples.json` 的 spinReq 為實際請求，不是回應 echo。原始明確零值、未知欄位與線路順序由 `_wire` 保留，下注欄位可修改後編碼。

## 自然免費局實包

單號 2490024636000020461，原始請求不含購買 f23。回應 RoundQueue 共 11 筆，含觸發局及 10 次免費局，末筆 FreeRemainRound=0、FreeNowRound=10、FreeTotalRound=10。TotalWin=134,400、FreeTotalWin=125,400（IDR）。簽章、原始 pirate2Proto 與完整 payload byte round-trip 均通過；共享 math 與 session math 一致，沒有衝突或 math/decode 錯誤。完整證據見 natural_free_detected.json。

最終 session 20261106-131323：385 筆成功 SPIN 均已即時發布並完成重驗；簽章／原始 codec／完整 payload byte round-trip 通過，0 錯誤、0 衝突，共享 math 全部與 session math 相同。385 份原始下注輸入也已完整 byte round-trip。機率團隊可直接使用本目錄逐局 JSON 及本款專用 proto／雙向 adapter；未知語意仍依中性欄位與原始表示保留。

## math 本機回放

執行 `.venv/bin/python -B replay_461.py` 即從本目錄 JSON 回放；`--bonus-first` 可快速驗證自然／購買免費局。每次 SPIN 重新載入修改或新增的 numeric JSON，按本款下注與購買參數分池。支援 `--math-dir`、`--rounds`、`--source wire`、`--no-watch-math`。輸出是擷取原局結果與餘額，沒有跨下注縮放或模擬連續錢包。詳細限制與驗證見本款 README.md 的本機 replay 章節。
