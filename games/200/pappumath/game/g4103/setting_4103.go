package g4103

import "pappumath/entity/setting"

const MachineID = 4103
const JILIGameID = 200

// Probability staff fill this map, one approved RTP version per key.
// Intentionally empty: no production probabilities/RTP are inferred from six rounds.
// Outcome.ReturnOdds is a 12-cell GROSS-return table. 0 -> base return 10.
// Examples of units: 20 means bet 100 returns 2000; it is not an EXTRA factor 20.
// Tests contain deterministic tables as fixtures ONLY, never used by this map.
// Each production version must also fill TargetRTP and RTPTolerance. Startup checks
// EVERY betting area against them; no approved target is inferred here.
var versionSettings = map[string]setting.VersionSetting{}

func VersionSettings() map[string]setting.VersionSetting {
	out := make(map[string]setting.VersionSetting, len(versionSettings))
	for key, value := range versionSettings {
		value.Outcomes = append([]setting.WeightedOutcome(nil), value.Outcomes...)
		out[key] = value
	}
	return out
}
