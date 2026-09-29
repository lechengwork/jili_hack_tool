package game

import (
	"math"
	"testing"

	"dicemath/entity"
)

// theoryTestBaseOdds 4102 的基礎淨賠率(測試內自帶一份，避免依賴 g4102)
var theoryTestBaseOdds = [entity.CellCount]int{4, 1, 1, 26, 12, 8, 6, 5, 5, 6, 8, 12, 26}

// TestTheoryRTP_NoExtraEqualsBaseRTP 測試完全沒有 EXTRA 時，TheoryRTP 算出的就是基礎 RTP。
//   - 每格權重只有 j = 1。
//   - 預期 13 格 RTP = 組合數/36 × (淨賠率+1)：例如 7、2~6、6、8 為 30/36(83.33%)，3、11 為 26/36(72.22%)。
func TestTheoryRTP_NoExtraEqualsBaseRTP(t *testing.T) {
	var weights [entity.CellCount][entity.MaxExtraMult]int
	for c := range weights {
		weights[c][0] = 1 // 永遠 j=1
	}
	want := [entity.CellCount]float64{
		30.0 / 36, 30.0 / 36, 30.0 / 36, // 7, 2~6, 8~12
		27.0 / 36, 26.0 / 36, 27.0 / 36, 28.0 / 36, 30.0 / 36, // 2, 3, 4, 5, 6
		30.0 / 36, 28.0 / 36, 27.0 / 36, 26.0 / 36, 27.0 / 36, // 8, 9, 10, 11, 12
	}
	got := TheoryRTP(theoryTestBaseOdds, weights, 0)
	for c := range want {
		if math.Abs(got[c]-want[c]) > 1e-12 {
			t.Errorf("cell %s: TheoryRTP = %.10f, want %.10f", entity.CellNames[c], got[c], want[c])
		}
	}
}

// TestTheoryRTP_WithExtra 測試有 EXTRA 時 TheoryRTP 的期望值計算。
//   - 「6」格權重 {1,1}：一半 j=1、一半 j=2 → E[淨賠率] = 1.5 × 5 = 7.5。
//   - 預期 RTP = 5/36 × (7.5+1)。
func TestTheoryRTP_WithExtra(t *testing.T) {
	var weights [entity.CellCount][entity.MaxExtraMult]int
	for c := range weights {
		weights[c][0] = 1
	}
	weights[entity.Cell6] = [entity.MaxExtraMult]int{1, 1} // 一半 j=1、一半 j=2 → E[淨賠率] = 1.5 × 5 = 7.5

	got := TheoryRTP(theoryTestBaseOdds, weights, 0)
	want := 5.0 / 36 * (7.5 + 1)
	if math.Abs(got[entity.Cell6]-want) > 1e-12 {
		t.Errorf("cell 6: TheoryRTP = %.10f, want %.10f", got[entity.Cell6], want)
	}
}

// TestTheoryRTP_MultiBucketUpToMaxJ 測試 j 分散在多個倍數(含上限 j = 10)時，TheoryRTP 仍計算正確。
//   - 「2」格 j ∈ {1,3,10} 各 1/3 → E[j] = 14/3；「7」格 j = 1~10 平均分佈 → E[j] = 5.5。
//   - 用來抓「權重陣列 index 與 j 差 1」這類錯誤(index i 對應 j = i+1)。
func TestTheoryRTP_MultiBucketUpToMaxJ(t *testing.T) {
	var weights [entity.CellCount][entity.MaxExtraMult]int
	for c := range weights {
		weights[c][0] = 1 // 永遠 j=1
	}
	// Cell2：j ∈ {1,3,10} 各權重 1 → E[j] = (1+3+10)/3 = 14/3
	weights[entity.Cell2] = [entity.MaxExtraMult]int{1, 0, 1, 0, 0, 0, 0, 0, 0, 1}
	// Cell7：j=1..10 權重都 1 → E[j] = 5.5
	weights[entity.Cell7] = [entity.MaxExtraMult]int{1, 1, 1, 1, 1, 1, 1, 1, 1, 1}

	got := TheoryRTP(theoryTestBaseOdds, weights, 0)

	wantCell2 := 1.0 / 36 * (14.0/3*26 + 1)
	if math.Abs(got[entity.Cell2]-wantCell2) > 1e-12 {
		t.Errorf("cell 2: TheoryRTP = %.10f, want %.10f", got[entity.Cell2], wantCell2)
	}

	wantCell7 := 6.0 / 36 * (5.5*4 + 1)
	if math.Abs(got[entity.Cell7]-wantCell7) > 1e-12 {
		t.Errorf("cell 7: TheoryRTP = %.10f, want %.10f", got[entity.Cell7], wantCell7)
	}
}

// TestTheoryRTP_ZeroWeightsReturnsZero 測試權重全為 0 的格，TheoryRTP 回傳 0 而不是除以 0 出錯。
//   - 這種表在建立引擎時就會被擋下，這裡只確認 TheoryRTP 本身不會壞掉。
func TestTheoryRTP_ZeroWeightsReturnsZero(t *testing.T) {
	var weights [entity.CellCount][entity.MaxExtraMult]int
	got := TheoryRTP(theoryTestBaseOdds, weights, 0)
	for c := range got {
		if got[c] != 0 {
			t.Errorf("cell %s: TheoryRTP = %v, want 0 for zero weights", entity.CellNames[c], got[c])
		}
	}
}

// TestTheoryRTP_NoExtraRate 測試 TheoryRTP 有把 NoExtraRate 算進去。
//   - NoExtraRate = 25%，「6」格有 EXTRA 的局 E'[j] = 1.5 → 整體 E[j] = 0.25 × 1 + 0.75 × 1.5。
//   - 永遠 j = 1 的格(7)不受 NoExtraRate 影響，維持基礎 RTP。
func TestTheoryRTP_NoExtraRate(t *testing.T) {
	var weights [entity.CellCount][entity.MaxExtraMult]int
	for c := range weights {
		weights[c][0] = 1
	}
	weights[entity.Cell6] = [entity.MaxExtraMult]int{1, 1} // 有 EXTRA 的局 E'[j] = 1.5

	got := TheoryRTP(theoryTestBaseOdds, weights, 2500)
	want := 5.0 / 36 * ((0.25+0.75*1.5)*5 + 1)
	if math.Abs(got[entity.Cell6]-want) > 1e-12 {
		t.Errorf("cell 6: TheoryRTP = %.10f, want %.10f", got[entity.Cell6], want)
	}
	if base := 30.0 / 36; math.Abs(got[entity.Cell7]-base) > 1e-12 { // 永遠 j=1 的格不受 NoExtraRate 影響
		t.Errorf("cell 7: TheoryRTP = %.10f, want %.10f", got[entity.Cell7], base)
	}
}
