package dice

import (
	"reflect"
	"testing"
)

// 這個沙盒刻意不依賴任何第三方套件（連 testify 都不用），
// cd 進來 go test ./... 就能跑，不必連網抓 module。
// 下面是最小的斷言工具。

// assertEq 不相等就記錯，繼續跑。
func assertEq[T comparable](t *testing.T, got, want T, format string, args ...any) bool {
	t.Helper()
	if got != want {
		t.Errorf("got %v, want %v — "+format, append([]any{got, want}, args...)...)
		return false
	}
	return true
}

// requireEq 不相等就中止這支測試。
func requireEq[T comparable](t *testing.T, got, want T, format string, args ...any) {
	t.Helper()
	if got != want {
		t.Fatalf("got %v, want %v — "+format, append([]any{got, want}, args...)...)
	}
}

// requireDeepEq 用於 slice / array 比較，不相等就中止。
func requireDeepEq(t *testing.T, got, want any, format string, args ...any) {
	t.Helper()
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %v, want %v — "+format, append([]any{got, want}, args...)...)
	}
}

// assertDeepEq 用於 slice / array 比較，不相等就記錯。
func assertDeepEq(t *testing.T, got, want any, format string, args ...any) {
	t.Helper()
	if !reflect.DeepEqual(got, want) {
		t.Errorf("got %v, want %v — "+format, append([]any{got, want}, args...)...)
	}
}

// requireInRange 中止版的範圍檢查。
func requireInRange(t *testing.T, got, lo, hi int, format string, args ...any) {
	t.Helper()
	if got < lo || got > hi {
		t.Fatalf("got %d, 應在 %d..%d 之間 — "+format, append([]any{got, lo, hi}, args...)...)
	}
}

// assertLess 小於才過。
func assertLess(t *testing.T, got, limit float64, format string, args ...any) {
	t.Helper()
	if !(got < limit) {
		t.Errorf(format, args...)
	}
}
