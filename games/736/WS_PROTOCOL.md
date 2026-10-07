# JILI 736 = Jackpot Fishing 2（魚機 / fishing）— WebSocket 協定分析

> 2026-10-07 逆向。來源＝`games/736/traffic_raw.json`（bootstrap 真玩一場，2886 WS frames：1873 SEND / 1013 RECV）。
> 工具：`ws_fish736_view.py`（每發 math JSON + session 統計）。分析腳本見 scratchpad `an736/dump736/money736`。

## ★★ 頭條：明文 protobuf、零加密，但不是回合制
Jackpot Fishing 2 是**魚機（連續射擊）**，和 124(骰子) / 94(牌) 都不同——**沒有「局」**，
每一**發子彈**是一筆事件。傳輸與 124/94 **同一個 WS 框架**（明文 protobuf，零加密），
696 的 Ed25519/X25519/AES route-X **完全用不上**。

- 遊戲路徑：**`/fish23/`**（124=`/sudm/`、94=`/rummy/`）。game_url=`uat-wbgame.jlfafafa3.com/fish23/?ssoKey&gameID=736`。
- WS：**`wss://uat-fish.jlfafafa1.com/v23/ws/<40hex>?r=`**（同 124 的 uat-fish host，但 path `/v23/ws`，非 `/sudm/ws`）。
- 認證：先 HTTP `POST uat-wbwebapi.jlfafafa2.com/sso-login.api`，再開 WS。
- 帳號：**既定 tryplayer002usd 就能開**（不用 CNY 子代理）。
- 心跳：大量 2B frame（cmd50 ping/pong）。

## Envelope（每個 binary frame）
```
f1 = cmd  (varint)
f2 = body (bytes)   // 依 cmd 解
```
**例外：握手兩幀無 envelope**（WS 開啟後裸送/裸收）：
- SEND DeviceHello：`{f1="OS X", f2="zh-CN", f3={chrome,154,1920,1080,dpr}, f5="Macintosh"}`
- RECV Welcome（328B）：`f3.f2`=帳號、`f3.f4.f2`=起始餘額、`f3.f4.f5`=幣別`$`、`f8.f3`=packed double[28] **下注級距 0.1/0.2/0.3…**

## cmd 頻譜（本場 2886 frames）
| 方向 | cmd | 次數 | 意義 |
|---|---|---|---|
| SEND | 22 | 874 | **發射子彈**(FireReq) |
| SEND | 23 | 872 | **宣稱命中魚**(HitReq) |
| RECV | 25 | 784 | **開砲結算**(ShotResult)★核心★ |
| RECV | 24 | 86 | **作廢的一發**(ShotVoid) |
| RECV | 46 | 8 | 金幣/道具拾取(側收入) |
| RECV | 28 | 15 | 四層彩金池(Jackpot) |
| RECV | 30 | 2 | 大獎公告 |
| RECV | 82 | 1 | 魚種目錄(1521B) |
| RECV | 45 | 1 | 場景/魚群設定(5291B) |
| both | 50 | 90/90 | 心跳(2B) |
| … | 21/27/31/40/92/95/100/115/140/143/144/146 | 少量 | session/控制/ack |

## cmd22 — 發射子彈（SEND FireReq）
```
f1 = Bullet{ f1 = bullet_id(遞增 1..N), f3 = bet(coin 值 double) }
f2 = Aim{ f1 = x(float32), f2 = y(float32) }   // 瞄準向量
f3 = 空
```

## cmd23 — 宣稱命中魚（SEND HitReq）
```
f1 = Bullet{ f1 = bullet_id, f3 = bet }
f2 = Target{ f1 = fish_id(畫面實例,transient), f2 = 1 }
f3 = 1
```
SEND22/23 幾乎 1:1。client 權威「我打中哪隻」，server 決定是否捕獲 + 配當。

## cmd25 — 開砲結算（RECV ShotResult）★機率核心★
```
f2 = Meta{ f1 = bullet_id, f2 = power_flag, f3 = bet }
f5 = Catch{ f1 = fish_id, f2 = payout(double),   // ← 捕獲才有;無=miss
            f3/f4 = AoE/連鎖波及的魚清單(視覺,RTP 不需要) }
f6 = balance(結算後餘額)
f7 = 1.0
f8 = 伺服器 tick/seed(多發可共用)
```

## ★★ 金流模型（全域守恆 + bullet_id 鏈結驗過）
```
cost（每發成本） = bet × power
payout（捕獲配當）= bet × M          // M = 魚倍率,乾淨整數
餘額            = 前餘額 − cost + payout   // miss: payout=0
RTP            = Σpayout / Σcost
```
- **`bet`（f2.f3）不是成本本身**。成本 = bet × **power**（砲台倍率）。
- **power 由 `cmd25.f2.f2`（power_flag）決定**：實測 `f2.f2=1 或缺 → ×1`、`f2.f2=6 → ×5`。
  ★旗標值(6)≠倍數(5)，是砲台等級索引；更多等級待更長 capture。`ws_fish736_view.py`
  會**自動從 miss 的餘額差校正** flag→倍數，不寫死。★
- **M = payout / bet 是乾淨整數**：實測 2/7/10/15/20/25/30/66/70/80/88/90/110/180/222/270/430/690…
  （相對 bet 欄位、**非**相對 shot 成本）。大魚/Boss 可達數百倍。
- ★排序：**務必按 bullet_id 排序**才會鏈對；ts(到達時間)排序會因爆發射擊亂序而對不上。★

### 實證（bullet_id 鏈，bet=0.03 power=5 → cost=0.15）
| bullet | fish | payout | M | Δ餘額 | =−cost+payout |
|---|---|---|---|---|---|
| 454 | 567 | 5.4 | 180 | +5.25 | −0.15+5.4 ✓ |
| 455 | 567 | 8.1 | 270 | +7.95 | −0.15+8.1 ✓ |
| 399 | 651 | 20.7 | 690 | +20.55 | −0.15+20.7 ✓ |
| 456(miss) | — | 0 | — | −0.15 | −0.15 ✓ |

## cmd24 — 作廢的一發（RECV ShotVoid）
```
f1 = Bullet{ f1 = bullet_id, f3 = bet }
f2 = bet(未實際扣)
f3 = balance(不變)
```
client 宣稱命中，但 server 處理時該魚已被別發打死/離場 → **這發不扣款、不配當，金流淨 0**。
魚機常見的延遲去同步。**RTP 計算要排除**（784 cmd25 + 86 cmd24 ≈ 872 cmd23）。

## 副功能（非 RTP 核心，但也可能動餘額，衝量時要納入守恆）
- **cmd28** 四層彩金池 `{grand~40000, major~5000, minor~500, mini~50}`，隨時間累積跳動（部分下注進彩池＝隱性成本）。SEND cmd25(裸`0819`)/cmd27(裸`081b`) 請求。
- **cmd30** 大獎公告 `{account, mult(690/222), net}`。
- **cmd46** 金幣/道具拾取 `{pos, amount(+0.017/0.086)}`＝側收入（`summary.RTP_with_pickups` 已計）。
- cmd82 魚種目錄（type ids 16411001…16444001 共 16 種 + 賽程時間）、cmd45 場景設定、cmd92 餘額快照、cmd21 進遊戲、cmd115 語言、cmd40/140/143/144/146 狀態同步、cmd31 ack。

## provably-fair
伺服器權威 RNG（cmd25.f8 = tick/seed），結果客戶端不可預測（同其他款）。

## 待補（更長 capture）
1. power 等級全集（目前只見 ×1/×5）；校正器會自動吸收新等級。
2. 魚種 type_id（cmd82/45 目錄）→ 基礎倍率對照；目前 `fish` 是畫面實例 id、非魚種。
3. 含彩金中獎的完整 RTP（cmd28 投入 + 中彩事件）。
4. 大量樣本算真 RTP（魚機單發變異極大）。
