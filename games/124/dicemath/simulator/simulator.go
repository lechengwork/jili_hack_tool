package simulator

import (
	"dicemath/entity"
	"dicemath/entity/result"
)

const betUnit int64 = 100

// PlayFunc 單局函式，例如 g4102.GetDiceResult 或 (*game.DiceMath).GetDiceResult
type PlayFunc func(in *result.DiceInput) (*result.DiceOutput, error)

// Simulator 對指定版本跑大量模擬：每局 13 格各押 betUnit，
// 真實 EXTRA 與點數獨立，所以同一局即可同時累積 13 格各自的單押 RTP。
type Simulator struct {
	Play      PlayFunc
	Version   string
	Rounds    int64
	cellBets  [entity.CellCount]int64
	cellWins  [entity.CellCount]int64
	sumCounts [13]int64                   // index = 點數總和
	litCounts [entity.CellCount + 1]int64 // index = 畫面亮格數
}

// NewSimulator 建立模擬器；version 是否合法由 Simulate 時的 GetDiceResult 回報
func NewSimulator(play PlayFunc, version string) *Simulator {
	return &Simulator{Play: play, Version: version}
}

// Simulate 跑 round 局並累積統計
func (s *Simulator) Simulate(round int) error {
	in := result.DiceInput{Version: s.Version}
	for c := range in.Bets {
		in.Bets[c] = betUnit
	}
	for i := 0; i < round; i++ {
		out, err := s.Play(&in)
		if err != nil {
			return err
		}
		s.Rounds++
		for c := range s.cellBets {
			s.cellBets[c] += betUnit
		}
		for _, c := range entity.WinningCells(out.Sum) {
			s.cellWins[c] += betUnit * int64(out.FinalOdds[c]+1)
		}
		s.sumCounts[out.Sum]++
		lit := 0
		for _, j := range out.ExtraMults {
			if j > 1 { // 含真實 EXTRA 與假演出
				lit++
			}
		}
		s.litCounts[lit]++
	}
	return nil
}

// CellRTP 各格單押實測 RTP
func (s *Simulator) CellRTP() [entity.CellCount]float64 {
	var rtp [entity.CellCount]float64
	for c := range rtp {
		if s.cellBets[c] > 0 {
			rtp[c] = float64(s.cellWins[c]) / float64(s.cellBets[c])
		}
	}
	return rtp
}

// SumProb 點數總和實測機率(index = 點數總和)
func (s *Simulator) SumProb() [13]float64 {
	var prob [13]float64
	if s.Rounds == 0 {
		return prob
	}
	for sum, n := range s.sumCounts {
		prob[sum] = float64(n) / float64(s.Rounds)
	}
	return prob
}

// LitCountProb 畫面亮格數實測機率(index = 亮格數)
func (s *Simulator) LitCountProb() [entity.CellCount + 1]float64 {
	var prob [entity.CellCount + 1]float64
	if s.Rounds == 0 {
		return prob
	}
	for k, n := range s.litCounts {
		prob[k] = float64(n) / float64(s.Rounds)
	}
	return prob
}
