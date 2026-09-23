package dice

import (
	"encoding/json"
	"math"
	"os"
	"testing"
)

// 這支測試不呼叫 GetDiceResult，驗的是「機率端形式 ↔ 原廠封包形式」的轉換，
// 對照同目錄上層 ws_session*.jsonl 解出來的真實對局。機率端還沒實作前它就應該全綠。

type goldenFile struct {
	BaseOddsPkt []int         `json:"baseOddsPkt"`
	Rounds      []goldenRound `json:"rounds"`
}

type goldenRound struct {
	Source   string    `json:"source"`
	RoundID  int64     `json:"roundId"`
	Die1     int       `json:"die1"`
	Die2     int       `json:"die2"`
	BetsPkt  []float64 `json:"betsPkt"`  // 元，封包順序
	ExtraPkt []int     `json:"extraPkt"` // 倍數，封包順序，沒蓋 = 1
	TotalWin float64   `json:"totalWin"` // 元
}

func loadGolden(t *testing.T) goldenFile {
	t.Helper()
	b, err := os.ReadFile("testdata/rounds_124.json")
	if err != nil {
		t.Fatalf("讀不到黃金資料: %v", err)
	}
	var g goldenFile
	if err := json.Unmarshal(b, &g); err != nil {
		t.Fatalf("黃金資料格式錯誤: %v", err)
	}
	requireEq(t, len(g.Rounds), 29, "黃金資料應有 29 局")
	return g
}

func toPoint(yuan float64) int64 { return int64(math.Round(yuan * 10000)) }

// TestFromPacketOdds 封包的基礎賠率轉成機率端形式後，要等於 DefaultBaseOdds。
func TestFromPacketOdds(t *testing.T) {
	g := loadGolden(t)
	assertDeepEq(t, FromPacketOdds(g.BaseOddsPkt), DefaultBaseOdds,
		"封包 %v 減 1 重排後應等於機率端賠率表", g.BaseOddsPkt)
}

// TestGoldenSettle 用實測 29 局驗結算公式：機率端形式算出來的總贏分要等於封包回的 total_win。
func TestGoldenSettle(t *testing.T) {
	g := loadGolden(t)
	for _, r := range g.Rounds {
		out, bets := goldenToUI(r, g.BaseOddsPkt)
		assertEq(t, SettleWin(bets, out.FinalOdds, out.Sum), toPoint(r.TotalWin),
			"%s rid=%d 骰子 %d+%d=%d", r.Source, r.RoundID, r.Die1, r.Die2, out.Sum)
	}
}

// TestGoldenRoundTrip 機率端形式再轉回封包，要完全還原原始封包值。
func TestGoldenRoundTrip(t *testing.T) {
	g := loadGolden(t)
	for _, r := range g.Rounds {
		out, _ := goldenToUI(r, g.BaseOddsPkt)

		pktBase, pktExtra, err := ToPacket(out, DefaultBaseOdds[:])
		if err != nil {
			t.Fatalf("rid=%d 轉封包失敗: %v", r.RoundID, err)
		}

		assertDeepEq(t, pktBase[:], g.BaseOddsPkt, "rid=%d 基礎賠率還原", r.RoundID)
		for i, want := range r.ExtraPkt {
			if math.Abs(pktExtra[i]-float64(want)) > 1e-9 {
				t.Errorf("rid=%d 封包 pos %d 的 extra 還原成 %v，應為 %d",
					r.RoundID, i, pktExtra[i], want)
			}
		}
	}
}

// TestWinPositions 每個點數和對應的中獎注點（畫面順序）。
func TestWinPositions(t *testing.T) {
	cases := map[int][]int{
		2: {PosSmall, 3}, 3: {PosSmall, 4}, 4: {PosSmall, 5}, 5: {PosSmall, 6},
		6: {PosSmall, 7}, 7: {PosSeven}, 8: {PosBig, 8}, 9: {PosBig, 9},
		10: {PosBig, 10}, 11: {PosBig, 11}, 12: {PosBig, 12},
	}
	for sum, want := range cases {
		assertDeepEq(t, WinPositions(sum), want, "sum=%d", sum)
	}
}

// TestSwapTrap 專測「7」和「2-6」互換這個陷阱：
// 這兩格是畫面順序與封包順序唯二不同的地方，接錯的話 13 格有 11 格還是對的。
func TestSwapTrap(t *testing.T) {
	assertEq(t, DefaultBaseOdds[PosSeven], 5, "畫面 idx1 是 7，含本金賠率 5")
	assertEq(t, DefaultBaseOdds[PosSmall], 2, "畫面 idx0 是 2-6，含本金賠率 2")
	assertEq(t, uiToPkt[PosSmall], 1, "2-6 在封包是 position 1")
	assertEq(t, uiToPkt[PosSeven], 0, "7 在封包是 position 0")
	assertDeepEq(t, ToPacketPositions([]int{PosSeven}), []int{0}, "押中 7 → 封包 position 0")
	assertDeepEq(t, ToPacketPositions([]int{PosSmall}), []int{1}, "押中 2-6 → 封包 position 1")

	// 押 7 中獎，賠率必須是 5 不是 2
	bets := make([]int64, PosCount)
	bets[PosSeven] = 100000
	finalOdds := DefaultBaseOdds
	assertEq(t, SettleWin(bets, finalOdds[:], 7), int64(500000),
		"押 7 一元中了要拿回 5 元，拿到 2 元就是順序接反了")
}

// goldenToUI 把實測封包資料（封包順序、顯示賠率）轉成機率端形式（畫面順序、含本金）。
func goldenToUI(r goldenRound, pktBase []int) (*DiceOutPut, []int64) {
	out := &DiceOutPut{
		Dices:      []int{r.Die1, r.Die2},
		Sum:        r.Die1 + r.Die2,
		ExtraMults: make([]int, PosCount),
		FinalOdds:  make([]int, PosCount),
	}
	bets := make([]int64, PosCount)

	for ui := 0; ui < PosCount; ui++ {
		pkt := uiToPkt[ui]
		final := pktBase[pkt]*r.ExtraPkt[pkt] + 1 // 顯示賠率 × extra 再加本金
		out.FinalOdds[ui] = final
		if r.ExtraPkt[pkt] != 1 {
			out.ExtraMults[ui] = final
		}
		bets[ui] = toPoint(r.BetsPkt[pkt])
	}
	out.TotalWin = SettleWin(bets, out.FinalOdds, out.Sum)
	return out, bets
}
