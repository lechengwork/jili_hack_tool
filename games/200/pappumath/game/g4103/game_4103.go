package g4103

import (
	"fmt"
	"pappumath/entity/result"
	"pappumath/game"
)

var pappuMath, pappuMathErr = newPappuMath()

func newPappuMath() (*game.PappuMath, error) {
	settings := VersionSettings()
	m, err := game.NewPappuMath(settings)
	if err != nil {
		return nil, err
	}
	for version, vs := range settings {
		if err := m.ValidateRTP(version, vs.TargetRTP, vs.RTPTolerance); err != nil {
			return nil, fmt.Errorf("g4103 production settings: %w", err)
		}
	}
	return m, nil
}

// GetPappuResult is a local Go call, with no RPC, network or database access.
func GetPappuResult(in *result.PappuInput) (*result.PappuOutput, error) {
	if pappuMathErr != nil {
		return nil, pappuMathErr
	}
	return pappuMath.GetPappuResult(in)
}

// GetRoomResult draws once per room. All players receive the same winning picture.
func GetRoomResult(in *result.RoomInput) (*result.RoomOutput, error) {
	if pappuMathErr != nil {
		return nil, pappuMathErr
	}
	return pappuMath.GetRoomResult(in)
}
