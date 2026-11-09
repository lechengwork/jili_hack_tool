package game

import (
	"crypto/rand"
	"errors"
	"fmt"
	"math"
	"math/big"

	"pappumath/entity"
	"pappumath/entity/result"
	"pappumath/entity/setting"
)

var ErrSettingsNotReady = errors.New("Pappu probability settings are not filled")
var ErrSpecialModeUnsupported = errors.New("Pappu special bonus mode is not yet specified")

type RNG func(max uint64) (uint64, error)
type table struct {
	outcomes []setting.WeightedOutcome
	total    uint64
}
type PappuMath struct{ versions map[string]table }

// NewPappuMath validates and copies settings. Subsequent calls only read immutable tables.
func NewPappuMath(settings map[string]setting.VersionSetting) (*PappuMath, error) {
	if len(settings) == 0 {
		return nil, ErrSettingsNotReady
	}
	m := &PappuMath{versions: make(map[string]table, len(settings))}
	for version, vs := range settings {
		if version == "" {
			return nil, errors.New("empty version")
		}
		if len(vs.Outcomes) == 0 {
			return nil, fmt.Errorf("version %s: %w", version, ErrSettingsNotReady)
		}
		vt := table{outcomes: append([]setting.WeightedOutcome(nil), vs.Outcomes...)}
		for i := range vt.outcomes {
			x := &vt.outcomes[i]
			normalized, err := NormalizeOutcome(x.Outcome)
			if err != nil {
				return nil, fmt.Errorf("version %s outcome %d: %w", version, i, err)
			}
			x.Outcome = normalized
			if x.Weight > math.MaxUint64-vt.total {
				return nil, errors.New("weight sum overflows uint64")
			}
			vt.total += x.Weight
		}
		if vt.total == 0 {
			return nil, errors.New("sum of outcome weights must be positive")
		}
		m.versions[version] = vt
	}
	return m, nil
}

func NormalizeOutcome(in result.Outcome) (result.Outcome, error) {
	if !in.Winner.Valid() {
		return result.Outcome{}, errors.New("winner must be a Pappu area 1..12")
	}
	if in.IsBonus {
		return result.Outcome{}, ErrSpecialModeUnsupported
	}
	if in.Pic != int32(in.Winner) {
		return result.Outcome{}, errors.New("ordinary-round pic must match winner")
	}
	for i, v := range in.ReturnOdds {
		if v == 0 {
			in.ReturnOdds[i] = entity.BaseReturnOdds
			continue
		}
		if v < entity.BaseReturnOdds {
			return result.Outcome{}, fmt.Errorf("return odds[%d] must be 0 or >=10", i)
		}
	}
	return in, nil
}

// NetToReturnOdds names the convention explicitly: net odds 1:2 -> gross return 3.
func NetToReturnOdds(net int64) (int64, error) {
	if net < 0 || net == math.MaxInt64 {
		return 0, errors.New("invalid net odds")
	}
	return net + 1, nil
}

func betTotal(bets entity.Bets) (int64, error) {
	var total int64
	for i, b := range bets {
		if b < 0 {
			return 0, fmt.Errorf("bet[%d] must not be negative", i)
		}
		if b > math.MaxInt64-total {
			return 0, errors.New("bet total overflows int64")
		}
		total += b
	}
	if total == 0 {
		return 0, errors.New("all final bets are zero")
	}
	return total, nil
}

// Settle is deterministic and consumes no RNG. Freeze bets before calling.
func Settle(bets entity.Bets, outcome result.Outcome) (*result.PappuOutput, error) {
	total, err := betTotal(bets)
	if err != nil {
		return nil, err
	}
	o, err := NormalizeOutcome(outcome)
	if err != nil {
		return nil, err
	}
	bet, odds := bets[o.Winner.Index()], o.ReturnOdds[o.Winner.Index()]
	if bet > math.MaxInt64/odds {
		return nil, errors.New("payout overflows int64")
	}
	win := bet * odds
	out := &result.PappuOutput{Winner: o.Winner, FinalReturnOdds: o.ReturnOdds, Pic: o.Pic, IsBonus: o.IsBonus, BetTotal: total, TotalWin: win, NetWin: win - total}
	for i := range out.BaseReturnOdds {
		out.BaseReturnOdds[i] = entity.BaseReturnOdds
	}
	return out, nil
}

func cryptoRNG(max uint64) (uint64, error) {
	if max == 0 {
		return 0, errors.New("RNG bound is zero")
	}
	n, err := rand.Int(rand.Reader, new(big.Int).SetUint64(max))
	if err != nil {
		return 0, err
	}
	return n.Uint64(), nil
}

func (m *PappuMath) DrawRound(version string) (*result.Outcome, []uint64, error) {
	return m.DrawRoundWithRNG(version, cryptoRNG)
}

// DrawRoundWithRNG permits reproducible tests/server RNG integration. The caller's
// RNG must be safe for its own usage; the engine stores neither RNG nor player bets.
func (m *PappuMath) DrawRoundWithRNG(version string, rng RNG) (*result.Outcome, []uint64, error) {
	if m == nil {
		return nil, nil, ErrSettingsNotReady
	}
	vt, ok := m.versions[version]
	if !ok {
		return nil, nil, fmt.Errorf("unsupported version %q", version)
	}
	if rng == nil {
		return nil, nil, errors.New("nil RNG")
	}
	x, err := rng(vt.total)
	if err != nil {
		return nil, nil, err
	}
	if x >= vt.total {
		return nil, nil, errors.New("RNG result outside [0,total weight)")
	}
	remaining := x
	for _, entry := range vt.outcomes {
		if remaining < entry.Weight {
			o := entry.Outcome
			return &o, []uint64{x}, nil
		}
		remaining -= entry.Weight
	}
	return nil, nil, errors.New("invalid weighted table")
}

// GetPappuResult is the 124-style convenience entry for a single player only.
// Shared rooms MUST use one DrawRound + Settle for each player, or GetRoomResult.
func (m *PappuMath) GetPappuResult(in *result.PappuInput) (*result.PappuOutput, error) {
	if in == nil {
		return nil, errors.New("nil input")
	}
	if _, err := betTotal(in.Bets); err != nil {
		return nil, err
	}
	o, used, err := m.DrawRound(in.Version)
	if err != nil {
		return nil, err
	}
	out, err := Settle(in.Bets, *o)
	if err != nil {
		return nil, err
	}
	out.UsedRNG = used
	return out, nil
}

func (m *PappuMath) GetRoomResult(in *result.RoomInput) (*result.RoomOutput, error) {
	if in == nil {
		return nil, errors.New("nil room input")
	}
	for _, bets := range in.Players {
		if _, err := betTotal(bets); err != nil {
			return nil, err
		}
	}
	o, used, err := m.DrawRound(in.Version)
	if err != nil {
		return nil, err
	}
	out := &result.RoomOutput{Outcome: *o, UsedRNG: used, Players: make([]result.PappuOutput, len(in.Players))}
	for i, bets := range in.Players {
		p, err := Settle(bets, *o)
		if err != nil {
			return nil, err
		}
		out.Players[i] = *p
	}
	return out, nil
}

// TheoryRTP reports per-area E[gross return] from the configured joint distribution.
func (m *PappuMath) TheoryRTP(version string) ([entity.AreaCount]float64, error) {
	var out [entity.AreaCount]float64
	if m == nil {
		return out, ErrSettingsNotReady
	}
	vt, ok := m.versions[version]
	if !ok {
		return out, fmt.Errorf("unsupported version %q", version)
	}
	for _, x := range vt.outcomes {
		i := x.Outcome.Winner.Index()
		out[i] += float64(x.Weight) / float64(vt.total) * float64(x.Outcome.ReturnOdds[i])
	}
	return out, nil
}

// ValidateRTP checks EVERY betting area, not the average over twelve areas.
func (m *PappuMath) ValidateRTP(version string, target, tolerance float64) error {
	if math.IsNaN(target) || math.IsInf(target, 0) || target <= 0 || math.IsNaN(tolerance) || math.IsInf(tolerance, 0) || tolerance < 0 {
		return errors.New("approved target RTP must be positive and tolerance must be finite/nonnegative")
	}
	rtp, err := m.TheoryRTP(version)
	if err != nil {
		return err
	}
	for i, value := range rtp {
		if math.Abs(value-target) > tolerance {
			return fmt.Errorf("version %s area %d RTP %.9f outside target %.9f +/- %.9f", version, i+1, value, target, tolerance)
		}
	}
	return nil
}
