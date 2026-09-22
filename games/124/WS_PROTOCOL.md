# JILI 124 = 7up7down (7上7下, Extra Pay) — WebSocket 協定分析

> 2026-09-18 逆向。來源=`games/124/ws_session1.jsonl`（真實對局 139 WS frames：73 SEND / 66 RECV）。
> 工具：`ws_decode.py`（通用 protobuf 傾印）、`ws_rounds.py`（每局校正表 → `ws_rounds.txt`）。

## ★★ 頭條：明文 protobuf、零加密
7up7down 後端走 **WebSocket + 明文 protobuf**，**完全沒有加密**。frame 裡直接看得到
`tryplayer002usd` / `chrome` / `Macintosh` / 骰子賠率 double。
→ 與 696 的 Ed25519+X25519+AES-GCM route-X **是兩套完全不同的協定**；696 那套 harness 對 124 不適用，
但 124 反而**簡單非常多**——不用破任何 crypto，直接讀 protobuf。

- 傳輸：`wss://uat-fish.jlfafafa1.com/sudm/ws/<40hex>?r=0`（**uat-fish** host，不是 696 的 gs/be）。
- 認證：先 `POST uat-wbwebapi.jlfafafa2.com/sso-login.api → 200`（HTTP），再開 WS。
- 心跳：大量 2-byte SEND/RECV frame（ping/pong），非遊戲資料。

## Envelope（每個 binary frame）
```
f1 = cmd  (varint)   // 22 = 遊戲局(下注/開獎)；另見 23/100/105/111/115=session/config/控制
f2 = body (bytes)    // 依 cmd 解
```

## cmd 22 — 遊戲局
### SEND 下注（`BetReq`）
```
f1 = repeated Bet    // 可 1 注或多注(實測一次下 12 個點, 165B frame)
       Bet: f1=amount(double), f2=position(varint 0..12)
f2 = action(=1)      // 下注並開骰
f3 = 0
```
純開骰（8B，無 bets）：`{f2=1, f3=0}` — 沿用場上既有注連續開。

### RECV 開獎（`GameResp`）
```
f1 = Result
       f1 = total_win(double)     // 贏才有；輸/0 省略
       f2 = die1(varint 1..6)     // 骰子1
       f3 = die2(varint 1..6)     // 骰子2 → sum 決定 大/小/和
       f4 = won_positions(bytes)  // 中獎注點(編碼待確認)
       f5 = repeated double[13]   // 該局各注點賠率(packed)
f3 = balance(double)              // 開獎後餘額
f4 = round_id(varint)             // 局號，單調遞增(每局 +~26~30)
f5 = repeated Bet                 // 回聲這局所下的注
```

## 驗證（餘額差校正，見 ws_rounds.txt）
| 下注 | 骰子 | res.f1(win) | 餘額Δ | 判定 |
|---|---|---|---|---|
| 2.0 @ pos1 | 3,1 (和4) | 6.0 | +4.0 | 贏 6 − 注 2 = 淨 +4 ✓ |
| 2.0 @ pos2 | 1,2 (和3) | — | −2.0 | 輸 ✓ |
| 4.0 @ pos0 | 1,5 (和6) | — | −4.0 | 輸 ✓ |
- 餘額 98611.9 逐局遞減、round_id 單調遞增，皆自洽。骰子 f2/f3 全程落在 1–6 ✓。

## ★注點對照(已釘死:單注實驗 13/13 + 對稱賠率反證)
| pos | 注區 | 基礎賠率 | pos | 注區 | 基礎賠率 |
|---|---|---|---|---|---|
| 0 | 和(=7) | 4x | 7 | 6 | 5x |
| 1 | 小(<7) | 1x | 8 | 8 | 5x |
| 2 | 大(>7) | 1x | 9 | 9 | 6x |
| 3 | 2 | 26x | 10 | 10 | 8x |
| 4 | 3 | 12x | 11 | 11 | 12x |
| 5 | 4 | 8x | 12 | 12 | 26x |
| 6 | 5 | 6x |  |  |  |

- 規律:pos0/1/2=和/小/大;pos3..12=特定點數 2,3,4,5,6,8,9,10,11,12(跳過 7=和)。
- 基礎賠率 = `GameConfig(cmd23).base_odds[13]` = `[4,1,1,26,12,8,6,5,5,6,8,12,26]`，以 sum7 對稱。
- ★`Result.f5` 是 **Extra Pay 每局隨機額外倍率**(2/5/10x)，**不是**基礎賠率(與骰子無關)。

## provably-fair
遊戲內文：「回合结果由**服务器种子**和该回合**前3个投注**组合决定」→ 伺服器權威 RNG，
結果無法客戶端預測（同其他款）。

## 待補（下一步）
1. position 0..12 → 大/小/和/各數字 的完整對照（多玩單一注點各一局即可反推）。
2. `Result.won_positions(f4)` 的 byte 編碼。
3. cmd 22 GameConfig(767B) 的下注限額/賠率表欄位；session cmd(23/100/105/111/115)。
4. 若要「離線重播/mock」：因伺服器權威，只能重播固定歷史(同 696)；但因明文無加密，重播 server 遠比 696 好做。
