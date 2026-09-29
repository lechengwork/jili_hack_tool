package result

import "dicemath/entity"

// DiceInput 每局輸入(server 鎖注後才呼叫)
type DiceInput struct {
	Version string                  // RTP 版本，例如 "0970"
	Bets    [entity.CellCount]int64 // 各格下注額(最小貨幣單位)，順序依 entity.Cell7..Cell12
}

// DiceOutput 每局輸出(欄位比照對方封包：die1/die2、base_odds、extra_pay、eff_odds、total_win)
type DiceOutput struct {
	Die1       int                   // 骰子 1(1~6)
	Die2       int                   // 骰子 2(1~6)
	Sum        int                   // 點數總和(2~12)
	BaseOdds   [entity.CellCount]int // 基礎淨賠率
	ExtraMults [entity.CellCount]int // EXTRA 倍數 j(1 = 不亮)，對應封包 extra_pay；不區分真實 EXTRA 與假演出
	FinalOdds  [entity.CellCount]int // 最終淨賠率 = ExtraMults × BaseOdds(畫面 nX，對應封包 eff_odds)，即注單快照
	TotalWin   int64                 // 總贏分(含本金)＝Σ 中獎格 Bets[c] × (FinalOdds[c] + 1)
	UsedRNG    []int                 // 本局依序消耗的亂數(稽核重現用)；可推算出真假 EXTRA，僅供 server log，不可轉發給前端
}
