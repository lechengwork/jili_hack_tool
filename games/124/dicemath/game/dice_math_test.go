package game

import (
	"testing"

	"dicemath/entity"
	"dicemath/entity/setting"
)

// testBaseOdds 4102 的基礎淨賠率
var testBaseOdds = [entity.CellCount]int{4, 1, 1, 26, 12, 8, 6, 5, 5, 6, 8, 12, 26}

// fillWeights 13 格都用同一組權重
func fillWeights(w [entity.MaxExtraMult]int) [entity.CellCount][entity.MaxExtraMult]int {
	var table [entity.CellCount][entity.MaxExtraMult]int
	for c := range table {
		table[c] = w
	}
	return table
}

// uniformLitCounts K=0..13 權重都是 1(注入值 v 即得 K=v)
func uniformLitCounts() [entity.CellCount + 1]int {
	var k [entity.CellCount + 1]int
	for i := range k {
		k[i] = 1
	}
	return k
}

// testSettings 只有 "0970" 一個版本的設定
func testSettings(weights [entity.CellCount][entity.MaxExtraMult]int, litCounts [entity.CellCount + 1]int, noExtraRate int) map[string]setting.VersionSetting {
	return map[string]setting.VersionSetting{"0970": {NoExtraRate: noExtraRate, ExtraWeights: weights, LitCountWeights: litCounts}}
}

// TestNewDiceMath_Valid 測試用合法設定建立引擎會成功，並正確推導假演出的挑格權重。
//   - GetMachineID 回傳建立時給的機台編號。
//   - 權重 {3,1}(亮的機率 1/4)的格，挑格權重 = 250000(1/4 × 10⁶)。
//   - 權重 {1}(永遠不亮)的格，挑格權重 = 0，之後永遠不會被挑去假演出。
func TestNewDiceMath_Valid(t *testing.T) {
	weights := fillWeights([entity.MaxExtraMult]int{3, 1})
	weights[entity.Cell3] = [entity.MaxExtraMult]int{1} // 永不亮

	m, err := NewDiceMath(9999, testBaseOdds, testSettings(weights, uniformLitCounts(), 0))
	if err != nil {
		t.Fatalf("NewDiceMath() error = %v, want nil", err)
	}
	if got := m.GetMachineID(); got != 9999 {
		t.Errorf("GetMachineID() = %d, want 9999", got)
	}

	picks := m.versions["0970"].fakePickWeights
	if picks[entity.Cell2] != 250_000 { // P(j≥2) = 1/4
		t.Errorf("fakePickWeights[Cell2] = %d, want 250000", picks[entity.Cell2])
	}
	if picks[entity.Cell3] != 0 {
		t.Errorf("fakePickWeights[Cell3] = %d, want 0 (never lit)", picks[entity.Cell3])
	}
}

// TestNewDiceMath_WeightsUsedAsIs 測試 ExtraWeights 照設定原樣使用，不會因為 NoExtraRate 被改動。
//   - 設定 NoExtraRate = 2500，引擎內部保存的權重必須與設定值完全相同。
//   - 同時確認 NoExtraRate 有被正確保存。
func TestNewDiceMath_WeightsUsedAsIs(t *testing.T) {
	w := [entity.MaxExtraMult]int{717850, 211612, 42323, 0, 22572, 0, 0, 0, 0, 5643}
	m, err := NewDiceMath(9999, testBaseOdds, testSettings(fillWeights(w), uniformLitCounts(), 2500))
	if err != nil {
		t.Fatalf("NewDiceMath() error = %v, want nil", err)
	}
	vt := m.versions["0970"]
	if vt.extraWeights[entity.CellLow] != w {
		t.Errorf("extraWeights = %v, want %v (as configured)", vt.extraWeights[entity.CellLow], w)
	}
	if vt.noExtraRate != 2500 {
		t.Errorf("noExtraRate = %d, want 2500", vt.noExtraRate)
	}
}

// TestNewDiceMath_InvalidSettings 測試各種錯誤設定在建立引擎時就回傳 error(不讓錯誤設定上線)。
//   - 版本不在白名單、設定是空的。
//   - 某格權重總和為 0、權重為負數。
//   - 基礎賠率為 0。
//   - 亮格數 K 表總和為 0。
//   - NoExtraRate 為負數、或 ≥ 10000(100%)。
func TestNewDiceMath_InvalidSettings(t *testing.T) {
	good := fillWeights([entity.MaxExtraMult]int{1, 1})

	zeroCell := good
	zeroCell[entity.Cell5] = [entity.MaxExtraMult]int{}

	negativeCell := good
	negativeCell[entity.Cell5] = [entity.MaxExtraMult]int{2, -1}

	badBaseOdds := testBaseOdds
	badBaseOdds[entity.Cell7] = 0

	tests := []struct {
		name     string
		baseOdds [entity.CellCount]int
		settings map[string]setting.VersionSetting
	}{
		{"version not in allow list", testBaseOdds, map[string]setting.VersionSetting{"9999": {ExtraWeights: good, LitCountWeights: uniformLitCounts()}}},
		{"empty settings map", testBaseOdds, map[string]setting.VersionSetting{}},
		{"cell weights sum zero", testBaseOdds, testSettings(zeroCell, uniformLitCounts(), 0)},
		{"negative weight", testBaseOdds, testSettings(negativeCell, uniformLitCounts(), 0)},
		{"base odds zero", badBaseOdds, testSettings(good, uniformLitCounts(), 0)},
		{"lit count weights sum zero", testBaseOdds, testSettings(good, [entity.CellCount + 1]int{}, 0)},
		{"NoExtraRate negative", testBaseOdds, testSettings(good, uniformLitCounts(), -1)},
		{"NoExtraRate 100%", testBaseOdds, testSettings(good, uniformLitCounts(), 10000)},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if _, err := NewDiceMath(9999, tt.baseOdds, tt.settings); err == nil {
				t.Error("NewDiceMath() error = nil, want error")
			}
		})
	}
}
