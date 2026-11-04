# 518／807 SPIN 即時輸出 math

2026-11-04：兩款 capture_server 現在都在每筆成功 SPIN 完成解密、簽章驗證後，使用各自的 math_adapter 立即轉換，並做完整 payload byte round-trip。**不必關遊戲、不必等 finish_capture。** 只需更新程式後重新啟動既有抓包流程。

| 遊戲 | 持續新增的機率 JSON | 本次工作階段備份 |
|---|---|---|
| 518 | games/518/math/<單號>.json | games/518/webcap/<session>/math/<單號>.json |
| 807 | games/807/math/<單號>.json | games/807/webcap/<session>/math/<單號>.json |

檔案仍為 data／service／postMoney／roundIndexV2／spinReq 五格，符合各款 math proto。JSON用暫存檔完整寫好才原子更名，讀取端不會讀到半份。終端每筆成功輸出會顯示 `math=OK file=...`。心跳、餘額查詢、失敗轉局及未驗章回應不產生 math。

若出現新欄位、結構驗證失敗或 codec 無法無損還原，終端明確顯示 `math=ERROR`，本次 session 的 `math_errors.jsonl` 保存錯誤及原始 SPIN 應用層 payload；原始 exchanges 仍完整保留，後續轉局繼續收集。這不是自動推測未知欄位的工具，新 schema 仍需定義後再補轉。

相同單號及相同內容重跑會跳過；若 games/<gid>/math 中有機率改過的同單號檔案，保留該修改，原始結果留在session/math並回報衝突。需要將原始結果重新放回共用math目錄時，先自行備份／移走修改檔，再執行finish。

`finish_capture.py` 改用同一個輸出流程，再驗章並補轉本次 session 的成功 SPIN，包含啟動早期尚未取得金鑰而錯過即時解碼的封包。摘要提供 math_written（含既有相同檔案）、math_errors。518既有原生codec named export仍另外保留。

```
python games/518/finish_capture.py
python games/807/finish_capture.py
python routex/test_live_math.py
```

math/all.jsonl、COVERAGE、descriptor及ZIP是發版快照，不會每轉一局就重建。即時消費請讀逐局JSON；需要重新發版時再跑各款build_math／打包器。抓包不會自動下注或切換模式，轉局仍由操作人員執行。
