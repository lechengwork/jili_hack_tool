package randomNumber

import (
	"reflect"
	"testing"
)

// TestRNG_InjectedSequence 測試 RNG 的注入序列與取值規則(所有單元測試都靠這個規則控制結果)。
//   - GetRandomIntMax(6) 注入 7 → 回傳 7 % 6 = 1。
//   - GetRandomIndexWeight 會依序扣權重決定 index，權重 0 的項目會被跳過。
//   - CopyUsedRNG 回傳實際用過的亂數，順序與注入相同。
func TestRNG_InjectedSequence(t *testing.T) {
	r := NewRNG()
	r.SetIntList([]int{7, 1, 3})

	got, err := r.GetRandomIntMax(6)
	if err != nil || got != 1 { // 7 % 6
		t.Fatalf("GetRandomIntMax(6) = %d, %v, want 1, nil", got, err)
	}

	idx, err := r.GetRandomIndexWeight([]int{1, 1, 0, 0})
	if err != nil || idx != 1 { // 1 % 2 = 1 → 扣掉 w[0]=1 後落在 index 1
		t.Fatalf("GetRandomIndexWeight([1 1 0 0]) = %d, %v, want 1, nil", idx, err)
	}

	idx, err = r.GetRandomIndexWeight([]int{1, 0, 1})
	if err != nil || idx != 2 { // 3 % 2 = 1 → 跳過權重 0 的 index 1，落在 index 2
		t.Fatalf("GetRandomIndexWeight([1 0 1]) = %d, %v, want 2, nil", idx, err)
	}

	if used := r.CopyUsedRNG(); !reflect.DeepEqual(used, []int{7, 1, 3}) {
		t.Errorf("CopyUsedRNG() = %v, want [7 1 3]", used)
	}
}

// TestRNG_GetRandomIndexWeight_InvalidSum 測試權重總和為 0 時，GetRandomIndexWeight 回傳 error 而不是亂選。
func TestRNG_GetRandomIndexWeight_InvalidSum(t *testing.T) {
	r := NewRNG()
	if _, err := r.GetRandomIndexWeight([]int{0, 0}); err == nil {
		t.Error("GetRandomIndexWeight([0 0]) error = nil, want error")
	}
}
