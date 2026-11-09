# 545 機率介面與證據

`math_adapter.py`提供`wire_to_math(payload)`／`math_to_wire(json)`；payload為已解密回應內的應用層f5，不是密文或整個加密信封。

| JSON | 線路依據／處理 |
|---|---|
| data | 外層f1，原始cc3x3Proto.SpinAck；9個message的欄名、型別、欄號由實際前端codec抽出，逐局交叉驗證 |
| service | 外層f2，整數陣列原樣保留；目前只有空內容，不推定內文schema |
| postMoney | 外層f6，double，原包餘額 |
| roundIndexV2 | 外層f20，uint64以十進位字串避免JS精度損失，實測尾碼545 |
| spinReq.bet | 外層f23內f1，double，基本下注；不自算實扣金額 |
| spinReq.context | f23內f25，整數陣列；回應echo中目前皆空，請求中為UI上下文，非模式輸入 |
| spinReq.featureOption | f23內f26；**缺席**、**空message(selector預設0)**、**f1=1**三種實測結構。selector為中性欄名，不稱為696的ante |
| _wire | 各層原始protobuf的整數陣列工程側錄；保留欄位順序、存在性、未知欄位與原始數值表示，不能當成新結果的盤面欄位 |

`data.RoundInfo`為ComboStageInfo列表，不等同696結構。Symbol／FinalSymbol是Column.Col整數陣列，Mul／FinalMul是ColumnM.Col double陣列；已觀察3列各3格，但尚未逐一人工比對畫面方向。CollectList、MysteryList、AwardDataVec、PotList均已有非空樣本，名稱沿用原codec；符號ID、獎池enum與位置索引語意仍需規則／更多畫面比對。

已觀察：f26缺席時GameType／Extra為0／0；空f26時為1／1；f26.f1=1時為2／2。這是樣本關聯，不代表已確認完整enum或扣款倍率。機率團隊可修改selector及結果欄位；前端輸入仍需選相同模式。保留`featureOption={}`代表缺席；`featureOption={"selector":0}`代表空message的選項0。

回應外層f3若存在，與data.TotalWin相同；adapter在回寫時同步，未對盤面自算中獎。`ShowIndex`是字串，`NowMoney`／RTP沿用原codec型別；不得將RTP欄位直接當成已驗證的長期返還率。

已捕獲重轉局`2487517748000020545`：五階段，GetReSpin首次true，ReSpinRemainRound為3/3/2/1/0，ReSpinTotalRound為0/1/2/3/4。尚缺更多自然／各模式觸發、加次數、多次重轉、各獎池與邊界結果；此單一例不代表完整覆蓋。

修改結果時保留`_wire`；命名欄位具有優先權，adapter不會因sidecar仍是原包就忽略修改。未知欄位沒有被靜默丟掉，會在原位置留下；新命名欄位必須先加入schema才能編碼。可用`clean()`取得只含命名欄位的分析視圖，但不要用清掉sidecar的分析副本覆蓋捕獲樣本，以免失去未知欄位與模式存在性。

`math_545.proto`是機率介面；`cc3x3_545.proto`是原始內層遊戲資料。機率proto中的_wire=1000只描述JSON工程側錄，不會被adapter送到原站協定。來源幣別在`../math_sources.json`，USD／THB不可混算；尚未推導各模式實扣倍率或估計RTP。
