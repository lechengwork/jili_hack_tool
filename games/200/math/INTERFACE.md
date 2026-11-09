# Pappu／4103／JILI 200：給機率團隊

機率填寫入口：`../pappumath/game/g4103/setting_4103.go`。server 直接 import Go module `pappumath`，不需要 RPC、math service 或資料庫。`../pappumath/README.md` 有呼叫方式與測試；本目錄六份單號 JSON 是實包驗證過的參考資料。

## 賠率與本金

區分「淨賠率」和「含本金回收倍數」。文字「1 賠 2」若指淨贏 2，淨賠率填 2、含本金回收為 3：押 100 回收 300、淨贏 200。若產品說的是「總回收 2X」，則填 2，押 100 回收 200。不要只寫未定義的 odds=2。

Pappu 原始前端 PappuGameDefine 的 12 區 odds:[9] 是基礎淨賠率，含本金基礎回收為 10。RoomEnd.bonus[type] 已經是含本金最終回收，直接對應 return_odds[type-1]：

```
0 → 無額外賠付，結算／轉封包時正規化成基礎 10
10 → 押 100 回收 1,000
20 → 押 100 回收 2,000
total_win = bets[winner - 1] × return_odds[winner - 1]
net_win = total_win - 所有注區總下注
```

不用再加本金，也不要再乘 9 或 10。本次單號 644919319188238536，陀螺 type 8 下兩次 100,000，合計 200,000，回收 2,000,000、淨贏 1,800,000。

124 舊介面文件用含本金，後來 Go 引擎 BaseOdds／FinalOdds 用淨賠率、結算才 +1。本模組以 ReturnOdds 明確表達含本金。沿用 124 的程式組織與本金區分，**不套它的 (final-1)/base、整除限制或 extra=1 約定**。Pappu 線路直接帶最終回收；目前見過 10／20／30，不代表完整值域或機率表。

## 注區順序

陣列固定 12 格，畫面由左到右、由上到下；index = 原始 type − 1。前端 areaNodeList 是欄優先遍歷，不能直接拿它當這裡的順序。

| index | type | 圖案／原始 enum |
|---|---|---|
| 0 | 1 | 雨傘 Umbrella |
| 1 | 2 | 足球 Soccer |
| 2 | 3 | 太陽 Sun |
| 3 | 4 | 油燈 Diya／原 enum Candle |
| 4 | 5 | 牛 Bull |
| 5 | 6 | 水桶 Bucket |
| 6 | 7 | 風箏 Kite |
| 7 | 8 | 陀螺 WhippingTop |
| 8 | 9 | 玫瑰 Rose |
| 9 | 10 | 蝴蝶 Butterfly |
| 10 | 11 | 鴿子 Pigeon |
| 11 | 12 | 兔子 Rabbit |

線路 bonus 有 13 格，index 0 是已觀察為 0 的 None 占位，由 adapter 保留；機率陣列不用多留一格。

## JSON 欄位

| 欄位 | 約定 |
|---|---|
| round_id | 原始 wagers 單號，JSON 十進位字串，不可轉 JS Number |
| room_id | 原房間號，本次為 4 |
| currency／currency_code | 本次來源 IDR／原碼 7，不推廣成共用幣別 enum |
| bets[12] | 自己已確認的最終下注，已累加加注／套用撤銷；不混其他玩家 |
| winner | 原始 type 1..12，普通局只有一個中獎圖案 |
| pic | 本次普通局等於 winner；未知特殊表示拒絕套用 |
| return_odds[12] | 含本金最終回收，0 正規化成 10 |
| is_bonus | 原始旗標，本次全 false；有 20X／30X 不代表它應為 true |
| bet_total／total_win／net_win | 總下注／含本金回收／淨損益，必須與結果一致 |
| balance_after | 原始結算後餘額快照，供驗證；錢包由 server 管理 |

金額使用同一個 server 選定的整數單位。這六份 IDR 樣本直接使用原始整數幣值；其他幣別先選定可精確表示的最小單位，不能擅自四捨五入或混幣計算。

## 雙向轉換與驗證

`../math_adapter.py` 的 round_to_math／math_round_to_wire 轉換乾淨資料與完整 RoomEnd Command。完整原始 bytes、欄位是否出現及未知表示只留在本機 webcap/<session>/math_wire/，不放進機率 JSON。未修改資料的整個應用層 frame 必須 byte 相同；修改結果後另用原始前端 codec 解碼驗證。

修改結果後可用 recalculate_round 重算衍生金額。實際回前端時，凍結下注、房間、單號不可改；派彩變更必須由 server 傳入 post_coin，adapter 不會沿用錯誤舊餘額。機率團隊不用處理登入、token 或編碼。

本版是明文 protobuf WebSocket／TLS。原始 Command codec 只有 type/data，已驗的已知 frame 沒有獨立應用層簽章欄位；不捏造 signature=OK。驗證包含原始 codec、完整 frame round-trip、自己的 uid／請求回應關聯、原始房間單號、賠付與餘額。未知欄位、未配對回應、特殊模式保留原始資料並拒絕發布。

沒自己下注的房間結果不算成功樣本。下次擷取已串接每局即時原子輸出；修改過的同單號不覆蓋，原始結果留 session 並記錄衝突。finish 只重驗、補轉與彙整。

## 機率團隊要填的部分

- 正式版本代碼、目標 RTP，以及圖案和完整回收表的聯合機率權重。
- 六局不足以推導 RTP、抽樣規律或完整 EXTRA 值域。
- isBonus=true、多個 reward、pic 與 winner 不一致目前拒絕執行；有規格或實包後再擴充，不借用 124 假演出規則。
