package game

import (
	"dicemath/entity"
	"dicemath/entity/setting"
)

// TheoryRTP 依基礎淨賠率、有 EXTRA 的局的權重表與 NoExtraRate(萬分比)算出 13 格的精確 RTP：
//
//	g           = NoExtraRate / 10000
//	E[j_c]      = g × 1 + (1 − g) × Σ_j (w_c[j] × j) / Σ_j w_c[j]
//	RTP_c       = CellCombos[c] / 36 × (E[j_c] × 基礎淨賠率_c + 1)
//
// 真實 EXTRA 與點數獨立，假演出只在沒中獎格，因此 RTP 只由權重表與 NoExtraRate 決定。
// 權重總和為 0 的格回傳 0(NewDiceMath 會擋下這種表，這裡不報錯)。
func TheoryRTP(baseOdds [entity.CellCount]int, weights [entity.CellCount][entity.MaxExtraMult]int, noExtraRate int) [entity.CellCount]float64 {
	g := float64(noExtraRate) / setting.NoExtraRateScale
	var rtp [entity.CellCount]float64
	for c := 0; c < entity.CellCount; c++ {
		sumW, sumWJ := 0, 0
		for i, w := range weights[c] {
			sumW += w
			sumWJ += w * (i + 1) // index i 對應 j = i+1
		}
		if sumW == 0 {
			continue
		}
		expectedMult := g + (1-g)*float64(sumWJ)/float64(sumW)
		rtp[c] = float64(entity.CellCombos[c]) / 36 * (expectedMult*float64(baseOdds[c]) + 1)
	}
	return rtp
}
