package dice

import (
	"os"
	"strconv"
	"sync"
	"testing"
)

// ===========================================================================
//
//	GetDiceResult 的規格＝這份測試。全綠就算完成。
//
//	go test ./...            完整跑（RTP 那支約數秒）
//	go test -short ./...     快速跑，統計測試用小樣本
//	go test -race ./...      併發安全
//
//	RTP 目標值還沒跟營運確認，先放 96% 附近。確定後改這三個常數即可。
//
// ===========================================================================

const (
	rtpMin    = 0.94 // 每格 RTP 下限
	rtpMax    = 0.97 // 每格 RTP 上限
	rtpSpread = 0.02 // 各格之間的最大差距，太大就會有一格特別好賺
)

func newInput(bets []int64) *DiceInput {
	if bets == nil {
		bets = make([]int64, PosCount)
	}
	base := DefaultBaseOdds
	return &DiceInput{Bets: bets, BaseOdds: base[:]}
}

func flatBets(amount int64) []int64 {
	b := make([]int64, PosCount)
	for i := range b {
		b[i] = amount
	}
	return b
}

// requireImplemented 先探一次，沒實作就乾淨地失敗，不要讓 panic 炸掉整個測試程序。
func requireImplemented(t *testing.T) {
	t.Helper()
	defer func() {
		if r := recover(); r != nil {
			t.Fatalf("GetDiceResult 尚未實作或直接 panic: %v", r)
		}
	}()
	_ = GetDiceResult(newInput(nil))
}

func rounds(t *testing.T, full, short int) int {
	t.Helper()
	if s := os.Getenv("DICE_ROUNDS"); s != "" {
		if n, err := strconv.Atoi(s); err == nil {
			return n
		}
	}
	if testing.Short() {
		return short
	}
	return full
}

// ---------------------------------------------------------------------------
// 形狀與自洽
// ---------------------------------------------------------------------------

// TestOutputShape 回傳的陣列長度、骰子範圍、點數和。
func TestOutputShape(t *testing.T) {
	requireImplemented(t)
	for i := 0; i < 2000; i++ {
		out := GetDiceResult(newInput(flatBets(10000)))
		if out == nil {
			t.Fatal("回傳 nil")
		}
		requireEq(t, len(out.Dices), 2, "Dices 要有兩顆骰子")
		requireEq(t, len(out.ExtraMults), PosCount, "ExtraMults 長度要是 13")
		requireEq(t, len(out.FinalOdds), PosCount, "FinalOdds 長度要是 13")
		requireInRange(t, out.Dices[0], 1, 6, "第一顆骰子")
		requireInRange(t, out.Dices[1], 1, 6, "第二顆骰子")
		requireEq(t, out.Sum, out.Dices[0]+out.Dices[1], "Sum 要等於兩顆骰子相加")
	}
}

// TestFinalOddsConsistent FinalOdds 必須 13 格填滿：有蓋 EXTRA 用 ExtraMults，沒蓋用 BaseOdds。
func TestFinalOddsConsistent(t *testing.T) {
	requireImplemented(t)
	base := DefaultBaseOdds
	for i := 0; i < 2000; i++ {
		out := GetDiceResult(newInput(flatBets(10000)))
		for p := 0; p < PosCount; p++ {
			want := base[p]
			if out.ExtraMults[p] != 0 {
				want = out.ExtraMults[p]
			}
			requireEq(t, out.FinalOdds[p], want,
				"注點 %s: 沒蓋 EXTRA 要填基礎賠率，不是 0", PosNames[p])
		}
	}
}

// TestExtraRules EXTRA 一定比原始賠率高，且減 1 後要被基礎顯示賠率整除。
func TestExtraRules(t *testing.T) {
	requireImplemented(t)
	base := DefaultBaseOdds
	for i := 0; i < 5000; i++ {
		out := GetDiceResult(newInput(flatBets(10000)))
		for p := 0; p < PosCount; p++ {
			e := out.ExtraMults[p]
			if e == 0 {
				continue
			}
			if e <= base[p] {
				t.Fatalf("注點 %s: EXTRA 賠率 %d 沒有比原始賠率 %d 高", PosNames[p], e, base[p])
			}
			if (e-1)%(base[p]-1) != 0 {
				t.Fatalf("注點 %s: 最終賠率 %d 減 1 後的 %d 不是顯示賠率 %d 的整數倍，原廠封包塞不下",
					PosNames[p], e, e-1, base[p]-1)
			}
		}
	}
}

// TestTotalWin TotalWin 要等於各中獎注點 bet x FinalOdds 的總和（含本金）。
func TestTotalWin(t *testing.T) {
	requireImplemented(t)
	bets := flatBets(10000)
	bets[PosSeven] = 30000
	bets[PosBig] = 0 // 留一格沒押，確認沒押的格子不會算進去
	for i := 0; i < 5000; i++ {
		out := GetDiceResult(newInput(bets))
		requireEq(t, out.TotalWin, SettleWin(bets, out.FinalOdds, out.Sum),
			"骰子 %v 和=%d", out.Dices, out.Sum)
	}
}

// TestNoBets 完全沒下注不能出事，而且照樣要灑 EXTRA（原廠實測 29 局裡有 6 局如此）。
func TestNoBets(t *testing.T) {
	requireImplemented(t)
	withExtra := 0
	for i := 0; i < 2000; i++ {
		out := GetDiceResult(newInput(nil))
		requireEq(t, out.TotalWin, int64(0), "沒下注不該有贏分")
		for p := 0; p < PosCount; p++ {
			if out.ExtraMults[p] != 0 {
				withExtra++
				break
			}
		}
	}
	if withExtra == 0 {
		t.Error("沒下注的局也要照樣灑 EXTRA，不能因為沒注就不灑")
	}
}

// TestInputNotMutated 不可以改動傳進來的 Input。
func TestInputNotMutated(t *testing.T) {
	requireImplemented(t)
	in := newInput(flatBets(10000))
	betsCopy := append([]int64(nil), in.Bets...)
	oddsCopy := append([]int(nil), in.BaseOdds...)
	for i := 0; i < 500; i++ {
		GetDiceResult(in)
	}
	assertDeepEq(t, in.Bets, betsCopy, "Bets 被改動了")
	assertDeepEq(t, in.BaseOdds, oddsCopy, "BaseOdds 被改動了")
}

// TestConcurrentSafe 併發呼叫不能有 data race（配 -race 跑）。
func TestConcurrentSafe(t *testing.T) {
	requireImplemented(t)
	var wg sync.WaitGroup
	for g := 0; g < 32; g++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < 200; i++ {
				out := GetDiceResult(newInput(flatBets(10000)))
				if len(out.FinalOdds) != PosCount {
					panic("長度不對")
				}
			}
		}()
	}
	wg.Wait()
}
