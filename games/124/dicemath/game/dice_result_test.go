package game

import (
	"fmt"
	"reflect"
	"sync"
	"testing"

	"dicemath/entity"
	"dicemath/entity/result"
	"dicemath/randomNumber"
)

// newInjectedMath 建立注入固定 RNG 序列的機台；回傳的 *RNG 指標在 GetDiceResult 後可檢查消耗量
func newInjectedMath(t *testing.T, weights [entity.CellCount][entity.MaxExtraMult]int, seq []int) (*DiceMath, **randomNumber.RNG) {
	t.Helper()
	return newInjectedMathWithRate(t, weights, 0, seq)
}

// newInjectedMathWithRate 同 newInjectedMath，可指定 NoExtraRate
func newInjectedMathWithRate(t *testing.T, weights [entity.CellCount][entity.MaxExtraMult]int, noExtraRate int, seq []int) (*DiceMath, **randomNumber.RNG) {
	t.Helper()
	m, err := NewDiceMath(9999, testBaseOdds, testSettings(weights, uniformLitCounts(), noExtraRate))
	if err != nil {
		t.Fatalf("NewDiceMath() error = %v", err)
	}
	var used *randomNumber.RNG
	m.newRng = func() *randomNumber.RNG {
		r := randomNumber.NewRNG()
		r.SetIntList(append([]int(nil), seq...))
		used = r
		return r
	}
	return m, &used
}

// seq 組合注入序列：本局有無 EXTRA(固定注入 gateExtra = 有 EXTRA)、骰子(d1,d2)、
// 13 格真實 EXTRA、K、其後假演出
func seq(d1, d2 int, extras [entity.CellCount]int, k int, fakes ...int) []int {
	s := []int{gateExtra, d1 - 1, d2 - 1}
	s = append(s, extras[:]...)
	s = append(s, k)
	return append(s, fakes...)
}

// gateExtra 注入到「本局有無 EXTRA」的值：9999 ≥ 任何合法 NoExtraRate(< 10000)，必為有 EXTRA 的局
const gateExtra = 9999

func assertConsumed(t *testing.T, used **randomNumber.RNG, want int) {
	t.Helper()
	if got := len((*used).CopyUsedRNG()); got != want {
		t.Errorf("RNG consumed %d values, want %d", got, want)
	}
}

func litCount(out *result.DiceOutput) int {
	n := 0
	for _, j := range out.ExtraMults {
		if j > 1 {
			n++
		}
	}
	return n
}

// TestGetDiceResult_NoExtra 測試沒有任何 EXTRA 時的開骰與結算。
//   - 注入骰子 2、3(總和 5)，13 格都不亮、K = 0。
//   - 預期 Die1/Die2/Sum 正確、ExtraMults 全為 1、FinalOdds = BaseOdds。
//   - 派彩：押 5 格 10 → 10 × (6+1)；押 2~6 格 20 → 20 × (1+1)；押 7 格沒中 → 0。
//   - 亂數消耗數量與注入序列一致。
func TestGetDiceResult_NoExtra(t *testing.T) {
	s := seq(2, 3, [entity.CellCount]int{}, 0)
	m, used := newInjectedMath(t, fillWeights([entity.MaxExtraMult]int{1, 1}), s)

	in := result.DiceInput{Version: "0970"}
	in.Bets[entity.Cell5] = 10
	in.Bets[entity.CellLow] = 20
	in.Bets[entity.Cell7] = 5

	out, err := m.GetDiceResult(&in)
	if err != nil {
		t.Fatalf("GetDiceResult() error = %v", err)
	}
	if out.Die1 != 2 || out.Die2 != 3 || out.Sum != 5 {
		t.Errorf("Die1, Die2, Sum = %d, %d, %d, want 2, 3, 5", out.Die1, out.Die2, out.Sum)
	}
	if litCount(out) != 0 {
		t.Errorf("ExtraMults = %v, want all 1", out.ExtraMults)
	}
	if out.BaseOdds != testBaseOdds || out.FinalOdds != testBaseOdds {
		t.Errorf("BaseOdds = %v, FinalOdds = %v, want both %v", out.BaseOdds, out.FinalOdds, testBaseOdds)
	}
	if want := int64(10*7 + 20*2); out.TotalWin != want { // 5 淨賠率 6、2~6 淨賠率 1；7 沒中
		t.Errorf("TotalWin = %d, want %d", out.TotalWin, want)
	}
	assertConsumed(t, used, len(s))
}

// TestGetDiceResult_RealExtraOnWinningCell 測試真實 EXTRA 落在中獎格時，用升級後的賠率派彩。
//   - 注入骰子 1、1(總和 2)，「2」格抽到 j = 2。
//   - 預期 ExtraMults[2] = 2、FinalOdds[2] = 52(2 × 26)。
//   - 押 10 → TotalWin = 10 × (52+1) = 530(含本金)。
func TestGetDiceResult_RealExtraOnWinningCell(t *testing.T) {
	var extras [entity.CellCount]int
	extras[entity.Cell2] = 1 // j=2
	s := seq(1, 1, extras, 0)
	m, used := newInjectedMath(t, fillWeights([entity.MaxExtraMult]int{1, 1}), s)

	in := result.DiceInput{Version: "0970"}
	in.Bets[entity.Cell2] = 10

	out, err := m.GetDiceResult(&in)
	if err != nil {
		t.Fatalf("GetDiceResult() error = %v", err)
	}
	if out.ExtraMults[entity.Cell2] != 2 || out.FinalOdds[entity.Cell2] != 52 {
		t.Errorf("Cell2 ExtraMults, FinalOdds = %d, %d, want 2, 52", out.ExtraMults[entity.Cell2], out.FinalOdds[entity.Cell2])
	}
	if out.TotalWin != 10*53 {
		t.Errorf("TotalWin = %d, want 530", out.TotalWin)
	}
	assertConsumed(t, used, len(s))
}

// TestGetDiceResult_SumSevenOnlyCell7Wins 測試開出 7 時只有「7」這一格中獎。
//   - 注入骰子 3、4(總和 7)，2~6、7、8~12 各押 10。
//   - 預期只有 7 格派彩：10 × (4+1) = 50；2~6、8~12 都不中。
func TestGetDiceResult_SumSevenOnlyCell7Wins(t *testing.T) {
	s := seq(3, 4, [entity.CellCount]int{}, 0)
	m, _ := newInjectedMath(t, fillWeights([entity.MaxExtraMult]int{1, 1}), s)

	in := result.DiceInput{Version: "0970"}
	in.Bets[entity.CellLow] = 10
	in.Bets[entity.Cell7] = 10
	in.Bets[entity.CellHigh] = 10

	out, err := m.GetDiceResult(&in)
	if err != nil {
		t.Fatalf("GetDiceResult() error = %v", err)
	}
	if out.TotalWin != 10*5 {
		t.Errorf("TotalWin = %d, want 50 (only cell 7 wins)", out.TotalWin)
	}
}

// TestGetDiceResult_FakeExtraSkipsWinningCellsAndUsesExtraDistribution 測試假演出不會落在中獎格，且假演出的倍數取自該格的權重表。
//   - 權重 {1,0,1}：真實只會是 j=1 或 j=3；注入全部不亮、K = 13(要求補滿)。
//   - 開 1、1(中獎格為 2~6 與 2)：這兩格必須維持不亮(j = 1)。
//   - 其他 11 格全部被補上假演出，倍數必為 j = 3(權重表 j≥2 部分只有 j=3)。
//   - 2~6 沒被假演出，派彩維持基礎賠率：10 × (1+1) = 20。
func TestGetDiceResult_FakeExtraSkipsWinningCellsAndUsesExtraDistribution(t *testing.T) {
	// 每格 {1,0,1}：真實 j=1 或 j=3；假演出 j 取 [0,1,...] → 必為 j=3
	fakes := []int{}
	for i := 0; i < 11; i++ { // 中獎格 2~6、2 以外的 11 格
		fakes = append(fakes, 0, 0) // 挑候選第一個、j=3
	}
	s := seq(1, 1, [entity.CellCount]int{}, 13, fakes...)
	m, used := newInjectedMath(t, fillWeights([entity.MaxExtraMult]int{1, 0, 1}), s)

	in := result.DiceInput{Version: "0970"}
	in.Bets[entity.CellLow] = 10

	out, err := m.GetDiceResult(&in)
	if err != nil {
		t.Fatalf("GetDiceResult() error = %v", err)
	}
	for c := 0; c < entity.CellCount; c++ {
		isWinning := c == entity.CellLow || c == entity.Cell2
		if isWinning && out.ExtraMults[c] != 1 {
			t.Errorf("winning cell %s got fake ExtraMults %d, want 1", entity.CellNames[c], out.ExtraMults[c])
		}
		if !isWinning && out.ExtraMults[c] != 3 {
			t.Errorf("cell %s ExtraMults = %d, want 3 (fake j=3)", entity.CellNames[c], out.ExtraMults[c])
		}
		if want := out.ExtraMults[c] * testBaseOdds[c]; out.FinalOdds[c] != want {
			t.Errorf("cell %s FinalOdds = %d, want %d", entity.CellNames[c], out.FinalOdds[c], want)
		}
	}
	if out.TotalWin != 10*2 { // 2~6 沒被假演出，維持淨賠率 1
		t.Errorf("TotalWin = %d, want 20", out.TotalWin)
	}
	assertConsumed(t, used, len(s))
}

// TestGetDiceResult_FakeFillsOnlyUpToK 測試假演出只補到畫面總亮格數 K 為止，且挑格順序正確。
//   - 「12」格真實亮 j = 2(真實亮格 r = 1)，K = 3 → 只再補 2 格。
//   - 候選格依索引排序，注入 0 → 依序挑到「7」與「8~12」。
//   - 預期 ExtraMults：12、7、8~12 為 2，其餘為 1；UsedRNG 與注入序列完全相同。
func TestGetDiceResult_FakeFillsOnlyUpToK(t *testing.T) {
	var extras [entity.CellCount]int
	extras[entity.Cell12] = 1 // 真實亮 12，r=1
	// K=3 → 補 2 格；候選依索引排序為 7, 8~12, 3, 4, ...（2~6、2 中獎，12 已亮）
	s := seq(1, 1, extras, 3, 0, 0, 0, 0)
	m, used := newInjectedMath(t, fillWeights([entity.MaxExtraMult]int{1, 1}), s)

	in := result.DiceInput{Version: "0970"}
	in.Bets[entity.Cell2] = 1

	out, err := m.GetDiceResult(&in)
	if err != nil {
		t.Fatalf("GetDiceResult() error = %v", err)
	}
	var want [entity.CellCount]int
	for c := range want {
		want[c] = 1
	}
	want[entity.Cell12] = 2
	want[entity.Cell7] = 2
	want[entity.CellHigh] = 2
	if out.ExtraMults != want {
		t.Errorf("ExtraMults = %v, want %v", out.ExtraMults, want)
	}
	assertConsumed(t, used, len(s))
	if !reflect.DeepEqual(out.UsedRNG, s) {
		t.Errorf("UsedRNG = %v, want %v", out.UsedRNG, s)
	}
}

// TestGetDiceResult_NoFakeWhenRealLitReachesK 測試真實亮格數已達到 K 時不再補假演出。
//   - 13 格全部真實亮(r = 13)，K = 5。
//   - 預期畫面亮 13 格，且不再多消耗任何亂數(沒有進行假演出)。
func TestGetDiceResult_NoFakeWhenRealLitReachesK(t *testing.T) {
	var extras [entity.CellCount]int
	for c := range extras {
		extras[c] = 1 // 13 格全部真實亮
	}
	s := seq(1, 1, extras, 5)
	m, used := newInjectedMath(t, fillWeights([entity.MaxExtraMult]int{1, 1}), s)

	in := result.DiceInput{Version: "0970"}
	in.Bets[entity.Cell2] = 1

	out, err := m.GetDiceResult(&in)
	if err != nil {
		t.Fatalf("GetDiceResult() error = %v", err)
	}
	if litCount(out) != 13 {
		t.Errorf("lit count = %d, want 13", litCount(out))
	}
	assertConsumed(t, used, len(s)) // r ≥ K，不得再消耗 RNG
}

// TestGetDiceResult_FakeSkipsZeroPickWeightCells 測試挑格權重為 0 的格子永遠不會被挑去假演出。
//   - 「3」格權重 {1}(永遠不亮 → 挑格權重 0)，K = 13(要求補滿)。
//   - 預期「3」格維持不亮，其餘 10 個非中獎格被補滿(總亮 10 格)。
func TestGetDiceResult_FakeSkipsZeroPickWeightCells(t *testing.T) {
	weights := fillWeights([entity.MaxExtraMult]int{1, 1})
	weights[entity.Cell3] = [entity.MaxExtraMult]int{1} // 永不亮 → 挑格權重 0
	fakes := []int{}
	for i := 0; i < 10; i++ { // 11 個非中獎格扣掉 Cell3
		fakes = append(fakes, 0, 0)
	}
	s := seq(1, 1, [entity.CellCount]int{}, 13, fakes...)
	m, used := newInjectedMath(t, weights, s)

	in := result.DiceInput{Version: "0970"}
	in.Bets[entity.Cell2] = 1

	out, err := m.GetDiceResult(&in)
	if err != nil {
		t.Fatalf("GetDiceResult() error = %v", err)
	}
	if out.ExtraMults[entity.Cell3] != 1 {
		t.Errorf("Cell3 ExtraMults = %d, want 1 (pick weight 0)", out.ExtraMults[entity.Cell3])
	}
	if litCount(out) != 10 {
		t.Errorf("lit count = %d, want 10", litCount(out))
	}
	assertConsumed(t, used, len(s))
}

// TestGetDiceResult_UsedRNGReplaysRound 測試 UsedRNG 能完整重現一局(稽核重現)。
//   - 用真實亂數跑一局取得 UsedRNG，再把 UsedRNG 注入重跑一次。
//   - 兩次輸出必須完全相同(含 UsedRNG 本身)；重複 200 局，涵蓋不發 EXTRA、真實 EXTRA、假演出各種情況。
func TestGetDiceResult_UsedRNGReplaysRound(t *testing.T) {
	m, err := NewDiceMath(9999, testBaseOdds, testSettings(fillWeights([entity.MaxExtraMult]int{2, 1, 1}), uniformLitCounts(), 2500))
	if err != nil {
		t.Fatalf("NewDiceMath() error = %v", err)
	}

	in := result.DiceInput{Version: "0970"}
	in.Bets[entity.Cell7] = 1

	for round := 1; round <= 200; round++ {
		m.newRng = randomNumber.NewRNG

		out1, err := m.GetDiceResult(&in)
		if err != nil {
			t.Fatalf("round %d: GetDiceResult() error = %v", round, err)
		}

		replaySeq := append([]int(nil), out1.UsedRNG...)
		m.newRng = func() *randomNumber.RNG {
			r := randomNumber.NewRNG()
			r.SetIntList(replaySeq)
			return r
		}

		out2, err := m.GetDiceResult(&in)
		if err != nil {
			t.Fatalf("round %d: replay GetDiceResult() error = %v", round, err)
		}

		if !reflect.DeepEqual(out1, out2) {
			t.Fatalf("round %d: replay mismatch\nout1 = %+v\nout2 = %+v", round, out1, out2)
		}
	}
}

// TestGetDiceResult_ConcurrentCallsAreSafe 測試多個 goroutine 同時呼叫 GetDiceResult 是安全的，且每局結果都合法。
//   - 8 個 goroutine × 各 2000 局，共用同一個 DiceMath。
//   - 每局檢查：骰子 1~6 且 Sum = Die1 + Die2；ExtraMults 在 1~10；FinalOdds = ExtraMults × BaseOdds；
//     TotalWin 與中獎格重算一致；UsedRNG 長度為 3(不發 EXTRA 的局，且全不亮)或 ≥ 17(有 EXTRA 的局)。
//   - 這台環境沒有 cgo，跑不了 -race；到有 cgo 的環境可以再用 `go test -race` 補跑。
func TestGetDiceResult_ConcurrentCallsAreSafe(t *testing.T) {
	m, err := NewDiceMath(9999, testBaseOdds, testSettings(fillWeights([entity.MaxExtraMult]int{2, 1, 0, 0, 1}), uniformLitCounts(), 2500))
	if err != nil {
		t.Fatalf("NewDiceMath() error = %v", err)
	}

	in := result.DiceInput{Version: "0970"}
	for c := range in.Bets {
		in.Bets[c] = 1
	}

	const goroutines = 8
	const callsPerGoroutine = 2000

	var wg sync.WaitGroup
	errs := make(chan string, goroutines*callsPerGoroutine)

	for g := 0; g < goroutines; g++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < callsPerGoroutine; i++ {
				out, err := m.GetDiceResult(&in)
				if err != nil {
					errs <- fmt.Sprintf("GetDiceResult() error = %v", err)
					continue
				}
				for _, d := range [2]int{out.Die1, out.Die2} {
					if d < 1 || d > 6 {
						errs <- fmt.Sprintf("die out of range: %d", d)
					}
				}
				if out.Sum != out.Die1+out.Die2 {
					errs <- fmt.Sprintf("Sum = %d, want %d", out.Sum, out.Die1+out.Die2)
				}
				for c := 0; c < entity.CellCount; c++ {
					j := out.ExtraMults[c]
					if j < 1 || j > entity.MaxExtraMult {
						errs <- fmt.Sprintf("cell %d: ExtraMults=%d out of range [1,%d]", c, j, entity.MaxExtraMult)
						continue
					}
					if out.FinalOdds[c] != j*out.BaseOdds[c] {
						errs <- fmt.Sprintf("cell %d: FinalOdds=%d, want ExtraMults×BaseOdds=%d", c, out.FinalOdds[c], j*out.BaseOdds[c])
					}
				}
				var wantWin int64
				for _, c := range entity.WinningCells(out.Sum) {
					wantWin += in.Bets[c] * int64(out.FinalOdds[c]+1)
				}
				if out.TotalWin != wantWin {
					errs <- fmt.Sprintf("TotalWin = %d, want %d", out.TotalWin, wantWin)
				}
				// 不發 EXTRA 的局只消耗「有無 EXTRA」＋兩顆骰子(3 個)且 13 格全不亮；
				// 有 EXTRA 的局至少再消耗 13 格真實 EXTRA ＋ K
				switch n := len(out.UsedRNG); {
				case n == 3:
					if lit := litCount(out); lit != 0 {
						errs <- fmt.Sprintf("no-extra round (len(UsedRNG)=3) but %d cells lit", lit)
					}
				case n < 3+entity.CellCount+1:
					errs <- fmt.Sprintf("len(UsedRNG) = %d, want 3 (no-extra round) or >= %d", n, 3+entity.CellCount+1)
				}
			}
		}()
	}

	wg.Wait()
	close(errs)

	reported := 0
	for msg := range errs {
		if reported >= 10 {
			continue
		}
		t.Error(msg)
		reported++
	}
}

// TestGetDiceResult_NoExtraRound 測試抽中 NoExtraRate(整局不發 EXTRA)時的行為。
//   - NoExtraRate = 50%，注入「有無 EXTRA」= 0(< 5000 → 不發)。
//   - 預期 13 格全不亮、FinalOdds = BaseOdds、不做假演出。
//   - 押「2」格 10、開 1、1 → 照基礎賠率派彩 10 × 27 = 270。
//   - 只消耗 3 個亂數(有無 EXTRA ＋ 兩顆骰子)。
func TestGetDiceResult_NoExtraRound(t *testing.T) {
	s := []int{0, 0, 0} // gate 0 < 5000 → 不發 EXTRA；骰子 1, 1
	m, used := newInjectedMathWithRate(t, fillWeights([entity.MaxExtraMult]int{1, 1}), 5000, s)

	in := result.DiceInput{Version: "0970"}
	in.Bets[entity.Cell2] = 10

	out, err := m.GetDiceResult(&in)
	if err != nil {
		t.Fatalf("GetDiceResult() error = %v", err)
	}
	if litCount(out) != 0 {
		t.Errorf("ExtraMults = %v, want all 1", out.ExtraMults)
	}
	if out.FinalOdds != testBaseOdds {
		t.Errorf("FinalOdds = %v, want %v", out.FinalOdds, testBaseOdds)
	}
	if out.TotalWin != 10*27 {
		t.Errorf("TotalWin = %d, want 270", out.TotalWin)
	}
	assertConsumed(t, used, len(s))
}

// TestGetDiceResult_ExtraRoundUsesWeightsAsIs 測試有 EXTRA 的局照設定的權重抽倍數。
//   - NoExtraRate = 50%，注入「有無 EXTRA」= 5000(邊界值，≥ 5000 → 有 EXTRA)。
//   - 權重 {1,1}、注入 1 → 「2」格必須抽到 j = 2。
func TestGetDiceResult_ExtraRoundUsesWeightsAsIs(t *testing.T) {
	var extras [entity.CellCount]int
	extras[entity.Cell2] = 1
	s := seq(1, 1, extras, 0)
	s[0] = 5000 // gate 5000 ≥ 5000 → 有 EXTRA(邊界值)
	m, used := newInjectedMathWithRate(t, fillWeights([entity.MaxExtraMult]int{1, 1}), 5000, s)

	in := result.DiceInput{Version: "0970"}
	in.Bets[entity.Cell2] = 1

	out, err := m.GetDiceResult(&in)
	if err != nil {
		t.Fatalf("GetDiceResult() error = %v", err)
	}
	if out.ExtraMults[entity.Cell2] != 2 {
		t.Errorf("Cell2 ExtraMults = %d, want 2", out.ExtraMults[entity.Cell2])
	}
	assertConsumed(t, used, len(s))
}

// TestGetDiceResult_Errors 測試不合法的輸入會回傳 error。
//   - 版本不支援(0800)、版本空白。
//   - 輸入為 nil。
//   - 任一格下注為負數。
//   - 13 格下注全為 0。
func TestGetDiceResult_Errors(t *testing.T) {
	m, _ := newInjectedMath(t, fillWeights([entity.MaxExtraMult]int{1, 1}), nil)

	unsupported := result.DiceInput{Version: "0800"}
	unsupported.Bets[entity.Cell7] = 1

	noVersion := result.DiceInput{}
	noVersion.Bets[entity.Cell7] = 1

	negative := result.DiceInput{Version: "0970"}
	negative.Bets[entity.Cell7] = 1
	negative.Bets[entity.Cell8] = -1

	tests := []struct {
		name string
		in   *result.DiceInput
	}{
		{"unsupported version", &unsupported},
		{"empty version", &noVersion},
		{"nil input", nil},
		{"negative bet", &negative},
		{"all bets zero", &result.DiceInput{Version: "0970"}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if _, err := m.GetDiceResult(tt.in); err == nil {
				t.Error("GetDiceResult() error = nil, want error")
			}
		})
	}
}
