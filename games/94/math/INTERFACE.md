# JILI Rummy（遊戲號 94 / 平台 111000094）— 機率團隊介面

> 看 `games/94/math/` 下每局一個 `<round_id>.json`（＋彙整 `all.jsonl`）算 RTP。
> 2026-10-01 由真實對局逆向並實證（6 局完整：2 勝 4 負，金流公式 100% 吻合）。線路層定義見 `games/94/ws_rummy.proto`。

## 一句話
**2 副牌的印度 Points Rummy（13 張）＋錦標賽**。伺服器權威發牌（RNG），明文 protobuf（無加密）。
非拉霸 → **沒有單一 spinresult**；每局的「結果」= 各家亮牌組合 + 分數 + 金流。

## 怎麼自己產資料
```
cd <repo>            # jili_hack_tool
./wscapture.sh 94     # 自動切VPN→產token→開Chrome;進牌桌打你要的局數(別開DevTools)
#   收工:關 server/Chrome
./wscapture_finish.sh 94   # → games/94/math/<round_id>.json + all.jsonl
```
（抓越多局，牌分佈/鬼牌率/drop 行為的統計越準。）

## ★金流模型（已實證，算 RTP 用這個）★
設某局你的分數 = `S0`，其他家分數和 = `Σothers`：
- **每分幣值 = 0.2**
- **你輸（S0>0）**：`Δ = − S0 × 0.2`　　（實證 4/4 精準：69→−13.8、80→−16.0、71→−14.2、68→−13.6）
- **你贏（S0=0）**：`Δ = Σothers × 0.2 × (1 − rake)`，**rake = 5%**
  （實證：Σ40×0.2=8.0→Δ+7.6＝8.0×0.95；Σ71×0.2=14.2→Δ+13.49＝14.2×0.95）
- **贏家實收 = 彩金 × 0.95；莊家抽水 = 彩金 × 5%**（彩金 = 各輸家付出之和）。
- **每局恰好 1 位贏家**(回合制:棄到剩最後 1 人即自動贏,不存在「全桌皆棄/無贏家」)。「其他人全放棄」= 他們各付 drop 罰分進彩池、你撿尾,**同一條公式**(48204094 實證:對手 20+20 → 你 +7.6)。
- **宣告動作 = 你送 `cmd17`**(declare);有效→你 score 0 贏,無效→full count 80。

> 分數語意（30 局實證）：**0 = 贏家**；**20 = first drop**(發牌第一手就棄)；**40 = middle drop**(摸過牌才棄)；
> **80 = full count**(打到底爆分/無效宣告)；其餘 = 打到底的 deadwood 點數和。

## 每局 JSON 欄位
| 欄位 | 型別 | 說明 |
|---|---|---|
| `round_id` | str | 局號（尾段含 gameID 94） |
| `you` | str | 你的帳號 |
| `start_balance` / `end_balance` | float | 本局前 / 後餘額 |
| `balance_delta` | float | `end − start`（＝上面金流公式） |
| `seats[]` | list | 本桌玩家：`{seat, account, amount}`。你的 `amount`=餘額；他人 `amount`=報名費/注(實測 16) |
| `wild_joker` | card | ★本局百搭鬼牌★（切出的牌；該點數全部當鬼牌） |
| `open_top` | card | 開局棄牌堆頂 |
| `stock_start` | int | 開局閉牌堆（摸牌堆）張數 |
| `your_hand[]` | card[] | ★你的 13 張手牌★ |
| `your_melds_init[]` | card[][] | 你開局時的分組（通常未成組） |
| `actions[]` | list | 依序的摸/棄/撿事件：`{cmd,dir,type,seat?,card?,picked?,stock}`。`type`∈ draw_closed(摸閉堆)/discard(棄到開堆)/draw_open(撿開堆)/my_discard(你棄) |
| `action_count` | int | 動作數 |
| `settlement` | obj | `{results[], balance}`；**無結算=半局，丟棄** |
| `settlement.results[]` | list | 每家 `{seat, score, melds[][]}`。`score=0`→贏家 |
| `outcome` | str | ★本局你的結果★:`win` / `first_drop`(20) / `middle_drop`(40) / `full_count`(80) / `loss`(deadwood) / `partial`(擷取中斷,略過) |
| `your_points` | int? | 你本局分數:贏=0;drop=20/40;loss=deadwood;full_count=80;partial=null |
| `action_count`… | | （其餘見檔） |

### 牌的編碼（`card`）
`{suit, rank, joker, label}`
- `suit`：**0–3 = 四個真花色**（對實際 ♣♦♥♠ 的順序**待確認**，`label` 只是暫定符號，請以 int 為準）；**4 = 印牌鬼牌 PJ**（實測恆 joker）。
- `rank`：1–13（1=A, 11=J, 12=Q, 13=K）。
- `joker`：true = 此牌**當鬼牌用**（印牌鬼牌，或等於本局 `wild_joker` 點數的牌）。
- 2 副牌 → 手牌出現**重複牌**（如兩張 ♣4）屬正常。

## 算 RTP / 要觀察什麼
1. **發牌隨機性 / 牌分佈**：`your_hand` + `wild_joker` across 多局 → 是否均勻、是否偏坦。
2. **鬼牌出現率**：每局固定 1 個 wild 點數（4 張）＋印牌鬼牌 PJ；統計你手上 joker 數分佈。
3. **抽水 rake = 5%**（已釘），彩金 = Σ輸家分 ×0.2。長期莊家收益 ≈ 5% × 總彩金流。
4. **drop / score 行為**：score 的值域與頻率（0 / 20 / …／80），drop 罰分規則。

## 注意 / 待確認
- 花色 int↔♣♦♥♠ 對應順序；`score` 的 drop 碼（20 之類）；`actions` 裡 cmd13/14 的次要旗標 —— 皆**多抓幾百局**即可釘死。
- 伺服器權威 RNG，客戶端只收廣播，**無法預測**（同其他款）。
- 半局（`settlement` 為空）請略過，別計入統計。
