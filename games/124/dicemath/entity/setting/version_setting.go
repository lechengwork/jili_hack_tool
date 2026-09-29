package setting

import "dicemath/entity"

// NoExtraRateScale NoExtraRate 的單位(萬分比)：2500 = 25%
const NoExtraRateScale = 10000

// VersionSetting 單一 RTP 版本的設定(每個版本各自一組，可整組從企劃 Excel 貼上)
type VersionSetting struct {
	// NoExtraRate 整局不發 EXTRA 的機率(萬分比，0 ≤ NoExtraRate < 10000)。
	// 抽中時該局 13 格全部 j=1，畫面一格都不亮，也不做假演出。與下注、點數無關。
	NoExtraRate int

	// ExtraWeights 有 EXTRA 的局，各格抽到 j=1..10 的權重(index 0 對應 j=1)，引擎照填照用。
	// 整體 RTP 需把 NoExtraRate 算進去：E[j] = g + (1 − g) × Σ(w_j × j)/Σw，g = NoExtraRate/10000(見 game.TheoryRTP)。
	ExtraWeights [entity.CellCount][entity.MaxExtraMult]int

	// LitCountWeights 有 EXTRA 的局，畫面總亮格數 K 的分佈(index = K，0~13)
	LitCountWeights [entity.CellCount + 1]int
}
