package dice

import "fmt"

// 這個檔案是遊戲層的事，機率端不用看。
//
// 機率端的世界與原廠封包的世界差在三點，全部在這裡收掉：
//
//	              機率端                          原廠封包
//	賠率形式      含本金(1:18 那格 = 19)          顯示賠率 N(= 18) + extra 倍數
//	沒蓋 EXTRA    0                               1.0
//	注點順序      畫面順序(2-6 開頭)              和/小/大 開頭
//
// 實測 29 局做「封包 → 機率端形式 → 封包」來回轉換 100% 還原，見 adapter_test.go。

// uiToPkt 畫面順序 → 原廠封包 position。
//
// ★ 只有前兩格互換，index 3..12 完全一樣。漏掉的話 13 格有 11 格都對，
// 只有押「7」和押「2-6」會錯，而且是互相拿對方的賠率與 extra
// （押 7 中了只賠 2 倍而不是 5 倍）。測試專門測這兩格。
//
// 這張表是自反的，所以封包轉回畫面順序用同一張表。
var uiToPkt = [PosCount]int{1, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}

// ToPacket 把機率端的結果轉成原廠封包格式。
//
// pktBase 對應 GameConfig(cmd 23) f3，pktExtra 對應 Result(cmd 22) f5，
// 兩者都已經是封包順序，可以直接塞進封包。
func ToPacket(out *DiceOutPut, baseOdds []int) (pktBase [PosCount]int, pktExtra [PosCount]float64, err error) {
	if len(out.ExtraMults) != PosCount || len(baseOdds) != PosCount {
		return pktBase, pktExtra, fmt.Errorf("長度必須是 %d，得到 extra=%d base=%d",
			PosCount, len(out.ExtraMults), len(baseOdds))
	}

	for ui := 0; ui < PosCount; ui++ {
		pkt := uiToPkt[ui]
		pktBase[pkt] = baseOdds[ui] - 1 // 含本金 → 顯示賠率 N

		if out.ExtraMults[ui] == 0 {
			pktExtra[pkt] = 1 // ★ 封包用 1.0 表示沒蓋 EXTRA，不是 0
			continue
		}

		display := out.ExtraMults[ui] - 1 // 畫面要顯示的 1:N 的 N
		if pktBase[pkt] <= 0 || display%pktBase[pkt] != 0 {
			return pktBase, pktExtra, fmt.Errorf(
				"注點 %s(畫面 %d/封包 %d): 最終賠率 %d 減 1 後的 %d 不是基礎賠率 %d 的整數倍，封包無法乾淨表示",
				PosNames[ui], ui, pkt, out.ExtraMults[ui], display, pktBase[pkt])
		}
		pktExtra[pkt] = float64(display / pktBase[pkt])
	}
	return pktBase, pktExtra, nil
}

// ToPacketPositions 把中獎注點從畫面順序轉成封包順序（對應 Result.f4 won_positions）。
func ToPacketPositions(uiPositions []int) []int {
	out := make([]int, 0, len(uiPositions))
	for _, ui := range uiPositions {
		out = append(out, uiToPkt[ui])
	}
	return out
}

// FromPacketOdds 把封包的基礎賠率（顯示賠率 N、封包順序）轉成機率端要的
// 含本金、畫面順序形式。
func FromPacketOdds(pktBase []int) (baseOdds [PosCount]int) {
	for ui := 0; ui < PosCount; ui++ {
		baseOdds[ui] = pktBase[uiToPkt[ui]] + 1
	}
	return baseOdds
}
