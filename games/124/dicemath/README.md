# 骰子遊戲機率沙盒（7up7down / JILI 124）

給機率端的工作區。**只要改一個檔案，把測試跑綠就結束。**

這是一個獨立的 Go module，零外部依賴（連 testify 都沒用），`cd` 進來就能跑，不必連網抓套件。

要改的檔案：`get_dice_result.go`

```bash
cd games/124/dicemath

go test ./...            # 完整跑，約 2 秒
go test -short ./...     # 快速跑，統計測試用小樣本
go test -race ./...      # 併發安全
```

全綠就完成。其他檔案不用動，也不需要碰遊戲層、封包、資料庫。

---

## 函式長這樣

```go
type DiceInput struct {
    Bets     []int64 // 各注點下注額，長度 13
    BaseOdds []int   // 基礎賠率，長度 13
}

type DiceOutPut struct {
    Dices      []int // 兩顆骰子
    Sum        int   // 點數和
    ExtraMults []int // 本局 EXTRA 賠率，沒蓋的填 0
    FinalOdds  []int // 每格實際生效的賠率，13 格填滿
    TotalWin   int64 // 總返還
}

func GetDiceResult(in *DiceInput) *DiceOutPut
```

## 五個約定

**一、注點順序＝畫面順序**（由上到下、由左到右），跟你那張賠率表一樣：

```
 0 = 2-6    1 = 7    2 = 8-12
 3 = 2   4 = 3   5 = 4   6 = 5   7 = 6
 8 = 8   9 = 9  10 = 10  11 = 11  12 = 12
```

原廠封包用的是另一套順序（0=和、1=小、2=大），轉換在 `adapter.go` 由遊戲層處理，你不用管。

**二、賠率一律含本金。** 1:1 記成 2、1:26 記成 27。畫面要顯示 1:18 的那格，你就回 19，
玩家押 10 拿回 190。算錢直接 `bet × odds`，不用再 +1。

```go
var DefaultBaseOdds = [13]int{2, 5, 2, 27, 13, 9, 7, 6, 6, 7, 9, 13, 27}
```

**三、`ExtraMults` 沒蓋的格子填 0**，不是 1、不是省略。`FinalOdds` 則要 13 格填滿
（沒蓋 EXTRA 的格子填 `BaseOdds[i]`）。

**四、EXTRA 賠率一定比原始賠率高，而且 `(ExtraMults[i] - 1)` 要被 `(BaseOdds[i] - 1)` 整除。**
因為原廠封包存的是「顯示賠率的倍數」，不整除就只能塞小數，客端乘回去會有浮點誤差
（`6 × 3.1666666666666665 = 18.999999999999996`）。

> 例：點數5 的 base 是 7，可以回 13(×2)、19(×3)、31(×5)、61(×10)，**不要回 20**。

**五、EXTRA 不可以看 `Bets`、也不可以看骰子結果決定。** 三者必須互相獨立。
原廠實測 29 局裡有 6 局玩家完全沒下注，照樣在灑 EXTRA；`Bets` 傳進來只是為了算 `TotalWin`。

---

## 唯一需要動腦的地方：每格的 RTP

基礎賠率只有 72%~83%，全靠 EXTRA 補到目標值，**而且各格要補的量不一樣**。
若所有格共用同一組 EXTRA 機率，「7」那格會超過 100%，玩家固定押 7 就長期打贏。

設 `m` 為蓋在該格的「顯示賠率倍數」（沒蓋 = 1），則：

```
該格 RTP = 命中率 × (顯示賠率 × E[m] + 1)
```

反解出各格要打平 96% 所需的 `E[m]`：

| 注點 | 命中率 | 顯示賠率 | 基礎RTP | E[m]@96% |
|---|---|---|---|---|
| 2-6 | 15/36 | 1 | 0.8333 | 1.3040 |
| 7 | 6/36 | 4 | 0.8333 | **1.1900** |
| 8-12 | 15/36 | 1 | 0.8333 | 1.3040 |
| 2 / 12 | 1/36 | 26 | 0.7500 | 1.2908 |
| 3 / 11 | 2/36 | 12 | 0.7222 | **1.3567** |
| 4 / 10 | 3/36 | 8 | 0.7500 | 1.3150 |
| 5 / 9 | 4/36 | 6 | 0.7778 | 1.2733 |
| 6 / 8 | 5/36 | 5 | 0.8333 | 1.1824 |

最簡單的做法：每格以機率 `q = E[m] − 1` 蓋一個 ×2 的 EXTRA，其餘不蓋。
想做得漂亮一點（偶爾出 ×5 / ×10 製造驚喜）就自己配權重，只要 `E[m]` 對得上就行。

`TestRTPPerPosition` 會把各格實測 RTP 印出來，方便你調：

```
注點            RTP
2-6      95.9612%
7        95.9243%
...
```

RTP 目標值（`rtpMin` / `rtpMax` / `rtpSpread`）在 `dice_test.go` 最上面，
還沒跟營運確認，先放 94%~97%，確定後改那三個常數即可。

---

## 測試在測什麼

| 測試 | 內容 |
|---|---|
| `TestOutputShape` | 陣列長度、骰子 1..6、Sum 正確 |
| `TestFinalOddsConsistent` | FinalOdds 13 格填滿，沒蓋 EXTRA 要填基礎賠率 |
| `TestExtraRules` | EXTRA 比原始高、減 1 後整除 |
| `TestTotalWin` | 總贏分等於各中獎注點 `bet × FinalOdds` |
| `TestNoBets` | 沒下注不出事，且照樣灑 EXTRA |
| `TestInputNotMutated` | 不可改動傳進來的 Input |
| `TestConcurrentSafe` | 併發呼叫無 data race |
| `TestDiceUniform` | 骰子公平（卡方檢定） |
| `TestExtraIndependentOfBets` | EXTRA 與下注無關 |
| `TestExtraIndependentOfDice` | EXTRA 與骰子無關 |
| `TestRTPPerPosition` | 每格 RTP 落在區間、彼此差距不過大 |

另外 `adapter_test.go` 驗的是遊戲層的格式轉換，拿 **JILI 124 真實對局 29 局**當黃金資料
（`testdata/rounds_124.json`，由上層 `ws_session*.jsonl` 解出來），
不呼叫 `GetDiceResult`，跟你無關，但它證明了上面這套賠率定義跟原廠封包是對得起來的。

樣本數可用環境變數調整：

```bash
DICE_ROUNDS=20000000 go test -run RTP ./...
```

---

## 檔案

| 檔案 | 說明 |
|---|---|
| `get_dice_result.go` | **機率端唯一要改的檔案** |
| `dice.go` | 型別、常數、共用規則（不要改） |
| `adapter.go` | 遊戲層的封包格式轉換（機率端不用看） |
| `dice_test.go` / `dice_stats_test.go` | 規格＝驗收測試 |
| `adapter_test.go` | 對照真實封包的黃金測試 |
| `testdata/rounds_124.json` | 29 局實測資料，`mkgolden.py` 產生 |

相關文件：

- `../EXTRA_MULT.md` — 封包實測與推導（extra_mult 的定義、賠付公式、各格 RTP 反解）
- `../WS_PROTOCOL.md` — cmd 22 / 23 的封包結構
- `../ws_124.proto` — 逆向出來的 proto
