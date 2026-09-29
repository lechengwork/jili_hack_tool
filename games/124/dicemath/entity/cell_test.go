package entity

import (
	"reflect"
	"testing"
)

// TestWinningCells 測試「點數總和 → 中獎格」的對應是否正確。
//   - 總和 2~6：中 2~6 大區＋該點數格；總和 8~12：中 8~12 大區＋該點數格。
//   - 總和 7：只中「7」這一格(7 同時是大區也是號碼格)。
//   - 總和不在 2~12(例如 1、13)：回傳 nil。
func TestWinningCells(t *testing.T) {
	tests := []struct {
		sum  int
		want []int
	}{
		{2, []int{CellLow, Cell2}},
		{3, []int{CellLow, Cell3}},
		{4, []int{CellLow, Cell4}},
		{5, []int{CellLow, Cell5}},
		{6, []int{CellLow, Cell6}},
		{7, []int{Cell7}},
		{8, []int{CellHigh, Cell8}},
		{9, []int{CellHigh, Cell9}},
		{10, []int{CellHigh, Cell10}},
		{11, []int{CellHigh, Cell11}},
		{12, []int{CellHigh, Cell12}},
		{1, nil},
		{13, nil},
	}
	for _, tt := range tests {
		if got := WinningCells(tt.sum); !reflect.DeepEqual(got, tt.want) {
			t.Errorf("WinningCells(%d) = %v, want %v", tt.sum, got, tt.want)
		}
	}
}

// TestCellCombos_MatchesAllDicePairs 測試各格的中獎組合數表 CellCombos 是否正確。
//   - 窮舉兩顆骰子的 36 種組合，用 WinningCells 數出每格實際中獎幾次。
//   - 預期與 CellCombos(7:6、2~6:15、8~12:15、2:1 … 12:1)完全一致；這張表是所有 RTP 計算的基礎。
func TestCellCombos_MatchesAllDicePairs(t *testing.T) {
	var counts [CellCount]int
	for d1 := 1; d1 <= 6; d1++ {
		for d2 := 1; d2 <= 6; d2++ {
			for _, c := range WinningCells(d1 + d2) {
				counts[c]++
			}
		}
	}
	if counts != CellCombos {
		t.Errorf("counts from dice pairs = %v, CellCombos = %v", counts, CellCombos)
	}
}

// TestCellOrder_MatchesPacket 測試 13 格的索引順序與對方封包一致。
//   - 預期順序：7, 2~6, 8~12, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12(Cell7 = 0、CellLow = 1、CellHigh = 2 …)。
//   - 同時檢查 CellNames 與 CellCombos 也是這個順序；順序錯會讓下注、賠率、權重全部對錯格。
func TestCellOrder_MatchesPacket(t *testing.T) {
	wantNames := [CellCount]string{"7", "2~6", "8~12", "2", "3", "4", "5", "6", "8", "9", "10", "11", "12"}
	if CellNames != wantNames {
		t.Errorf("CellNames = %v, want %v", CellNames, wantNames)
	}
	if Cell7 != 0 || CellLow != 1 || CellHigh != 2 || Cell2 != 3 || Cell12 != 12 {
		t.Errorf("cell indices = Cell7:%d CellLow:%d CellHigh:%d Cell2:%d Cell12:%d, want 0 1 2 3 12",
			Cell7, CellLow, CellHigh, Cell2, Cell12)
	}
	wantCombos := [CellCount]int{6, 15, 15, 1, 2, 3, 4, 5, 5, 4, 3, 2, 1}
	if CellCombos != wantCombos {
		t.Errorf("CellCombos = %v, want %v", CellCombos, wantCombos)
	}
}
