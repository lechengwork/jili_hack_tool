# Pappu math：4103／JILI 200

這是比照 124 dicemath 組織的 Go module，零外部依賴，直接放進 server 呼叫。機率團隊主要改 `game/g4103/setting_4103.go`，server 接 `g4103.GetRoomResult`；沒有 RPC、HTTP 或資料庫。完整欄位與原始封包依據見 `../math/INTERFACE.md`，乾淨規格是 `../math_200.proto`。

## Server 呼叫

```go
import (
    "pappumath/entity"
    "pappumath/entity/result"
    "pappumath/game/g4103"
)

// server 鎖注後，將每個有下注玩家的最終下注快照依序傳入。
out, err := g4103.GetRoomResult(&result.RoomInput{
    Version: version,
    Players: []entity.Bets{playerABets, playerBBets},
})
// err 必須處理；未填權重時會得到 game.ErrSettingsNotReady。
// out.Outcome 是全桌同一結果，out.Players[i] 對應傳入的第 i 個玩家。
```

**整桌只抽一次。** 不要在玩家迴圈逐個呼叫 GetPappuResult，否則會抽成不同局。同房即使沒有下注玩家也可以呼叫 GetRoomResult 產生廣播結果；旁觀者不需要在 Players 塞一份全 0 下注。

若 server 已自行管理房間，可先用 `game.NewPappuMath(settings)` 建立不可變引擎，一次 `DrawRound(version)`，再逐人 `game.Settle(frozenBets, *outcome)`。單人模式才用比照 124 的 `g4103.GetPappuResult(&result.PappuInput{Version: version, Bets: bets})`。

本 module 的 Outcome、PappuOutput 不帶玩家身分、登入資料或錢包存取。UsedRNG 只用於 server 稽核，不能轉送前端。server 負責下注階段、鎖注、逾時、同單號冪等、房間分派、下注上下限、錢包扣款／入帳、斷線重連與單號；這些不由 math 重複實作。

## 機率團隊填寫區

`game/g4103/setting_4103.go` 的 versionSettings 目前刻意留空。**尚未填正式權重／目標 RTP，預設不會偷偷用等機率或測試表出結果。** 填入批准的版本與權重後重新編譯即可；啟動時建構並驗證一次，後續呼叫併發安全。

每個版本是一組 `setting.WeightedOutcome`：

| 欄位 | 機率團隊填的內容 |
|---|---|
| Weight | 非負整數權重；所有結果的總和須 >0，且不溢位 uint64 |
| VersionSetting.TargetRTP | 此版本批准的含本金 RTP，例如 0.97（只是格式示意，不是本專案已批准值） |
| VersionSetting.RTPTolerance | 每個下注區的絕對誤差，例如 0.001 表示 0.1 個百分點 |
| Outcome.Winner | 本局圖案，原始 type 1..12 |
| Outcome.ReturnOdds | 12 格含本金最終回收；0 表示使用基礎回收 10 |
| Outcome.Pic | 普通局填相同圖案 type |
| Outcome.IsBonus | 已支援普通局填 false；true 目前回錯誤 |

這裡採「圖案＋全表回收」的聯合結果權重，避免無證據地假設圖案與 EXTRA 獨立。如果機率團隊改用其他抽法，請保留 Outcome 與 Settle 的契約，及每桌只抽一次的約定。測試中的 fixture 版本只驗抽樣邊界，不代表生產權重。

`TheoryRTP(version)` 回傳每個下注區的理論 RTP，公式是 Σ P(某聯合結果) × 該結果中這格是否中獎 × 含本金回收倍數。各格可能不同，不能只驗全格平均。g4103 啟動時會按 TargetRTP／RTPTolerance 逐格驗收；目標未填、任一區超標，入口會回錯誤。六局實測不足以推導這些權重或正式目標。

## 規則與金額口徑

- 固定 12 注區，陣列順序為畫面兩排各 6 格：雨傘、足球、太陽、油燈、牛、水桶／風箏、陀螺、玫瑰、蝴蝶、鴿子、兔子。index=原始 type−1；不使用前端欄優先遍歷順序。
- 普通局開一個圖案；`Pic == Winner`。中獎區按最終回收計算，其他區回收 0；淨損益要扣所有區下注。
- 原始基礎淨賠率 9，所以含本金基本回收 10。`FinalReturnOdds` 已含本金，`TotalWin = Bets[winner-1] × FinalReturnOdds[winner-1]`，不能再 +1。
- 「1 賠 2」若指淨賠 2，`NetToReturnOdds(2)=3`；若指總回收 2X，就直接是 2。這個換算工具講的是名詞，**Pappu 普通局本身仍要求回收至少 10**。
- ReturnOdds=0 是未提高的基礎回收，必須回到 10，不能當成中獎不賠。Pappu 線路 bonus 就是最終回收，不套 124 的 `(odds-1)/base` 限制。
- IsBonus 與畫面額外賠付是不同欄位：樣本有 20／30，但 IsBonus 仍為 false。特殊模式、複數 reward 尚無規格，會回錯誤，不輸出貌似成功的普通結果。
- server 先累加已確認加注、套用撤銷差額，鎖注後才傳入非負最終 Bets。金額用同一整數單位；負數、玩家全 0、總下注或派彩溢位會回錯誤。
- Pappu 實測有 RoomStart／RoomEnd、其他玩家 accountID 分流，是多人房間；124 的 EXTRA_MULT.md 則記錄其已驗樣本為玩家各自 request/response。這點以各款實包為準。

## 測試

在此目錄執行：

```sh
go test ./...
go test -race ./...
```

測試涵蓋：淨／含本換算、0 回基礎、直接 final-return 不重乘、12 區順序、混合下注輸贏、權重邊界與錯誤 RNG、設定未填／不可變、金額溢位、版本拒絕、每桌共同結果、理論 RTP、併發，以及六局原始 IDR 樣本（包括 200,000 → 2,000,000 的中獎局）。

Go 測試資料 `game/testdata/live_rounds.json` 僅含乾淨下注／結果，不含真站憑證或完整原始請求。Python 的 `../verify_math.py` 另驗證完整線路 round-trip、修改後原始前端 codec 解碼，以及即時匯出不覆蓋已修改檔案。
