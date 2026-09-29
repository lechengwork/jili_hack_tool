package g4102

import (
	"math"
	"testing"

	"dicemath/entity"
	"dicemath/entity/result"
	"dicemath/entity/setting"
	"dicemath/game"
)

const rtpTolerance = 0.001 // ±0.1pp

// TestGetDiceResult_SupportedVersions 測試 server 入口 g4102.GetDiceResult 對版本的處理。
//   - 11 個支援版本都能正常出結果。
//   - 不支援的版本(0800、9999、空字串)回傳 error。
func TestGetDiceResult_SupportedVersions(t *testing.T) {
	for _, v := range Versions() {
		in := result.DiceInput{Version: v}
		in.Bets[entity.Cell7] = 10
		if _, err := GetDiceResult(&in); err != nil {
			t.Errorf("GetDiceResult(version %q) error = %v, want nil", v, err)
		}
	}
	for _, v := range []string{"0800", "9999", ""} {
		in := result.DiceInput{Version: v}
		in.Bets[entity.Cell7] = 10
		if _, err := GetDiceResult(&in); err == nil {
			t.Errorf("GetDiceResult(version %q) error = nil, want error (not supported by 4102)", v)
		}
	}
}

// TestDiceMath_BuiltAtStartup 測試 4102 的內建設定合法，程式啟動時能成功建立引擎。
//   - 啟動時建立引擎的錯誤(diceMathErr)必須為 nil；設定改錯會在這裡直接失敗，不會等到上線才發現。
//   - 機台編號為 4102。
func TestDiceMath_BuiltAtStartup(t *testing.T) {
	if diceMathErr != nil {
		t.Fatalf("newDiceMath() error = %v, want nil (built-in settings must be valid)", diceMathErr)
	}
	if got := diceMath.GetMachineID(); got != MachineID {
		t.Errorf("GetMachineID() = %d, want %d", got, MachineID)
	}
}

// TestTheoryRTP_AllVersionsWithinTolerance 測試每個版本 × 13 格的理論 RTP 都落在目標值 ±0.1pp 內(含 NoExtraRate)。
//   - 企劃從 Excel 替換權重表後，跑這支測試就能確認有沒有超標；也能確保「最佳押法」不會比標示的 RTP 更划算。
func TestTheoryRTP_AllVersionsWithinTolerance(t *testing.T) {
	weights := VersionSettings()
	for _, v := range Versions() {
		target, ok := setting.GetVersionRtp(v)
		if !ok {
			t.Fatalf("version %s not in allow list", v)
		}
		vs, ok := weights[v]
		if !ok {
			t.Fatalf("version %s has no weight table", v)
		}
		rtp := game.TheoryRTP(BaseOdds(), vs.ExtraWeights, vs.NoExtraRate)
		for c := range rtp {
			if math.Abs(rtp[c]-target) > rtpTolerance {
				t.Errorf("version %s cell %s: theory RTP = %.6f, want %.4f ± %.3f", v, entity.CellNames[c], rtp[c], target, rtpTolerance)
			}
		}
	}
}

// TestVersionSettings_CoversExactlySupportedVersions 測試版本設定表的版本數與支援版本清單一致。
//   - 防止 Versions() 有列、versionSettings 卻漏了某個版本(或反過來)。
func TestVersionSettings_CoversExactlySupportedVersions(t *testing.T) {
	weights := VersionSettings()
	if len(weights) != len(Versions()) {
		t.Errorf("VersionSettings() has %d versions, Versions() has %d", len(weights), len(Versions()))
	}
}

// TestBaseOdds_MatchesPacketOrder 測試 4102 的基礎淨賠率與對方封包 base_odds 的順序、數值一致。
//   - 預期 {4, 1, 1, 26, 12, 8, 6, 5, 5, 6, 8, 12, 26}(7, 2~6, 8~12, 2 … 12)。
func TestBaseOdds_MatchesPacketOrder(t *testing.T) {
	want := [entity.CellCount]int{4, 1, 1, 26, 12, 8, 6, 5, 5, 6, 8, 12, 26}
	if got := BaseOdds(); got != want {
		t.Errorf("BaseOdds() = %v, want %v", got, want)
	}
}
