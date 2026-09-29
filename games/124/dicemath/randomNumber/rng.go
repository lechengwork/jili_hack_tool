package randomNumber

import (
	"errors"
	"fmt"
	"math/rand"
)

// MAX_RNG_VALUE RNG 精準度上限(比照 lib/survivalroad/randomNumber/rng.go)
const MAX_RNG_VALUE = 100_000_000

// RNG 亂數產生器(比照 lib/survivalroad/randomNumber/rng.go 複製)
type RNG struct {
	MAX_RNG_VALUE int
	intList       []int // 將要使用的rng(供測試注入固定序列)
	usedRNG       []int // 已經使用的rng(供稽核/重現)
}

// NewRNG 產生一個亂數產生器
func NewRNG() *RNG {
	return &RNG{
		MAX_RNG_VALUE: MAX_RNG_VALUE,
	}
}

// SetIntList 設定要使用的rng(測試/重現用)
func (r *RNG) SetIntList(list []int) {
	r.intList = list
}

// CopyUsedRNG 傳出目前已使用的rng
func (r *RNG) CopyUsedRNG() []int {
	result := make([]int, len(r.usedRNG))
	copy(result, r.usedRNG)
	return result
}

// GetRandomIntMax 隨機產生一個 [0~max) 的數，取得盡可能均勻的隨機數，並檢查是否超過RNG設定上限
func (r *RNG) GetRandomIntMax(max int) (int, error) {
	if max > r.MAX_RNG_VALUE || max <= 0 {
		return 0, errors.New("max value is not supported")
	}
	bound := r.MAX_RNG_VALUE - (r.MAX_RNG_VALUE % max)
	var temp int
	for {
		temp = r.generateRNG()
		if temp < bound {
			break
		}
	}
	return temp % max, nil
}

// GetRandomIndexWeight 依照weight的內容當權重，回傳對應index
func (r *RNG) GetRandomIndexWeight(weights []int) (int, error) {
	sum := 0
	for _, w := range weights {
		sum += w
	}
	if sum > r.MAX_RNG_VALUE || sum <= 0 {
		return -1, fmt.Errorf("sum of weights is invalid, weights: %v, sum: %d", weights, sum)
	}

	index, err := r.GetRandomIntMax(sum)
	if err != nil {
		return -1, errors.New("sum of weights is not supported")
	}

	for i, w := range weights {
		if index < w {
			return i, nil
		}
		index -= w
	}
	return -1, errors.New("no result")
}

// generateRNG 產生一個隨機數
func (r *RNG) generateRNG() int {
	var result int
	if len(r.intList) != 0 {
		result = r.intList[0]
		r.intList = r.intList[1:]
	} else {
		result = rand.Intn(r.MAX_RNG_VALUE)
	}
	r.usedRNG = append(r.usedRNG, result)
	return result
}
