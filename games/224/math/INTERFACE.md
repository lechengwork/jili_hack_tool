# Go Rush 機率介面 — 平台4104／JILI224

逐局入口：`math/<原始roundIndex>.json`；專用proto為上層`math_224.proto`，原始工程schema為`aviator_224.proto`。不另建ZIP或dist。

每份math只代表本帳號有正額下注、收到成功BetResp並完成FlyEnd的完整一局。兩個下注區仍屬同一局。零額BetReq、握手、心跳、餘額輪詢及旁觀不算成功下注樣本。

|欄位|來源與含義|
|---|---|
|round_id|BetResp.roundIndex，int64以十進位字串保真，不轉JS Number|
|currency|本場IDR；初始回應中wallet原始f7=IDR、f5=Rp、f1=7，帳號token幣別亦相符|
|spinReq|本款原始BetReq，betData各區bet與autoRate、seed、useFree、clientName保留原名；不將autoRate當作實際兌現倍率|
|data.betResponse|本款BetResp；betFailed=true不輸出成功math；未確認free bet模式先拒絕發布|
|data.cashOutReqs|本帳號主動送出的CashOutReq，依實際順序；自動兌現可能沒有此請求|
|data.cashOuts|本帳號CashOut回應，myRate、win、betType、coin、now保留原名及實際有無；省略的proto scalar依proto預設為0|
|data.flyEnd|FlyEnd：endRate為本局終止倍率，totalWin為本帳號總回收（含已兌現本金），coin為來源餘額；isMax與now依封包保留|

這是Crash遊戲，不是slot SPIN；成功下注到結算是math輸出單位。倍數上升由SyncRate同步，不能把每筆SyncRate算一局。盤面動畫／歷史倍率不構成下一局機率證據。總回收使用真站結果，另核對本局CashOut.win加總與FlyEnd.totalWin一致，不另套slot下注倍率公式。

傳輸為明文protobuf WebSocket／TLS。觀察到的本款訊息沒有獨立應用層簽章欄位，不捏造驗章成功；TLS憑證驗證保持開啟，並用原始aviatorProto逐筆驗證與回編完整BetReq、BetResp、CashOutReq、CashOut及FlyEnd應用層frame。未知wrapper欄位或原始codec回編不一致時保留原始frame、記錄錯誤並拒絕發布math。

`math_adapter.cjs`直接載入本款原始codec，`math_adapter.py`提供`wire_to_math`、`math_to_wire`、`round_to_math`及`math_to_round_wire`。公開math沒有原始wire bytes；byte表示、欄位存在性及完整wrapper保存在忽略版控的session/math_wire。雙向轉換時搭配該局自己的wire context，以保留完整原始表示。若改變cashout結構而不只是欄位值，adapter會拒絕舊context。

即時輸出：現在執行中的session用被動watch_live_math.py，不中斷抓包；下一次capture_server.py直接內建同一Collector。完成一局即驗證原始codec與完整frame byte round-trip、再以fsync及macOS RENAME_EXCL原子發布。共享math已修改則保留session/math原始結果並寫math_conflicts.jsonl，不覆蓋。finish_capture.py只補轉、重驗與彙整。

已確認原廠提供雙下注區、手動與自動兌現；尚未推導本款精確Crash分布、RTP、seed組合／hash演算法與server seed揭露驗證，不能宣稱provably-fair驗證已完成。少量實包也不能用來估計真實RTP。free-bet、未觀察的分次兌現或罕見模式維持拒絕發布，等待實包確認。

2026-11-09 公平性補充：已有一筆server seed對下注前SHA-256承諾的精確驗證，尚未完成完整種子組合到倍率的獨立重算。排行榜本帳號雙注以總回收／總下注呈現rate，例如(160000+168000)/200000=1.64；這是兌現後的合併回收倍率，不是9.65677的墜落倍率。詳見上層analysis/rank_fairness_validation.json。
