package g4102

import (
	"fmt"
	"math"
	"os"
	"testing"

	"dicemath/entity"
	"dicemath/game"
	"dicemath/simulator"
)

// DICE_SIM=1 go test -run "^Test_RTPConvergence$" -v -timeout 48h
// PowerShell：$env:DICE_SIM=1; go test -run "^Test_RTPConvergence$" -v -timeout 48h

const simulationRounds = 10_000_000

// Test_RTPConvergence 對 4102 每個版本各跑 1000 萬局蒙地卡羅模擬，輸出報表 4102_rtp_version{版本}.txt。
//   - 報表內容：13 格的理論 RTP 與實測 RTP、點數 2~12 的理論與實測機率、畫面亮格數 0~13 的分佈。
//   - 用來確認實作沒有 bug(實測應收斂到理論值)，以及檢視畫面亮格的節奏。
//   - 耗時數分鐘，預設不跑；需設定環境變數 DICE_SIM=1。
func Test_RTPConvergence(t *testing.T) {
	if os.Getenv("DICE_SIM") == "" {
		t.Skip("set DICE_SIM=1 to run the 4102 simulation")
	}
	for _, version := range Versions() {
		sim := simulator.NewSimulator(GetDiceResult, version)
		if err := sim.Simulate(simulationRounds); err != nil {
			t.Fatalf("version %s: Simulate() error = %v", version, err)
		}
		if err := writeReport(version, sim); err != nil {
			t.Fatalf("version %s: writeReport error = %v", version, err)
		}
		t.Logf("version %s: 模擬完成", version)
	}
}

// writeReport 輸出單一版本的模擬報表
func writeReport(version string, sim *simulator.Simulator) error {
	f, err := os.Create(fmt.Sprintf("4102_rtp_version%s.txt", version))
	if err != nil {
		return err
	}
	defer f.Close()

	fmt.Fprintf(f, "machineId\t%d\n", MachineID)
	fmt.Fprintf(f, "version\t%s\n", version)
	fmt.Fprintf(f, "totalRound\t%d\n\n", sim.Rounds)

	theory := game.TheoryRTP(BaseOdds(), VersionSettings()[version].ExtraWeights, VersionSettings()[version].NoExtraRate)
	simRTP := sim.CellRTP()
	fmt.Fprintln(f, "cell\ttheoryRTP\tsimRTP")
	for c := 0; c < entity.CellCount; c++ {
		fmt.Fprintf(f, "%s\t%.4f\t%.4f\n", entity.CellNames[c], theory[c], simRTP[c])
	}
	fmt.Fprintln(f)

	sumProb := sim.SumProb()
	fmt.Fprintln(f, "sum\ttheoryProb\tsimProb")
	for s := 2; s <= 12; s++ {
		theoryProb := float64(6-int(math.Abs(float64(s-7)))) / 36
		fmt.Fprintf(f, "%d\t%.4f\t%.4f\n", s, theoryProb, sumProb[s])
	}
	fmt.Fprintln(f)

	fmt.Fprintln(f, "litCount\tsimProb")
	for k, p := range sim.LitCountProb() {
		fmt.Fprintf(f, "%d\t%.4f\n", k, p)
	}
	return nil
}
