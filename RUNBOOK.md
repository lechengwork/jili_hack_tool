# JILI 696 RUNBOOK — 解壓 → 跑(擷取) → 跑完(匯出) → 播(重播)

> 平台：Mac（腳本用 sudo / /etc/hosts / osascript）。Windows 收方看 `REPLAY_README.md` 的等效命令。
> 帳號：擷取用 `config.json` 裡的 `player_id`（本包 = 你現在這個）。

---

## 0. 解壓 + 一次性設定
```
cd <解壓路徑>/jili
python3 -m venv .venv
.venv/bin/pip install cryptography requests
```

## 1. 跑（擷取真站 spin）
```
./webcapture.sh 696
```
- 自動：VPN 關→TW 產 token → split hosts（只 doc host 指本機、api 走真站）→ 開 server（443，**在跳出的新視窗輸一次 Mac 密碼**）→ VPN 開→BR → 開 Chrome 進遊戲。
- 進遊戲後用遊戲的 **【自動轉 / autoplay】** 轉到你要的局數。**★別開 DevTools★**（會觸發 Jscrambler）。
- 盯 **server 視窗**：每轉一局就即時印出該局的**機率介面**（輸入 `spinReq` / 輸出 `data`，沒有密文欄位），並即時寫入：
  - `games/696/math/<局號>.json`（★★★**給機率的就是這個**，`math_696.proto` 形狀）
  - `games/696/webcap/backend_raw/spins/<局號>.json`（工程用明文：payload_hex/payload_named…）
  - `games/696/webcap/spins_raw/<局號>.json`（含 raw，回放用）；`spins/`（熟視圖）也會寫，僅供參考
  - 要主控台改印工程用明文：`LIVE_RAW=1`。
- VPN profile 不是預設的 → `VPN_UUID=<你的UUID> ./webcapture.sh 696`。
- 註：`/fg5/req` 是整個協定通道，log 會有很多筆（handshake / 餘額輪詢 / keepalive…），**只有 type=0 才是 spin**；每局檔數 = 你實際轉的局數。

## 2. 跑完（匯出重播來源）
```
./webcapture_finish.sh 696
```
→ 產生 `games/696/webcap/exchanges_ordered.jsonl`（重播來源）＋補齊 `spins/`、`spins_raw/`、`pretty.jsonl`、`backend_raw/`（工程用原封不動封包），
並轉出 **`games/696/math/`（★★★給機率的那一包）**，最後自動跑一次 byte 級 round-trip 自我驗證。
（本版 server 在 sudo 下會自動把擷取檔擁有者還給你，**不用手動 chown**。）

## 3. 播（本地重播，免 sudo／免改 hosts）

> ★本包已附回放資料★：`games/696/webcap/spins_raw/`（829 局）＋ `exchanges_ordered.jsonl`。
> **不用先跑擷取就能直接播。**
```
./stop.sh                                                     # 先停擷取用的 server(443)
REPLAY=games/696/webcap/exchanges_ordered.jsonl ./web_own.sh <你的base域名>
# 例：REPLAY=games/696/webcap/exchanges_ordered.jsonl ./web_own.sh mydomain.com
```
- `web_own.sh`：鑄一個撞中白名單的自有子網域（過 DomainLock，零改 bundle）→ 起 mock（8443、INJECT_BUNDLE）→ 開拋棄式 Chrome（`--host-resolver-rules` 全映本機）。VPN 開關都無所謂（全本機）。
- **mock 視窗要看到**（缺任一代表沒對）：
  - `[shim] shim loaded (…B) — BUNDLE-prepend into "polyfills.bundle"`
  - `[replay] N spin board(s)` / `[initseq] M ordered init responses (types: [1, …])`
  - `[fg5] … seq=2 …`（**不卡在 seq=1 狂重送**）→ 進轉盤、可 spin。
- **★別開 DevTools★**。收工：`./stop.sh`。
- 每局回放（用 raw 檔）：再加 `REPLAY_SPINS=games/696/webcap/spins_raw`（指含 raw 的那個目錄；REPLAY 仍要給，供 init）。

---

> ★資料格式怎麼讀、每個欄位是什麼:見 `BACKEND_RAW_README.md`。
> ★想看 696 現在能不能抓(取 token 是否又卡):`./watch_games.sh --once`。

## 產物一覽（機率團隊）

**機率只要看這三個,其餘都是工程層的東西:**

| 路徑 | 內容 |
|---|---|
| `games/696/math_696.proto` | ★★★**機率要填的 proto**。全 int / double / enum,**沒有 bytes**、沒有 reserved、沒有 envelope |
| `games/696/math/<局號>.json` | ★★★**輸入 `spinReq` → 輸出 `data`**。形狀=舊 JILI 機台那個 envelope,只把 `data` 換成 `data` |
| `games/696/math/INTERFACE.md` | ★★★欄位表＋每格的實測依據＋**實扣倍率(1× / 1.5× / 8×,算 RTP 必看)**＋還缺哪些樣本 |

流程:`前端 spin → 解密 → 轉成機率格式餵機率 → 機率吐回 → 轉回線路格式 → 加密 → 回前端`。
兩個方向都在 `math_adapter.py`,**58 局真實封包 round-trip byte 完全相同**(`python math_adapter.py --selftest`)。
★這層只存在於這包擷取工具,正式跑的遊戲不做這層轉換。★

**以下是工程層產物,機率不用看:**

| 路徑 | 內容 |
|---|---|
| `games/696/webcap/backend_raw/spins/<局號>.json` | **後端原封不動封包**（未改名／未丟欄位／未自算）。三層 hex：`response_wire_hex`(線上加密)、`plaintext_hex`(完整 Envelope)、`payload_hex`(=SpinResult=重播單位)＋`payload_decoded`(忠實 f# 傾印,無名字)＋`payload_named`(★套 fg5_696.proto 名字的可讀解讀;逆向來的、部分欄位待確認、未知欄位保留 f<N>) |
| `games/696/webcap/backend_raw/backend_raw.jsonl` | 全回應各一筆，同上三層 hex |
| `games/696/webcap/spins/<局號>.json` | ⚠**熟視圖**：webcap_pretty 把 window→board、reels 改名，丟掉 nudge_pos/rtp_const/post_nudge/時間戳，且**自算** paid_bet=底注×ante、win=0 補 total_win=0（封包其實省略）。**只當可讀參考，RTP/數學請用上面 backend_raw** |
| `games/696/webcap/spins_raw/<局號>.json` | `{round_id,idx,type,ret,raw}`（raw=SpinResult，供 REPLAY_SPINS 回放） |
| `games/696/webcap/exchanges_ordered.jsonl` | 整場（含 init + spins），重播來源；已含 `pt_hex`(完整明文)+`time` |
| `games/696/webcap/pretty.jsonl` | 全部一行一筆的熟視圖彙整（同 spins/ 注意事項） |
| `games/696/fg5_696.proto` | spin 完整結構 schema（proto3）；`Envelope.f5`=`SpinResult` |

> **給機率一句話**：你只要看 `games/696/math/`，照 `games/696/math_696.proto` 填。密文怎麼解、protobuf 怎麼包、envelope 怎麼串，都是我們遊戲層的事，不會出現在你那份檔案裡。
> ✅ `games/696/math/<局號>.json` **每轉一局就即時產生**，server 視窗也即時印同一份——機率邊轉邊看即可，不必等收工。收工再跑 `./webcapture_finish.sh 696` 會把整場重生一份並跑 byte 級 round-trip 驗證。
> ⚠ 696 **只有額外下注（extra bet），沒有免費遊戲**。
> 收工再跑 `./webcapture_finish.sh 696` 會把整場（含 init/config/balance）完整重生一份，並產出 `backend_raw.jsonl`、`exchanges_ordered.jsonl` 等。

## 觀念（重要）
- **「每局 log + json」是「跑(擷取)」階段產生的**（解真站傳回的新 spin）；「播(重播)」是把那些盤面服務回遊戲、不再重印/重存。要研究就看 `spins/`，要重現就 `web_own.sh`。

## 常見卡點
- `[warn] crypto.patched.wasm missing` → **可無視**（INJECT_BUNDLE 是編譯前改 pub，不走預 patch wasm）。
- mock log 出現 `.wasm`(crypto) **404** → 回報，需補一顆對應此組 mockkeys 的 patched wasm。
- 卡在 `seq=1` 狂重送 / MSG 999.2 → pub-patch 沒生效：確認 `routex/wasm_patch_shim.js` 在、且起 server 有 `INJECT_BUNDLE=1`。
- `PermissionError … webcap/…`（舊資料）→ `sudo chown -R "$USER" games/696` 一次即可（本版起 server 已自動 chown，新擷取不會再遇到）。
