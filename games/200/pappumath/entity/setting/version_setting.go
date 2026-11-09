package setting

import "pappumath/entity/result"

// One weighted joint outcome holds the winner AND the full final-return-odds table.
// Probability staff fill this distribution. No independence assumption is imposed.
type WeightedOutcome struct {
	Weight  uint64
	Outcome result.Outcome
}

type VersionSetting struct {
	Outcomes     []WeightedOutcome
	TargetRTP    float64 // approved gross-return RTP, e.g. 0.97; required by g4103
	RTPTolerance float64 // absolute tolerance, e.g. 0.001 = 0.1 percentage points
}
