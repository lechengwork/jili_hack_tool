package game

import (
	"errors"
	"fmt"
	"math"

	"dicemath/entity"
	"dicemath/entity/result"
	"dicemath/entity/setting"
	"dicemath/randomNumber"
)

// fakePickScale 假演出挑格權重的整數化精度(P(j≥2) × 10⁶)；13 格總和最多 1.3×10⁷，在 RNG 上限內
const fakePickScale = 1_000_000

// DiceMath 機台實體：建構時載入並驗證所有版本的設定，
// 之後 GetDiceResult() 只查表 + 抽 RNG，不再重新計算任何機率。
type DiceMath struct {
	MachineID int
	baseOdds  [entity.CellCount]int    // 基礎淨賠率
	versions  map[string]versionTables // version → 該版本建構後的查表資料
	newRng    func() *randomNumber.RNG // 每局產生一個新的 RNG 實例，天生併發安全；測試可替換
}

// versionTables 單一版本建構後的查表資料
type versionTables struct {
	noExtraRate     int                                        // 整局不發 EXTRA 的機率(萬分比)
	extraWeights    [entity.CellCount][entity.MaxExtraMult]int // 有 EXTRA 的局使用的權重(即設定值)
	fakePickWeights [entity.CellCount]int                      // 假演出挑格權重(由 extraWeights 推導)
	litCountWeights [entity.CellCount + 1]int                  // 有 EXTRA 的局，畫面總亮格數 K 的分佈
}

// NewDiceMath 建立機台實體。任一設定驗證失敗即回傳錯誤(fail fast)，不允許帶著錯誤設定上線。
func NewDiceMath(machineID int, baseOdds [entity.CellCount]int, settings map[string]setting.VersionSetting) (*DiceMath, error) {
	if len(settings) == 0 {
		return nil, errors.New("settings is empty")
	}
	for c, odds := range baseOdds {
		if odds <= 0 {
			return nil, fmt.Errorf("cell %s: base odds must be > 0, got %d", entity.CellNames[c], odds)
		}
	}

	versions := make(map[string]versionTables, len(settings))
	for version, vs := range settings {
		if _, ok := setting.GetVersionRtp(version); !ok {
			return nil, fmt.Errorf("version %s not in allowed list", version)
		}
		vt, err := buildVersionTables(vs)
		if err != nil {
			return nil, fmt.Errorf("version %s: %w", version, err)
		}
		versions[version] = vt
	}

	return &DiceMath{
		MachineID: machineID,
		baseOdds:  baseOdds,
		versions:  versions,
		newRng:    randomNumber.NewRNG,
	}, nil
}

// buildVersionTables 驗證單一版本設定並建立查表資料(權重照設定使用，不做換算)
func buildVersionTables(vs setting.VersionSetting) (versionTables, error) {
	var vt versionTables
	if vs.NoExtraRate < 0 || vs.NoExtraRate >= setting.NoExtraRateScale {
		return vt, fmt.Errorf("NoExtraRate = %d, must be in [0, %d)", vs.NoExtraRate, setting.NoExtraRateScale)
	}
	if err := validateWeights(vs.LitCountWeights[:]); err != nil {
		return vt, fmt.Errorf("LitCountWeights: %w", err)
	}

	vt.noExtraRate = vs.NoExtraRate
	vt.litCountWeights = vs.LitCountWeights
	vt.extraWeights = vs.ExtraWeights
	for c, weights := range vs.ExtraWeights {
		if err := validateWeights(weights[:]); err != nil {
			return vt, fmt.Errorf("cell %s: %w", entity.CellNames[c], err)
		}
		vt.fakePickWeights[c] = triggerPickWeight(weights)
	}
	return vt, nil
}

// GetMachineID 取得機台編號
func (m *DiceMath) GetMachineID() int {
	return m.MachineID
}

// validateWeights 權重皆須 ≥ 0，總和須 > 0 且不超過 RNG 上限
func validateWeights(weights []int) error {
	sum := 0
	for i, w := range weights {
		if w < 0 {
			return fmt.Errorf("weight[%d] = %d, must be >= 0", i, w)
		}
		sum += w
	}
	if sum <= 0 {
		return errors.New("sum of weights must be > 0")
	}
	if sum > randomNumber.MAX_RNG_VALUE {
		return fmt.Errorf("sum of weights %d exceeds RNG limit %d", sum, randomNumber.MAX_RNG_VALUE)
	}
	return nil
}

// triggerPickWeight 該格真實觸發率 P(j≥2) 的整數化，作為假演出挑格權重
func triggerPickWeight(weights [entity.MaxExtraMult]int) int {
	total, lit := 0, 0
	for i, w := range weights {
		total += w
		if i > 0 {
			lit += w
		}
	}
	return int(math.Round(float64(lit) * fakePickScale / float64(total)))
}

// GetDiceResult 單局結果。流程(RNG 消耗順序固定)：
// 本局有無 EXTRA → 開骰 d1 → d2 →(有 EXTRA 的局才有)13 格真實 EXTRA(index 0→12) → 總亮格數 K
// → 假演出(每格先挑格、再抽 j) → 結算
func (m *DiceMath) GetDiceResult(in *result.DiceInput) (*result.DiceOutput, error) {
	if in == nil {
		return nil, errors.New("input is nil")
	}
	vt, ok := m.versions[in.Version]
	if !ok {
		return nil, fmt.Errorf("version %s is not supported by machine %d", in.Version, m.MachineID)
	}
	if err := validateBets(in.Bets); err != nil {
		return nil, err
	}

	rng := m.newRng()
	out := &result.DiceOutput{BaseOdds: m.baseOdds}

	// 本局有無 EXTRA：抽中 NoExtraRate 時整局 13 格全不亮、也不做假演出(與下注、點數無關)
	gate, err := rng.GetRandomIntMax(setting.NoExtraRateScale)
	if err != nil {
		return nil, fmt.Errorf("draw no-extra gate: %w", err)
	}
	noExtra := gate < vt.noExtraRate

	// 開骰：兩顆各自獨立抽 1~6，禁止直接對總和抽樣
	d1, err := rng.GetRandomIntMax(6)
	if err != nil {
		return nil, fmt.Errorf("roll die 1: %w", err)
	}
	d2, err := rng.GetRandomIntMax(6)
	if err != nil {
		return nil, fmt.Errorf("roll die 2: %w", err)
	}
	out.Die1, out.Die2 = d1+1, d2+1
	out.Sum = out.Die1 + out.Die2

	var isWinning [entity.CellCount]bool
	winningCells := entity.WinningCells(out.Sum)
	for _, c := range winningCells {
		isWinning[c] = true
	}

	if noExtra {
		for c := range out.ExtraMults {
			out.ExtraMults[c] = 1
		}
	} else if err := m.drawExtra(rng, vt, isWinning, &out.ExtraMults); err != nil {
		return nil, err
	}

	// 結算：FinalOdds = ExtraMults × BaseOdds(畫面 nX，注單快照)，TotalWin 含本金
	for c := 0; c < entity.CellCount; c++ {
		out.FinalOdds[c] = out.ExtraMults[c] * m.baseOdds[c]
	}
	for _, c := range winningCells {
		out.TotalWin += in.Bets[c] * int64(out.FinalOdds[c]+1)
	}
	out.UsedRNG = rng.CopyUsedRNG()
	return out, nil
}

// drawExtra 有 EXTRA 的局：每格依權重獨立抽真實 EXTRA，再依 K 補假演出
func (m *DiceMath) drawExtra(rng *randomNumber.RNG, vt versionTables, isWinning [entity.CellCount]bool, extraMults *[entity.CellCount]int) error {
	// 真實 EXTRA：每格依權重獨立抽 j，與點數、下注無關
	realLit := 0
	for c := 0; c < entity.CellCount; c++ {
		idx, err := rng.GetRandomIndexWeight(vt.extraWeights[c][:])
		if err != nil {
			return fmt.Errorf("draw extra for cell %s: %w", entity.CellNames[c], err)
		}
		extraMults[c] = idx + 1 // idx 0 = j=1(不亮)
		if idx > 0 {
			realLit++
		}
	}

	// 假演出：K 為畫面總亮格數(含真實)，只補在沒亮且沒中獎的格子，不影響派彩
	k, err := rng.GetRandomIndexWeight(vt.litCountWeights[:])
	if err != nil {
		return fmt.Errorf("draw lit count: %w", err)
	}
	return m.addFakeExtra(rng, vt.extraWeights, vt.fakePickWeights, isWinning, k-realLit, extraMults)
}

// addFakeExtra 從「沒亮(j=1)、沒中獎、挑格權重 > 0」的候選格中，依挑格權重不放回抽 need 格，
// 倍數取該格權重表 j≥2 的部分(與真實 EXTRA 分佈一致)。候選不足時補到沒有為止；need ≤ 0 不動作。
func (m *DiceMath) addFakeExtra(rng *randomNumber.RNG, weights [entity.CellCount][entity.MaxExtraMult]int,
	pickWeights [entity.CellCount]int, isWinning [entity.CellCount]bool, need int, extraMults *[entity.CellCount]int) error {

	candidates := make([]int, 0, entity.CellCount)
	for c := 0; c < entity.CellCount; c++ {
		if extraMults[c] == 1 && !isWinning[c] && pickWeights[c] > 0 {
			candidates = append(candidates, c)
		}
	}

	for ; need > 0 && len(candidates) > 0; need-- {
		candidateWeights := make([]int, len(candidates))
		for i, c := range candidates {
			candidateWeights[i] = pickWeights[c]
		}
		i, err := rng.GetRandomIndexWeight(candidateWeights)
		if err != nil {
			return fmt.Errorf("pick fake extra cell: %w", err)
		}
		c := candidates[i]
		candidates = append(candidates[:i], candidates[i+1:]...)

		idx, err := rng.GetRandomIndexWeight(weights[c][1:]) // idx 0 = j=2
		if err != nil {
			return fmt.Errorf("draw fake extra for cell %s: %w", entity.CellNames[c], err)
		}
		extraMults[c] = idx + 2
	}
	return nil
}

// validateBets 任一格下注 < 0 或 13 格全為 0 時回傳錯誤(下注上限由 server 管理)
func validateBets(bets [entity.CellCount]int64) error {
	var total int64
	for c, bet := range bets {
		if bet < 0 {
			return fmt.Errorf("cell %s: bet must be >= 0, got %d", entity.CellNames[c], bet)
		}
		total += bet
	}
	if total == 0 {
		return errors.New("all bets are zero")
	}
	return nil
}
