# JILI 696 擷取資料格式說明（給數學／機率團隊）

> 這份講「擷取後你會拿到什麼、怎麼讀、哪個欄位是什麼」。
> 擷取流程本身見 `RUNBOOK.md`；欄位權威定義見 `games/696/fg5_696.proto`。

---

## 1. 你會拿到的檔

這些檔在兩個時機產生，格式完全一樣：
- **即時**：每轉一局，server 視窗就印出明文、並當場寫一個 `backend_raw/spins/<局號>.json`（不用等收工）。
- **收工**：`./webcapture_finish.sh 696` 會把整場（含 init/config/balance）一次重生到 `games/696/webcap/backend_raw/`。

位置 `games/696/webcap/backend_raw/`：

| 檔案 | 用途 |
|---|---|
| `backend_raw/spins/<局號>.json` | ★**每局一檔，你主要看這個**（後端原封不動封包＋各層解讀） |
| `backend_raw/backend_raw.jsonl` | 整場全回應各一行（含 init/config/balance…，同格式） |
| `backend_raw/README.txt` | 簡短說明 |

⚠ **不要用**這兩個做數學（它們是事後「熟視圖」，會**改名／丟欄位／自算**）：
- `games/696/webcap/spins/*.json`、`pretty.jsonl` —— 例如 `paid_bet` 是我們算的（封包沒有）、`board` 其實是 proto 的 `window`、`total_win` 在沒中獎時被我們補 0（封包其實省略）。**只當可讀參考。**

---

## 2. 一局的資料分層（同一份 bytes 的不同視圖）

一個 spin 回應，從線上加密原文一路解到套名字，**都是同一段 bytes**：

```
response_wire_hex   線上實際 bytes：sig(64)‖nonce(12)‖AES-256-GCM 密文
      │  AES-256-GCM 解密（唯一不可免的處理）
plaintext_hex       完整 Envelope 明文（後端原封不動那一包）
      │  取 field 5（Envelope.data）
payload_hex   ★★★  = SpinResult 的原始 bytes  ＝ 也是「重播單位」
      │  解 protobuf（純結構，零改名）
payload_decoded     [{f:1,k:msg,...}, {f:6,k:f64,v:...}, ...]  只有欄位「編號」＋wire
      │  對 fg5_696.proto 套名字
payload_named       {board:{reels:[...],...}, balance:..., round_id:..., bet:{...}}
```

**每個檔還附**：
- `round_id`（單號，5-6-8 格式）、`type`、`ret`、`server_time`、`sig_ok`（Ed25519 簽章是否有效）
- `envelope_fields`：完整明文的欄位（f1=server 時間戳、f5=payload）

> 驗證過：`payload_hex == envelope_fields["5"]`；只拿 `payload_hex` 重解 100% 還原出 `payload_named`。
> ⇒ 這些層不是各自獨立的資料，是**同一段 payload 的不同解讀**。

---

## 3. 怎麼用（重要）

### (A) 要精準做數學 → 用 `payload_hex` ＋ proto 自己解
protobuf 線上**只帶欄位編號、不帶名字**；名字全來自 `fg5_696.proto`（我們逆向的）。最穩的方式：
```python
# 由 fg5_696.proto 產生類別後：
from fg5_696_pb2 import SpinResult
sr = SpinResult()
sr.ParseFromString(bytes.fromhex(rec["payload_hex"]))
print(sr.board.reels, sr.balance, sr.round_id, sr.bet.base_bet)
```
（`protoc --python_out=. games/696/fg5_696.proto` 產出 `fg5_696_pb2.py`）

### (B) 要肉眼快速看 → 用 `payload_named`
已套好名字的巢狀 JSON。但記住：
- 這是**我們逆向的解讀**，proto 有幾個欄位標「待確認」（見下表 ★）。
- **未知／沒對到的欄位保留 `f<編號>`**，不會被藏起來——看到 `f3`/`f5` 這種就是 proto 還沒命名的。
- **真正的 ground truth 永遠是 `payload_hex`。**

### (C) 重播驗證單位 = `payload_hex`（f5 = SpinResult）
你數學引擎「翻譯後」重新編碼出的 SpinResult bytes，就是丟回放的東西——
mock server 的 `make_response(data=<這段>)` 會自己補回外層 Envelope＋重新加密。

---

## 4. SpinResult 欄位速查（type 0）

| 名稱 | proto f# | 意義 | 備註 |
|---|---|---|---|
| `board` | 1 | 局面明細（BoardDetail） | 見下 |
| `reserved_f2` | 2 | 恆空 | |
| `total_win` | 3 | 總中獎金額 | ★**win=0 時封包省略**（= board.total_win） |
| `balance` | 6 | spin 後餘額 | |
| `round_id` | 20 | 單號（uint64） | 末 3 碼=696 |
| `bet` | 23 | 下注資訊（BetInfo） | |

**BoardDetail（board）**：

| 名稱 | f# | 意義 | 備註 |
|---|---|---|---|
| `reels` | 1 | 各軸符號序列（每軸 3 個符號 id） | 機率/RTP 原始輸入 |
| `window` | 2 | 可見盤面符號窗 | |
| `unknown_f3` | 3 | varint，eg 25/3 | ★待確認（疑符號總數/盤面尺寸） |
| `unknown_f5` | 5 | varint，eg 1/2 | ★待確認（疑 reel set/狀態） |
| `line_wins` | 6 | 中獎線（LineWin[]） | 沒中整段省略 |
| `win_line_cnt` | 7 | 中獎線數 | 0 時省略 |
| `nudge_pos` | 8 | EX NUDGE 後各軸位置 | 5 bytes |
| `multiplier` | 12 | ★倍率（nudge 後最終總倍率） | 單線最終分 = base × 此值 |
| `total_win` | 13 | 總中獎 | 沒中省略 |
| `rtp_const` | 15 | 恆 0.97 | ★語意待確認 |
| `ante_level` | 18 | 額外下注級別（1.5x=1,8x=2） | 沒開省略 |
| `post_nudge` | 19 | nudge 後盤面/符號狀態 | |

**LineWin（line_wins[]）**：`symbol_id`(1,疑) `match_count`(2,疑) `payline_index`(3,線號) `win_cash`(4,該線最終中獎，已含 multiplier)
**BetInfo（bet）**：`base_bet`(1，★額外下注時這裡仍是 base，不是實付額) `reserved_f25`(25,恆空) `ante`(26)
**Ante（bet.ante）**：省略=沒開；`{}`（空）=1.5x；`{level:1}`=8x

> 符號 id ↔ 賠付，以 **JILI 官方 696 數學表**為準；win 數學細節（f12 倍率怎麼套、f7 vs line_wins 筆數）proto 標「待確認」，本工具只忠實抽欄位。

---

## 5. 檢查遊戲能不能抓（`watch_games.sh`）

LoginGame 有時會對某款遊戲回「成功但拿不到 game_url」（= 該遊戲在後台被下架/維護）。想看 696 現在能不能抓：

```bash
./watch_games.sh --once      # 看一眼現況（各帳號×各遊戲）
./watch_games.sh             # 開著持續盯（每 180s 一次；696 一恢復會響鈴提示）
INTERVAL=120 ./watch_games.sh
```
狀態：`✓ 上架`(拿到 url) ／ `✗ 下架`(success+null) ／ `! 500 抽風`(暫時) ／ `? 帳號不存在`。
要改盯哪些遊戲/帳號：編 `watch_games.sh` 頂部的 `WATCH=(...)`（帳號候選在 `config.json` 的 `login_accounts`）。

> **`✗ 下架/停用(success+null)` 就是「取 token 那段卡住」的原因**——不是你的錯，等它自己回來即可（別換帳號、別改 payload，換了也一樣）。

---

## 6. 擷取注意事項（給實際跑的人）

- 全程用 **VPN 到巴西（BR）** 跑遊戲；產 token 那步要 **VPN 關（TW）**（`webcapture.sh` 會自動切）。
- game_url 的 **ssoKey 十幾分鐘就過期**，拿到就儘快進遊戲、開 autoplay。
- ★**別開 DevTools**★（會觸發 Jscrambler 防護）。
- server 視窗的「即時逐局」現在直接印**明文**（`payload_hex` + `payload_named`），且**每轉一局就即時寫** `backend_raw/spins/<局號>.json`——機率邊轉邊看即可。
- 收工再跑一次 `./webcapture_finish.sh 696`：把整場（含 init/config/balance…）完整重生一份，並產出 `backend_raw.jsonl`、`exchanges_ordered.jsonl` 等。
