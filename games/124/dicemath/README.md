# dicemath：雙骰 EXTRA（機台 4102）數學引擎

獨立 Go module（`module dicemath`），零外部依賴。

## Server 串接：只有一個函式

```go
import (
	"dicemath/entity/result"
	"dicemath/game/g4102"
)

out, err := g4102.GetDiceResult(&result.DiceInput{
	Version: "0970",
	Bets:    bets, // [13]int64，順序同封包：7, 2~6, 8~12, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12
})
```

- 必須在**鎖注之後**才呼叫；鎖注後拒絕任何加注、undo、double 由 server 負責。
- 併發安全，可多個 goroutine 同時呼叫。
- 版本不支援、任一格下注 < 0、13 格下注全為 0、內建設定有誤時回傳 error。
- 支援版本：`0880, 0920, 0940, 0950, 0960, 0970, 0975, 0980, 1020, 1100, 2000`。

## 輸出（`result.DiceOutput`，欄位比照封包）

| 欄位 | 內容 | 對應封包 |
|---|---|---|
| `Die1`, `Die2`, `Sum` | 兩顆骰子點數與總和 | die1 / die2 |
| `BaseOdds` | 基礎淨賠率（畫面 1:N 的 N） | base_odds |
| `ExtraMults` | EXTRA 倍數 j，1 = 不亮（真實與假演出不區分） | extra_pay |
| `FinalOdds` | `ExtraMults × BaseOdds`，畫面 nX，注單快照 | eff_odds |
| `TotalWin` | 總贏分（含本金）＝ Σ 中獎格 `Bets × (FinalOdds + 1)` | total_win |
| `UsedRNG` | 本局依序消耗的亂數，稽核重現用 | —（**只能寫 log，不可轉發前端**） |

## 目錄

```
entity/            格子索引、中獎格判定、輸入輸出、版本白名單、VersionSetting
game/              DiceMath 通用引擎、TheoryRTP（解析 RTP）
game/g4102/        機台 4102：GetDiceResult 入口、各版本設定（setting_4102.go）、模擬報表
randomNumber/      RNG（可注入序列、記錄已用亂數）
simulator/         蒙地卡羅模擬
```

## 調整設定

各版本設定在 `game/g4102/setting_4102.go` 的 `versionSettings`，每版本一組：

- `NoExtraRate`：整局不發 EXTRA 的機率（萬分比，2500 = 25%）。
- `ExtraWeights`：有 EXTRA 的局，13 格 × j=1..10 的權重（可直接貼上 Excel「設定」欄）。
- `LitCountWeights`：有 EXTRA 的局，畫面總亮格數 K 的分佈。

整體 RTP：`期望淨賠率 = (g + (1 − g) × Σ(w_j × j)/Σw) × 淨賠率`，`g = NoExtraRate/10000`，`RTP = Prob × (期望淨賠率 + 1)`。

## 測試

```bash
go test ./...                                                        # 單元測試＋解析 RTP 驗證（改表後必跑）
DICE_SIM=1 go test ./game/g4102/ -run "^Test_RTPConvergence$" -v -timeout 48h   # 各版本 1000 萬局模擬，產生 4102_rtp_version*.txt
```

PowerShell：`$env:DICE_SIM=1; go test ./game/g4102/ -run "^Test_RTPConvergence$" -v -timeout 48h`
