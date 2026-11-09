package g4103

import (
	"errors"
	"pappumath/entity"
	"pappumath/entity/result"
	"pappumath/game"
	"testing"
)

func TestBuiltInSettingsReadiness(t *testing.T) {
	_, err := GetPappuResult(&result.PappuInput{Version: "0970", Bets: entity.Bets{100}})
	if len(VersionSettings()) == 0 {
		if !errors.Is(err, game.ErrSettingsNotReady) {
			t.Fatalf("unfilled tables must fail closed: %v", err)
		}
	} else if pappuMathErr != nil {
		t.Fatal(pappuMathErr)
	}
	if MachineID != 4103 || JILIGameID != 200 {
		t.Fatal("platform and original game IDs were mixed")
	}
}
