# 807 Fortune Garuda 1000 — 機率介面 v2

2026-11-04 升版：2,399 局全部通過應用層完整 payload 與 SpinAck 的 byte round-trip，以及獨立 Google protobuf codec 重建。這是已觀測資料的結構規格，未完整導出原生前端 codec，也不是正式概率分布。

機率輸入看 `spinReq`，輸出填 `data`；遊戲層回填 `postMoney`、字串 `roundIndexV2`（uint64，末三碼807）。從完整樣本修改，保留零值及空陣列；未知欄位會拒絕，不會靜默丟棄。

## v1 → v2

- `effect_context_f9` 改為重複訊息陣列：缺省為 `[]`，一次為 `[{}]`，兩次為 `[{}, {}]`。每次選到 Ex Nudge 對應一筆；所有已見內文均空。這是 ABI 變更，舊版 null／{values:[]} 必須改用陣列。非空內容尚無定義，adapter 拒絕。
- 新增 `gift_pool_f14`、`upgrade_symbols_f15`、`respin_previous_reel_f16`，皆為 int32 陣列。
- 新增 `ante_mode`：0普通、1額外投注1.5×、2額外投注8×。
- `spinReq.special` 普通模式 `{}`；1.5× 為 `{"ante":{"level":0}}`；8× 為 `{"ante":{"level":1}}`。保留 ante 訊息的出現與否，不能把 level=0 與普通模式混用。wire BetInfo f26 對應此訊息，SpinAck f22 必須一致。
- 基本下注觀測到1.0和3.0；不是所有下注／模式組合都捕獲。mock 依完整 request action 分池，math 回放依基本下注與模式配對，不混播模式。

## SpinAck 欄位

| wire | JSON 名稱 | 定義／證據界線 |
|---|---|---|
| 1 | reels | 三軸各三格，Column.values |
| 2 | nudge_marks | 四軸標記；前三軸各三格。金色 SUPER WILD 位置數字對應抽取數量 |
| 3 | multiplier_reel | 特殊軸完整序列，頭尾各兩格為視窗外側；普通五格中心索引2 |
| 4 | extra_steps | 初始 Ex Nudge 次數 |
| 5 | extra_step_chain | 連鎖追加次數，依序保留 |
| 6 | effect_symbols_f6 | SUPER WILD 選中結果，依實際套用順序；SymbolCount(symbol_id,count) |
| 7 | effect_symbols_f7 | 未選結果；已見 f6+f7 共8筆 |
| 8 | effect_indices_f8 | f6 中 Ex Nudge 的次數，依選中順序 |
| 9 | effect_context_f9 | 每個選中 Ex Nudge 一個空訊息；保留重複筆數，未知內文待案例 |
| 11 | line_wins | Symbol ID、匹配數、線索引、該線含倍率派彩 |
| 12 | win_type | 已見0無贏分、1普通中獎、3 Ex Nudge、5 SUPER WILD；不外推未見 enum |
| 13 | effect_slots_f13 | 五格效果成功參數，見下文 |
| 14 | gift_pool_f14 | 增加特殊軸出現率的候選符號池 |
| 15 | upgrade_symbols_f15 | 升級符號序列；有50→100直接畫面佐證 |
| 16 | respin_previous_reel_f16 | 重轉前主軸三格；已有第三軸成功案例 |
| 17 | effect_slots_f17 | 五格其他／未改善演出參數，不可一概當成沒有觸發 |
| 18 | multiplier | 最終總倍率 |
| 19 | total_win | 線獎加總，與外層總派彩相同 |
| 21 | config_value_f21 | 實測0.97；不據此宣稱正式 RTP |
| 22 | ante_mode | 0／1／2，見上方模式輸入 |

f13/f17 的五格索引0–4：候選池、替換、升級、特殊軸交換／重轉、主軸重轉。f13[1] 已見參數為被替換原符號；f13[3] 位置參數1/2/3/4對應特殊軸索引0/1/3/4，部分位置沿用696結構比對，未全數有807畫面佐證。f13[4] 主軸編號自1起算。

f17[1] 有手持候選但最後未替換、f17[3] 有交換失敗、f17[4]=3 有第三軸確實重轉但零贏分的直接觀察。**f17[2] 尚無非零案例**；不能保證此版本一定會產生。細節與證據信心見 `../handoff/definitions_evidence.json`、`../696_807_FIELD_MAP.md`。

## 倍率與派彩

倍率符號9→1、10→2、11→3、12→5、13→10、14→15、15→20、16→25、17→50、18→100、19→500、20→1000；21為Ex Nudge，不直接貢獻現金倍率。高值符號部分由696結構及807候選畫面比對，不能據此推定每種模式都允許每個值。

普通 Ex Nudge 的序列長度為 `5 + extra_steps + sum(extra_step_chain)`；已見案例最終倍率為特殊軸 `values[2:-2]` 對應倍率總和。SUPER WILD 依f6順序套用固定倍率與Ex Nudge片段；不能把所有固定倍率提前加總後當成動畫順序。例 `2486007347000260807`：初始15 → 加25 → Ex8增加170 → 加20 → Ex15增加295，最終525。

已見線獎符合 `base_bet × symbol_payrate × multiplier / 5`；符號0–6賠率依序1、2、3.5、5、6、7.5、10。額外投注影響實際扣款倍率，base_bet仍為基本下注。adapter 只驗證基本型別、盤面尺寸、模式一致與總派彩加總，不是完整遊戲數學規則驗證器。

## 驗證及回放

```
python games/807/math_adapter.py --selftest
python replay_807.py --selftest
python games/807/verify_math.py
python replay_807.py --source math --rounds 2486007347000260807
```

前端需選該樣本對應的基本下注與模式。全部統計見 `COVERAGE.json`；user-described案例、對照截圖及規則來源在 `../handoff/`。收集到的頻率不能作為正式RTP或機率分布。Windows前端尚未實機驗證。
