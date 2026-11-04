# 518 機率輸入／輸出介面

交付以 `../math_518.proto` 為準。輸入 `spinReq`，機率只產出 `data`（SpinAck）。
`service`、`postMoney`、`roundIndexV2` 是遊戲層信封，機率不負責加密、單號或錢包結算。

## JSON 外圈與輸入

外圈固定五格：`data / service / postMoney / roundIndexV2 / spinReq`，和 696 交付習慣一致。
`roundIndexV2` 是 **字串**，不能轉成 JavaScript Number；樣本是 19 位、尾碼 518。
`service` 在本批恆為 `{}`。

```json
{"bet":0.3,"special":{}}
```

另一個請求形狀只出現一次：

```json
{"bet":0.1,"special":{"context23":{"field1":0,"field2":0,"field3":4.65}}}
```

`context23` 是工程保留的數值上下文，原始業務名稱尚未確認；不要刪除、改名或讓機率臆測它的 enum 意義。
原始前端 request 另外帶三個恆為 0 的 options，response 裡是空包；這些通訊細節由遊戲層處理，不放進機率 JSON。
field3 與此一筆相鄰錢包變化推導出的實扣吻合，**不是證明所有特色下注都用同一公式**；不可將本批所有 `bet` 直接相加當成完整實扣總額計算 RTP。

## 輸出 data = SpinAck

所有已定義欄位固定保留；沒有值就填 `0 / false / []`。JSON 若由 protobuf 工具輸出，請包含預設值。
全介面沒有 bytes、hex、金鑰或傳輸 envelope。

| 欄位 | 型別 | 說明／證據 |
|---|---|---|
| RoundQueue | RoundInfo[] | 一次回應中的回合序列，順序就是演出順序 |
| FreeTotalWin | double | 原始免費總贏分；唯一特色樣本為 0.72 |
| BuyType | int32 | 原欄位碼；151 筆恆 0，不猜其他值 |
| TotalWin | double | = sum(RoundQueue[].RoundWin)，151 筆相符 |
| AckType | int32 | 原欄位碼；151 筆恆 0，不猜其他值 |
| RTP | double | 151 筆恆 0.972；只是封包欄位，不是這批小樣本估算的 RTP |
| LID / RID | int32 | 原始識別欄位，保留樣本／預設值，語意未驗證 |

### RoundInfo

| 欄位 | 型別 | 說明 |
|---|---|---|
| ComboStageData | ComboStageInfo[] | 本回合的盤面／連消階段，勿排序或刪掉收尾階段 |
| RoundWin | double | = sum(ComboStageData[].ComboStageWin)，161 回合相符 |
| ScatterCount | int32 | 原始 scatter 計數 |
| FreeRemainRound | int32 | 原始免費剩餘回合欄位 |
| FreeTotalRound | int32 | 原始免費總回合欄位 |
| AddRounds | int32 | 原始新增回合欄位 |
| AwardTypeFlag | int32 | 原始旗標，實測 3/4/5/8/9/12；尚不替它們命名 |
| MaxFlag | bool | 原始上限旗標，保持樣本語意 |

唯一特色回應含 **11 個 RoundInfo**：第一個是觸發回合，後面 10 個免費回合。
其 FreeTotalRound=10，FreeRemainRound 由 10 到 0，第一個 AddRounds=10；這只是本筆實證，不能當成所有免費玩法固定規則。

### ComboStageInfo

| 欄位 | 型別 | 說明 |
|---|---|---|
| ComboStageSymbol | Column[] | 6 組主盤面；219 個 stage 的 Col 長度皆為 `[3,4,5,5,4,3]` |
| ComboMult | double | 原始階段倍率，實測 1/2/4/8/16 |
| ComboStageWin | double | = sum(AwardDataVec[].Win)，219 個 stage 相符 |
| AwardDataVec | AwardData[] | 原始中獎記錄 |
| FillSymbols | Column[] | 原始補入符號序列；保留空欄與位置 |
| NeedEliminate | bool | 原始消除標記 |
| Eliminate | Column[] | 原始消除資料；Col 中的整數不要自行改成 bool |
| IsMain | bool | 原始主遊戲標記 |
| MaxFlag | bool | 原始上限標記 |

Column 只有 `repeated int32 Col`。盤面符號實測出現 0–7、10–17、20–21；保留完整 ID，
不要做 `%10`、不要任意合併符號。它們的美術／特殊形態對應尚未在本次交付定案。
不要用可見陣列長度去反推 4096 ways 的算法；本文件只確認封包佈局，沒有重建支付規則。

### AwardData

`Symbol / Count / LineNum` 為 int32，`Win` 為 double，`Pos` 為 int32[]。
以上沿用前端原欄位名稱。Pos 的座標編碼、Count／LineNum 的完整業務意義尚未驗證，請保留樣本，不能直接套用 696 的支付線索引。

## 改資料與驗證

```text
python games/518/math_adapter.py --selftest
python replay_518.py --source math --rounds 2484635253000060518
```

修改獎金時須同時維持 Award Win → Stage Win → Round Win → TotalWin 的加總。
adapter 不會幫忙產生符號、消除位置、補牌或重新算機率，也不會再次把金額乘上 ComboMult。
它會拒絕漏欄、未知鍵、錯誤型別、NaN、錯誤盤面維度和金額不一致，避免把錯誤資料送進前端。

程式介面（檔案位於 `games/518/math_adapter.py`）：

```python
env = wire_to_math(decrypted_game_payload)
wire = math_to_wire(env)
```

這裡的 wire 是**已解密的遊戲 payload 信封**，不是網路上的加密回應。
對機率服務而言只需接收 `env['spinReq']`、產出 `env['data']`；正式服務由遊戲層填寫餘額與新單號，再交加密層。
