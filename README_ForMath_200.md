# Pappu：機率團隊入口（平台 4103／JILI 200）

- 填機率設定：`games/200/pappumath/game/g4103/setting_4103.go`。
- 規則、含本金約定、server 直接呼叫及測試：`games/200/pappumath/README.md`。
- 六份真站逐局 JSON 與欄位表：`games/200/math/`、`math/INTERFACE.md`。
- 乾淨 proto：`games/200/math_200.proto`。

比照 124 的本地 Go module，不經 RPC。正式權重／RTP 目標留給機率團隊填，未填時明確回錯誤。Pappu 用含本金 `ReturnOdds`：基礎 10，0 回基礎；RoomEnd.bonus 已是最終回收，不再加本金、不套 124 的 EXTRA 換算。

多人桌每局只抽一次，再逐人結算。Go 模組不管理錢包、下注階段或登入，也不帶真站憑證。

在 `games/200/pappumath/` 跑 `go test ./...`、`go test -race ./...`；在專案根目錄跑 `.venv/bin/python -B games/200/verify_math.py` 驗線路轉換與即時輸出衝突保護。
