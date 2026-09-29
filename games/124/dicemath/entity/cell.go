package entity

// 13 個押注格的固定索引順序(比照對方封包)；所有 [CellCount] 陣列都依此順序
const (
	Cell7     = iota // 7
	CellLow          // 2~6
	CellHigh         // 8~12
	Cell2            // 2
	Cell3            // 3
	Cell4            // 4
	Cell5            // 5
	Cell6            // 6
	Cell8            // 8
	Cell9            // 9
	Cell10           // 10
	Cell11           // 11
	Cell12           // 12
	CellCount        // 押注格總數(13)
)

// MaxExtraMult EXTRA 升級倍數 j 的上限；權重陣列長度，index 0 對應 j=1(無 EXTRA)
const MaxExtraMult = 10

// CellCombos 各格中獎組合數(兩顆骰共 36 種組合)，中獎機率 = CellCombos[c] / 36
var CellCombos = [CellCount]int{6, 15, 15, 1, 2, 3, 4, 5, 5, 4, 3, 2, 1}

// CellNames 各格畫面名稱(報表用)
var CellNames = [CellCount]string{"7", "2~6", "8~12", "2", "3", "4", "5", "6", "8", "9", "10", "11", "12"}

// numberCellBySum 點數總和對應的號碼格(7 只有一格，同時是大區也是號碼格)
var numberCellBySum = map[int]int{
	2: Cell2, 3: Cell3, 4: Cell4, 5: Cell5, 6: Cell6, 7: Cell7,
	8: Cell8, 9: Cell9, 10: Cell10, 11: Cell11, 12: Cell12,
}

// WinningCells 回傳點數總和 sum 的中獎格：
// Sum=7 → {Cell7}；Sum≤6 → {CellLow, 點數格}；Sum≥8 → {CellHigh, 點數格}；sum 不在 2~12 回傳 nil
func WinningCells(sum int) []int {
	cell, ok := numberCellBySum[sum]
	if !ok {
		return nil
	}
	switch {
	case sum == 7:
		return []int{Cell7}
	case sum <= 6:
		return []int{CellLow, cell}
	default:
		return []int{CellHigh, cell}
	}
}
