package game

import (
	"encoding/json"
	"errors"
	"math"
	"os"
	"sync"
	"testing"

	"pappumath/entity"
	"pappumath/entity/result"
	"pappumath/entity/setting"
)

func outcome(a entity.Area, odds int64) result.Outcome {
	o := result.Outcome{Winner: a, Pic: int32(a)}
	if a.Valid() {
		o.ReturnOdds[a.Index()] = odds
	}
	return o
}
func engine(t *testing.T) *PappuMath {
	t.Helper()
	m, err := NewPappuMath(map[string]setting.VersionSetting{"fixture": {Outcomes: []setting.WeightedOutcome{
		{Weight: 2, Outcome: outcome(entity.AreaUmbrella, 20)},
		{Weight: 3, Outcome: outcome(entity.AreaPigeon, 10)},
	}}})
	if err != nil {
		t.Fatal(err)
	}
	return m
}

// Net odds 1:2 means profit 2 plus stake 1 -> gross 3. Gross x2 means return 2.
func TestNetVersusGrossOdds(t *testing.T) {
	for _, tc := range []struct{ net, want int64 }{{1, 2}, {2, 3}, {9, 10}, {19, 20}} {
		got, err := NetToReturnOdds(tc.net)
		if err != nil || got != tc.want {
			t.Fatalf("net %d => %d,%v; want gross %d", tc.net, got, err, tc.want)
		}
	}
	for _, bad := range []int64{-1, math.MaxInt64} {
		if _, err := NetToReturnOdds(bad); err == nil {
			t.Fatal("accepted invalid net odds")
		}
	}
	var bets entity.Bets
	bets[entity.AreaWhippingTop.Index()] = 200000
	out, err := Settle(bets, outcome(entity.AreaWhippingTop, 10))
	if err != nil || out.TotalWin != 2000000 || out.NetWin != 1800000 {
		t.Fatalf("stake double-counted: %+v, %v", out, err)
	}
}

func TestZeroMeansBaseAndBonusIsFinalReturn(t *testing.T) {
	var bets entity.Bets
	bets[0] = 100
	for _, tc := range []struct{ odds, want int64 }{{0, 1000}, {10, 1000}, {20, 2000}, {30, 3000}, {19, 1900}} {
		out, err := Settle(bets, outcome(entity.AreaUmbrella, tc.odds))
		if err != nil || out.TotalWin != tc.want {
			t.Fatalf("gross %d: %+v, %v", tc.odds, out, err)
		}
		if out.FinalReturnOdds[1] != 10 {
			t.Fatal("unlit losing cell must retain base return")
		}
	}
	// Pappu carries final gross odds directly: 19 is encodable; do not apply 124 divisibility rules.
}

func TestAllTwelveScreenIndicesAndLosingBets(t *testing.T) {
	for a := entity.AreaUmbrella; a <= entity.AreaRabbit; a++ {
		var bets entity.Bets
		bets[a.Index()] = 100
		bets[(a.Index()+1)%entity.AreaCount] = 30
		out, err := Settle(bets, outcome(a, 10))
		if err != nil || out.TotalWin != 1000 || out.NetWin != 870 || out.BetTotal != 130 {
			t.Fatalf("area %d: %+v %v", a, out, err)
		}
	}
	if entity.AreaWhippingTop.Index() != 7 || entity.AreaPigeon.Index() != 10 {
		t.Fatal("wire-to-screen index shifted")
	}
	var b entity.Bets
	b[0] = 100
	out, err := Settle(b, outcome(entity.AreaRabbit, 30))
	if err != nil || out.TotalWin != 0 || out.NetWin != -100 {
		t.Fatalf("loser received stake: %+v %v", out, err)
	}
}

func TestRejectInvalidAndOverflow(t *testing.T) {
	var zero entity.Bets
	if _, err := Settle(zero, outcome(1, 10)); err == nil {
		t.Fatal("accepted all-zero player")
	}
	negative := entity.Bets{-1, 2}
	if _, err := Settle(negative, outcome(1, 10)); err == nil {
		t.Fatal("accepted negative final bet")
	}
	sumOverflow := entity.Bets{math.MaxInt64, 1}
	if _, err := Settle(sumOverflow, outcome(1, 10)); err == nil {
		t.Fatal("bet sum overflow")
	}
	productOverflow := entity.Bets{math.MaxInt64/10 + 1}
	if _, err := Settle(productOverflow, outcome(1, 10)); err == nil {
		t.Fatal("payout overflow")
	}
	good := entity.Bets{100}
	for _, bad := range []result.Outcome{outcome(0, 10), outcome(13, 10), outcome(1, -1), outcome(1, 9), {Winner: 1, Pic: 2}, {Winner: 1, Pic: 1, IsBonus: true}} {
		if _, err := Settle(good, bad); err == nil {
			t.Fatalf("accepted invalid outcome %+v", bad)
		}
	}
}

func TestWeightedBoundariesAndRNGAudit(t *testing.T) {
	m := engine(t)
	for _, tc := range []struct {
		n    uint64
		want entity.Area
	}{{0, 1}, {1, 1}, {2, 11}, {4, 11}} {
		o, used, err := m.DrawRoundWithRNG("fixture", func(max uint64) (uint64, error) {
			if max != 5 {
				t.Fatal("wrong weight sum")
			}
			return tc.n, nil
		})
		if err != nil || o.Winner != tc.want || len(used) != 1 || used[0] != tc.n {
			t.Fatalf("boundary %d: %+v %v %v", tc.n, o, used, err)
		}
	}
	for _, rng := range []RNG{nil, func(uint64) (uint64, error) { return 5, nil }, func(uint64) (uint64, error) { return 0, errors.New("RNG failed") }} {
		if _, _, err := m.DrawRoundWithRNG("fixture", rng); err == nil {
			t.Fatal("accepted invalid RNG")
		}
	}
	if _, _, err := m.DrawRound("unknown"); err == nil {
		t.Fatal("accepted unknown version")
	}
}

func TestSettingsFailFastAndRemainImmutable(t *testing.T) {
	if _, err := NewPappuMath(nil); !errors.Is(err, ErrSettingsNotReady) {
		t.Fatal(err)
	}
	for _, vs := range []setting.VersionSetting{
		{}, {Outcomes: []setting.WeightedOutcome{{Weight: 0, Outcome: outcome(1, 10)}}},
		{Outcomes: []setting.WeightedOutcome{{Weight: math.MaxUint64, Outcome: outcome(1, 10)}, {Weight: 1, Outcome: outcome(2, 10)}}},
		{Outcomes: []setting.WeightedOutcome{{Weight: 1, Outcome: outcome(0, 10)}}},
	} {
		if _, err := NewPappuMath(map[string]setting.VersionSetting{"fixture": vs}); err == nil {
			t.Fatal("accepted invalid weights/outcome")
		}
	}
	settings := map[string]setting.VersionSetting{"fixture": {Outcomes: []setting.WeightedOutcome{{Weight: 1, Outcome: outcome(1, 10)}}}}
	m, err := NewPappuMath(settings)
	if err != nil {
		t.Fatal(err)
	}
	settings["fixture"].Outcomes[0].Outcome.Winner = 12
	o, _, err := m.DrawRoundWithRNG("fixture", func(uint64) (uint64, error) { return 0, nil })
	if err != nil || o.Winner != 1 {
		t.Fatal("caller mutated engine settings")
	}
	o.Winner = 12
	o, _, _ = m.DrawRoundWithRNG("fixture", func(uint64) (uint64, error) { return 0, nil })
	if o.Winner != 1 {
		t.Fatal("caller mutated cached outcome")
	}
}

func TestRoomUsesSharedOutcomeAndBetsDoNotChooseWinner(t *testing.T) {
	m := engine(t)
	for i := 0; i < 20; i++ {
		out, err := m.GetRoomResult(&result.RoomInput{Version: "fixture", Players: []entity.Bets{{100}, {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100}}})
		if err != nil {
			t.Fatal(err)
		}
		if len(out.UsedRNG) != 1 || out.Players[0].Winner != out.Players[1].Winner {
			t.Fatal("room redrawn per player")
		}
	}
	// Draw has no Bets input; the same outcome can be settled against any frozen player ledger.
	o, _, _ := m.DrawRoundWithRNG("fixture", func(uint64) (uint64, error) { return 0, nil })
	a, _ := Settle(entity.Bets{100}, *o)
	b, _ := Settle(entity.Bets{0, 0, 100}, *o)
	if a.Winner != b.Winner || a.TotalWin != 2000 || b.TotalWin != 0 {
		t.Fatal("settlement changed shared draw")
	}
	if _, err := m.GetRoomResult(&result.RoomInput{Version: "fixture"}); err != nil {
		t.Fatal("spectator-only room cannot draw", err)
	}
}

func TestTheoryRTPAndConcurrentCalls(t *testing.T) {
	m := engine(t)
	rtp, err := m.TheoryRTP("fixture")
	if err != nil || rtp[0] != 8 || rtp[10] != 6 {
		t.Fatalf("theory RTP: %v %v", rtp, err)
	}
	// These deliberately nonproduction RTPs make a wrong +1 obvious.
	var wg sync.WaitGroup
	for i := 0; i < 32; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 10; j++ {
				if _, err := m.GetPappuResult(&result.PappuInput{Version: "fixture", Bets: entity.Bets{100}}); err != nil {
					t.Error(err)
				}
			}
		}()
	}
	wg.Wait()
}

func TestSixCapturedIDRRounds(t *testing.T) {
	raw, err := os.ReadFile("testdata/live_rounds.json")
	if err != nil {
		t.Fatal(err)
	}
	var rounds []struct {
		ID       string      `json:"round_id"`
		Currency string      `json:"currency"`
		Bets     entity.Bets `json:"bets"`
		Winner   entity.Area `json:"winner"`
		Pic      int32       `json:"pic"`
		Odds     entity.Odds `json:"return_odds"`
		Bonus    bool        `json:"is_bonus"`
		Win      int64       `json:"total_win"`
		Net      int64       `json:"net_win"`
	}
	if err = json.Unmarshal(raw, &rounds); err != nil {
		t.Fatal(err)
	}
	if len(rounds) != 6 {
		t.Fatalf("expected six live own-wager samples, got %d", len(rounds))
	}
	for _, r := range rounds {
		if r.Currency != "IDR" {
			t.Fatal("mixed currencies")
		}
		out, err := Settle(r.Bets, result.Outcome{Winner: r.Winner, Pic: r.Pic, ReturnOdds: r.Odds, IsBonus: r.Bonus})
		if err != nil || out.TotalWin != r.Win || out.NetWin != r.Net {
			t.Fatalf("round %s: %+v %v; want win %d net %d", r.ID, out, err, r.Win, r.Net)
		}
	}
}

func TestRTPAcceptanceChecksEveryArea(t *testing.T) {
	var outcomes []setting.WeightedOutcome
	for a := entity.AreaUmbrella; a <= entity.AreaRabbit; a++ {
		outcomes = append(outcomes, setting.WeightedOutcome{Weight: 1, Outcome: outcome(a, 12)})
	}
	m, err := NewPappuMath(map[string]setting.VersionSetting{"fixture": {Outcomes: outcomes}})
	if err != nil {
		t.Fatal(err)
	}
	if err := m.ValidateRTP("fixture", 1, 0.000000001); err != nil {
		t.Fatal(err)
	}
	if err := m.ValidateRTP("fixture", 0.97, 0.001); err == nil {
		t.Fatal("accepted wrong target RTP")
	}
	for _, bad := range []float64{0, -1, math.NaN(), math.Inf(1)} {
		if err := m.ValidateRTP("fixture", bad, 0.001); err == nil {
			t.Fatal("accepted invalid target")
		}
	}
	if err := m.ValidateRTP("fixture", 1, -0.1); err == nil {
		t.Fatal("accepted negative tolerance")
	}
	// A matching twelve-area average is not enough: this table heavily favors area 1.
	biased := engine(t)
	if err := biased.ValidateRTP("fixture", 14.0/12.0, 0.001); err == nil {
		t.Fatal("checked average instead of individual areas")
	}
}
