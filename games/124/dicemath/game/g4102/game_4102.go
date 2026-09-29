package g4102

import (
	"fmt"

	"dicemath/entity/result"
	"dicemath/game"
)

// diceMath 機台 4102 的數學引擎實體，程式啟動(套件載入)時建立一次，之後所有呼叫共用。
// 內建設定(賠率、各版本 NoExtraRate／權重表／亮格數分佈)有誤時不 panic，錯誤存在 diceMathErr，由 GetDiceResult 回傳。
var diceMath, diceMathErr = newDiceMath()

func newDiceMath() (*game.DiceMath, error) {
	m, err := game.NewDiceMath(MachineID, BaseOdds(), VersionSettings())
	if err != nil {
		return nil, fmt.Errorf("g4102: invalid built-in settings: %w", err)
	}
	return m, nil
}

// GetDiceResult 機台 4102 單局結果，server 只需要呼叫這個函式。
// in.Version 為 RTP 版本(例如 "0970")；版本不支援、任一格下注 < 0、13 格下注全為 0，
// 或內建設定有誤(啟動時建立引擎失敗)時回傳錯誤。
//
// 併發安全：每次呼叫都使用新的 RNG 實例，彼此不共用任何可變狀態。
// 回傳的 UsedRNG 可推算出真假 EXTRA，只能寫入 server log，不可轉發給前端。
func GetDiceResult(in *result.DiceInput) (*result.DiceOutput, error) {
	if diceMathErr != nil {
		return nil, diceMathErr
	}
	return diceMath.GetDiceResult(in)
}
