# JILI 94 — Rummy（歷史工作留底）

原始 JILI gameID：94；當時記錄的平台代碼：111000094。遊戲為 13 張印度 Points Rummy／錦標賽。

本目錄保存 2026 年 9 月底至 10 月初的擷取分析成果。使用者後續取消此款工作，2026-11-09 將現有內容提交留底；不代表恢復開發或完成交付驗收。

- `math/`：46 份逐局 JSON、彙整 `all.jsonl` 及歷史介面說明。
- `ws_rummy.proto`：依當時實包整理的協定草稿，包含尚未確認的語意。
- 根目錄 `ws_rummy_view.py`：歷史 WebSocket 解碼／匯出工具。
- `static/`：當時保存的遊戲素材；WebP 檢查結果另見 `texture_validation.json`。
- `traffic.jsonl`：本機原始流量，排除版本控制。

本次留底只檢查 Python 語法、JSON 可讀性、逐局資料與彙整一致性，以及待提交檔案的憑證掃描。未重新操作真站或驗證完整 replay；舊解碼器未具備現行完整 byte round-trip、即時輸出與衝突保護，因此只作歷史分析用途，不能直接套用於新擷取。`math/INTERFACE.md` 中的驗證說明屬當時紀錄。
