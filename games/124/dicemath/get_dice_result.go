package dice

// ===========================================================================
//
//	★ 機率端只要改這個檔案 ★
//
// 把下面的 GetDiceResult 實作完，然後跑：
//
//	go test ./services/common/game/dice/...
//
// 全綠就結束。規格全部寫在 dice.go 的型別註解與 dice_test.go 的測試裡，
// 其他檔案不用動。
//
// ===========================================================================

// GetDiceResult 算一局。
//
// 要做的事：
//  1. 擲兩顆骰子（各 1..6，公平），填 Dices 與 Sum。
//  2. 決定本局要在哪幾格蓋 EXTRA、蓋多少，填 ExtraMults（沒蓋填 0）。
//  3. 填 FinalOdds（沒蓋 EXTRA 的格子填 in.BaseOdds[i]）。
//  4. 依 Bets 與 FinalOdds 算 TotalWin（含本金）。
//
// 硬性要求（測試會擋）：
//   - 所有回傳陣列長度都是 13，Dices 長度 2。
//   - EXTRA 賠率一定比原始賠率高，且 (ExtraMults[i]-1) 要被 (BaseOdds[i]-1) 整除。
//   - ★ EXTRA 不可以看 in.Bets 決定 ★。原廠實測 29 局中有 6 局玩家完全沒下注，
//     照樣會灑 EXTRA；Bets 傳進來只是為了算 TotalWin。
//   - ★ EXTRA 不可以看骰子結果決定 ★，兩者必須獨立。
//   - 骰子要是公平的 2d6（測試會做卡方檢定）。
//   - 每格的長期 RTP 要落在 dice_test.go 的 rtpMin / rtpMax 之間，
//     且各格之間的差距不能超過 rtpSpread。這是這個函式唯一需要動腦的地方，
//     細節見 docs/dice-game/EXTRA_MULT.md 的「每格需要的 E[extra]」。
//   - 不要有 package 層級的可變狀態，必須 goroutine-safe（測試會用 -race 併發呼叫）。
//   - 不要改動 in 的內容。
func GetDiceResult(in *DiceInput) *DiceOutPut {
	panic("dice.GetDiceResult 尚未實作")
}
