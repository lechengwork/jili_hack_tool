// Package dice 是骰子遊戲（7up7down，JILI 124）的機率運算沙盒。
//
// 機率端只需要實作 get_dice_result.go 裡的 GetDiceResult，
// 跑 `go test ./services/common/game/dice/...` 全綠就算完成。
// 這個檔案是規格與共用常數，不要改。
package dice

// PosCount 注點數量。
const PosCount = 13

// 注點順序＝畫面順序（由上到下、由左到右），與機率端的賠率表一致：
//
//	0 = 2-6 (小)    1 = 7 (和)     2 = 8-12 (大)
//	3 = 點數2   4 = 點數3   5 = 點數4   6 = 點數5   7 = 點數6
//	8 = 點數8   9 = 點數9  10 = 點數10  11 = 點數11  12 = 點數12
//
// 原廠封包用的是另一套順序（0=和、1=小、2=大，3..12 相同），
// 轉換由遊戲層的 adapter.go 處理，機率端不用管。
const (
	PosSmall = 0 // 2-6 DOWN
	PosSeven = 1 // 7
	PosBig   = 2 // 8-12 UP
	PosSum2  = 3 // 之後依序是點數 3,4,5,6,8,9,10,11,12
)

// PosNames 各注點名稱，測試輸出用。
var PosNames = [PosCount]string{
	"2-6", "7", "8-12", "2", "3", "4", "5", "6", "8", "9", "10", "11", "12",
}

// DefaultBaseOdds 基礎賠率，★含本金★形式、★畫面順序★。
// 逐格對應機率端賠率表的「實際賠率」欄：1:1 記成 2、1:26 記成 27。
//
// 來源：JILI 124 GameConfig(cmd 23) f3 實測 [4,1,1,26,12,8,6,5,5,6,8,12,26]
// 各 +1 後再重排成畫面順序。
var DefaultBaseOdds = [PosCount]int{2, 5, 2, 27, 13, 9, 7, 6, 6, 7, 9, 13, 27}

// DefaultMaxBet 每個注點的下注上限（畫面順序），單位 db point (1:10000)。
// 來源：GameConfig(cmd 23) f2.1 實測值重排，實際數字由營運決定。
var DefaultMaxBet = [PosCount]int64{10000, 3000, 10000, 200, 400, 600, 800, 1000, 1000, 800, 600, 400, 200}

// DiceInput 一局的輸入。
type DiceInput struct {
	// Bets 各注點下注額，長度固定 13，index = 畫面順序，未下注填 0。
	// 單位：db point (1:10000)，下注 10 元 = 100000。
	Bets []int64

	// BaseOdds 基礎賠率，長度固定 13，★含本金★形式，見 DefaultBaseOdds。
	BaseOdds []int
}

// DiceOutPut 一局的結果。所有陣列長度都必須是 13，index = 畫面順序。
type DiceOutPut struct {
	// Dices 兩顆骰子的點數，長度 2，各為 1..6。
	Dices []int

	// Sum 點數總和 = Dices[0] + Dices[1]。
	Sum int

	// ExtraMults 本局蓋了 EXTRA 的格子的「含本金最終賠率」。
	//
	//	有蓋：填含本金賠率。畫面要顯示 1:18 就填 19。
	//	沒蓋：填 0。
	//
	// 三個規則（測試會檢查）：
	//   1. 0 代表「這格沒蓋 EXTRA」，不是「這格賠率是 0」。
	//   2. EXTRA 賠率一定比原始賠率高：ExtraMults[i] == 0 或 > BaseOdds[i]。
	//   3. (ExtraMults[i]-1) 必須被 (BaseOdds[i]-1) 整除。
	//      因為原廠封包的 extra 欄位存的是「顯示賠率的倍數」，不整除就只能塞小數，
	//      客端乘回去會有浮點誤差（6 x 3.1666666666666665 = 18.999999999999996）。
	//      例：點數5 base=7 → 可填 13(x2)、19(x3)、31(x5)、61(x10)，不要填 20。
	ExtraMults []int

	// FinalOdds 每格本局實際生效的含本金賠率，★13 格全部填滿★：
	//
	//	有蓋 EXTRA：= ExtraMults[i]
	//	沒蓋 EXTRA：= BaseOdds[i]
	//
	// 這裡不要用 0，否則沒蓋 EXTRA 的格子中獎會算成 0 賠付。
	FinalOdds []int

	// TotalWin 本局總返還（★含本金★）：
	//
	//	TotalWin = Σ Bets[i] * FinalOdds[i]   // i 為中獎注點
	//
	// 玩家淨輸贏 = TotalWin - Σ Bets。
	TotalWin int64
}

// WinPositions 依點數和算出中獎注點（畫面順序）。
// 純規則，與下注、與 EXTRA 都無關。
func WinPositions(sum int) []int {
	var out []int
	switch {
	case sum == 7:
		return []int{PosSeven}
	case sum < 7:
		out = append(out, PosSmall, PosSum2+(sum-2))
	default:
		out = append(out, PosBig, PosSum2+(sum-3))
	}
	return out
}

// SettleWin 依 FinalOdds 結算本局總返還（含本金）。
// 機率端的 TotalWin 必須與這個函式算出來的一致，測試會比對。
func SettleWin(bets []int64, finalOdds []int, sum int) int64 {
	var total int64
	for _, pos := range WinPositions(sum) {
		total += bets[pos] * int64(finalOdds[pos])
	}
	return total
}
