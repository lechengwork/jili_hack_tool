package simulator

import (
	"math"
	"testing"

	"dicemath/entity"
	"dicemath/entity/setting"
	"dicemath/game"
)

var testBaseOdds = [entity.CellCount]int{4, 1, 1, 26, 12, 8, 6, 5, 5, 6, 8, 12, 26}

// TestSimulator_ConvergesToTheoryRTP 測試 simulator 的統計結果會收斂到理論值。
//   - 用簡化權重(每格 1/4 機率 j=2，NoExtraRate 25%)跑 20 萬局。
//   - 每格實測 RTP 與 TheoryRTP 差距 ≤ 0.05；點數 2~12 機率與 1/36~6/36 差距 ≤ 0.005；亮格數分佈總和為 1。
func TestSimulator_ConvergesToTheoryRTP(t *testing.T) {
	var weights [entity.CellCount][entity.MaxExtraMult]int
	for c := range weights {
		weights[c] = [entity.MaxExtraMult]int{3, 1} // 1/4 機率 j=2
	}
	litCounts := [entity.CellCount + 1]int{0: 1, 5: 1}
	m, err := game.NewDiceMath(9999, testBaseOdds, map[string]setting.VersionSetting{"0970": {NoExtraRate: 2500, ExtraWeights: weights, LitCountWeights: litCounts}})
	if err != nil {
		t.Fatalf("NewDiceMath() error = %v", err)
	}

	sim := NewSimulator(m.GetDiceResult, "0970")
	if err := sim.Simulate(200_000); err != nil {
		t.Fatalf("Simulate() error = %v", err)
	}
	if sim.Rounds != 200_000 {
		t.Errorf("Rounds = %d, want 200000", sim.Rounds)
	}

	theory := game.TheoryRTP(testBaseOdds, weights, 2500)
	const rtpTolerance = 0.05 // 20萬局的統計容忍範圍(號碼 2/12 標準差約 0.012)
	for c, got := range sim.CellRTP() {
		if math.Abs(got-theory[c]) > rtpTolerance {
			t.Errorf("cell %s: sim RTP = %.4f, theory = %.4f", entity.CellNames[c], got, theory[c])
		}
	}

	sumProb := sim.SumProb()
	for s := 2; s <= 12; s++ {
		want := float64(6-int(math.Abs(float64(s-7)))) / 36
		if math.Abs(sumProb[s]-want) > 0.005 {
			t.Errorf("sum %d: sim prob = %.4f, want %.4f", s, sumProb[s], want)
		}
	}

	var total float64
	for _, p := range sim.LitCountProb() {
		total += p
	}
	if math.Abs(total-1) > 1e-9 {
		t.Errorf("LitCountProb() sums to %.6f, want 1", total)
	}
}

// TestSimulator_PropagatesVersionError 測試 simulator 遇到不支援的版本時，會把 GetDiceResult 的 error 往上回傳，而不是默默跑完。
func TestSimulator_PropagatesVersionError(t *testing.T) {
	var weights [entity.CellCount][entity.MaxExtraMult]int
	for c := range weights {
		weights[c][0] = 1
	}
	m, err := game.NewDiceMath(9999, testBaseOdds, map[string]setting.VersionSetting{"0970": {ExtraWeights: weights, LitCountWeights: [entity.CellCount + 1]int{0: 1}}})
	if err != nil {
		t.Fatalf("NewDiceMath() error = %v", err)
	}
	if err := NewSimulator(m.GetDiceResult, "0800").Simulate(1); err == nil {
		t.Error("Simulate() with unsupported version error = nil, want error")
	}
}
