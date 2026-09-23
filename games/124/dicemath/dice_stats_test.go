package dice

import (
	"testing"
)

// 統計性質的測試。這幾支才是這個函式真正需要動腦的地方。
// 樣本數可用環境變數 DICE_ROUNDS 覆寫，例如 DICE_ROUNDS=20000000 go test -run RTP ./...

// chiSquare 回傳卡方統計量。obs 與 exp 長度須相同。
func chiSquare(obs []float64, exp []float64) float64 {
	var chi float64
	for i := range obs {
		if exp[i] <= 0 {
			continue
		}
		d := obs[i] - exp[i]
		chi += d * d / exp[i]
	}
	return chi
}

// sumCounts 兩顆骰子點數和的組合數，index 0..12（0、1 不用）。
var sumCounts = [13]float64{0, 0, 1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1}

// TestDiceUniform 骰子要公平：單顆 6 面均勻、兩顆相加的分佈符合 2d6。
func TestDiceUniform(t *testing.T) {
	requireImplemented(t)
	n := rounds(t, 1_000_000, 100_000)

	die := [2][7]float64{}
	sums := [13]float64{}
	for i := 0; i < n; i++ {
		out := GetDiceResult(newInput(nil))
		die[0][out.Dices[0]]++
		die[1][out.Dices[1]]++
		sums[out.Sum]++
	}

	for d := 0; d < 2; d++ {
		obs := die[d][1:7]
		exp := make([]float64, 6)
		for i := range exp {
			exp[i] = float64(n) / 6
		}
		chi := chiSquare(obs, exp)
		assertLess(t, chi, 30.0, "第 %d 顆骰子不均勻，卡方=%.1f 觀測=%v", d+1, chi, obs)
	}

	obs, exp := sums[2:13], make([]float64, 11)
	for s := 2; s <= 12; s++ {
		exp[s-2] = float64(n) * sumCounts[s] / 36
	}
	chi := chiSquare(obs, exp)
	assertLess(t, chi, 40.0, "點數和分佈不符合公平 2d6，卡方=%.1f 觀測=%v", chi, obs)
}

// countExtra 跑 n 局，回傳每格出現 EXTRA 的次數。
func countExtra(n int, bets []int64) [PosCount]float64 {
	var c [PosCount]float64
	for i := 0; i < n; i++ {
		out := GetDiceResult(newInput(bets))
		for p := 0; p < PosCount; p++ {
			if out.ExtraMults[p] != 0 {
				c[p]++
			}
		}
	}
	return c
}

// chi2x2 對 2x2 列聯表做卡方（df=1）。
func chi2x2(a, b, c, d float64) float64 {
	n := a + b + c + d
	den := (a + b) * (c + d) * (a + c) * (b + d)
	if den == 0 {
		return 0
	}
	num := a*d - b*c
	return n * num * num / den
}

// TestExtraIndependentOfBets EXTRA 不可以看玩家押了哪幾格決定。
// 做法：一組完全不下注、一組押好押滿，比較每格出現 EXTRA 的比率。
func TestExtraIndependentOfBets(t *testing.T) {
	requireImplemented(t)
	n := rounds(t, 400_000, 50_000)

	noBet := countExtra(n, make([]int64, PosCount))
	allBet := countExtra(n, flatBets(100000))

	for p := 0; p < PosCount; p++ {
		chi := chi2x2(noBet[p], float64(n)-noBet[p], allBet[p], float64(n)-allBet[p])
		assertLess(t, chi, 25.0,
			"注點 %s 的 EXTRA 出現率跟有沒有下注有關（卡方=%.1f，沒押 %.0f/%d、押滿 %.0f/%d）— "+
				"EXTRA 不能看 Bets 決定", PosNames[p], chi, noBet[p], n, allBet[p], n)
	}
}

// TestExtraIndependentOfDice EXTRA 不可以跟骰子結果有關聯
// （例如「只在會中的格子蓋」或「只在不會中的格子蓋」）。
func TestExtraIndependentOfDice(t *testing.T) {
	requireImplemented(t)
	n := rounds(t, 500_000, 50_000)

	var extraWin, extraLose, noExtraWin, noExtraLose [PosCount]float64
	for i := 0; i < n; i++ {
		out := GetDiceResult(newInput(nil))
		won := [PosCount]bool{}
		for _, p := range WinPositions(out.Sum) {
			won[p] = true
		}
		for p := 0; p < PosCount; p++ {
			switch {
			case out.ExtraMults[p] != 0 && won[p]:
				extraWin[p]++
			case out.ExtraMults[p] != 0:
				extraLose[p]++
			case won[p]:
				noExtraWin[p]++
			default:
				noExtraLose[p]++
			}
		}
	}

	for p := 0; p < PosCount; p++ {
		chi := chi2x2(extraWin[p], extraLose[p], noExtraWin[p], noExtraLose[p])
		assertLess(t, chi, 25.0,
			"注點 %s 的 EXTRA 與該格中不中有關聯（卡方=%.1f）— 兩者必須獨立", PosNames[p], chi)
	}
}

// TestRTPPerPosition 每一格的長期 RTP 都要落在區間內，且彼此差距不能太大。
//
// 這是這個遊戲唯一真正需要設計的地方：基礎賠率只有 72%~83%，
// 全靠 EXTRA 補到目標值，而且各格要補的量不一樣。
// 若所有格共用同一組 EXTRA 機率，「7」那格會超過 100%，玩家固定押 7 就長期打贏。
// 各格需要的 EXTRA 期望值見 README.md。
func TestRTPPerPosition(t *testing.T) {
	requireImplemented(t)
	n := rounds(t, 5_000_000, 200_000)

	const unit int64 = 10000
	bets := flatBets(unit)
	var ret [PosCount]int64

	for i := 0; i < n; i++ {
		out := GetDiceResult(newInput(bets))
		for _, p := range WinPositions(out.Sum) {
			ret[p] += unit * int64(out.FinalOdds[p])
		}
	}

	staked := float64(n) * float64(unit)
	lo, hi := 2.0, 0.0
	t.Logf("%-6s %10s", "注點", "RTP")
	for p := 0; p < PosCount; p++ {
		rtp := float64(ret[p]) / staked
		t.Logf("%-6s %9.4f%%", PosNames[p], rtp*100)
		lo, hi = min(lo, rtp), max(hi, rtp)

		if testing.Short() {
			continue // 樣本太少，只看有沒有離譜
		}
		if rtp < rtpMin {
			t.Errorf("注點 %s 的 RTP %.4f%% 低於下限 %.2f%%", PosNames[p], rtp*100, rtpMin*100)
		}
		if rtp > rtpMax {
			t.Errorf("注點 %s 的 RTP %.4f%% 高於上限 %.2f%%", PosNames[p], rtp*100, rtpMax*100)
		}
	}

	if testing.Short() {
		if lo <= 0.5 || hi >= 1.5 {
			t.Errorf("有一格的 RTP 離譜（最低 %.4f、最高 %.4f）", lo, hi)
		}
		return
	}
	if hi-lo > rtpSpread {
		t.Errorf("各格 RTP 差距 %.4f 太大（最低 %.4f、最高 %.4f）— 玩家會固定押最好賺的那格",
			hi-lo, lo, hi)
	}
}
