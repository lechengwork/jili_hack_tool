# JILI 696 純網頁擷取 — Windows 交接說明（給同事 + 他的 AI）

目標：**生 token → 開巴西 VPN → 進遊戲用 autoplay 轉 N 局 → 解出每局的可讀 JSON**。
免 Frida、免 netlog。macOS 上已整條實測通過（真伺服器、簽章全效）。

這份給「同事的 AI」：**Python 程式碼（`.py`）全部跨平台、不用改**；要改的只有 **3 個 `.sh` 編排腳本**（可改成 `.ps1`，或照本文「手動步驟」直接跑），外加**一個路徑修正**（見 §3 的 `GRAB`）。

---

## 1. 資料夾結構（解壓後就是這樣，**相對路徑不能動**）

`server.py` 用 `../` 定位靜態站與資料檔，所以整個結構要保持：

```
jili/
├─ webcapture.sh              # 編排①:VPN關→產token→split hosts→開server→VPN開→開Chrome  ← 要移植
├─ webcapture_finish.sh       # 編排②:把側錄檔批次解密+語意化                          ← 要移植
├─ webcap_pretty.py           # 語意化(貼標籤)                                          ← 跨平台,不用改
├─ stop.sh                    # 停 server/Chrome                                        ← 要移植(可選)
├─ jili_login.py              # 產 token(打 LoginGame)                                  ← 跨平台,不用改
├─ config.json                # 內含 LoginGame 的 JWT(產 token 用)                      ← 必要,含密鑰
├─ routex/
│  ├─ server.py               # 主程式(capture 模式)                                    ← 跨平台;僅 §3 路徑要設環境變數
│  ├─ fg5.py                  # crypto/protobuf 核心                                     ← 跨平台
│  ├─ capture_shim.js         # 注入頁面的側錄 shim                                      ← 跨平台
│  ├─ decrypt_capture.py      # 離線解密                                                 ← 跨平台
│  ├─ mockkeys.json           # server 啟動必需(即使 capture 模式)                       ← 必要
│  ├─ wasm_pub_patches.json   # 提供 shim 的記憶體錨 ORIG0                               ← 必要
│  ├─ server.crt / server.key # 自簽憑證(缺了會自動產,可不帶)                           ← 可選
├─ game_site_backup/uat-wbgame.jlfafafa3.com/   # 遊戲靜態站,本機供應=shim 載體(~51MB)   ← ★必要;不是回放,capture 靠它注入 shim
└─ games/696/
   └─ GAME_FORMAT_SPEC.md     # 欄位語意定義(pretty.jsonl 就是照它做的)                  ← 參考
   (執行時這裡會自動產出 webcap_exchanges.jsonl / webcap_grv.jsonl / webcap/ )
```

> 不需要的檔（別帶）：`*.har`、`deobf*`、`*.zip`、heap dump、Frida 相關（`patchwasm.py`/`grab*.py`）、mock 專用的 `run.sh`/`web.sh`。capture 用不到。

---

## 2. Python 環境

裝 Python 3.10+，然後：

```
pip install cryptography requests
```

> ★只想驗證轉換、不抓樣本的話,連這步都不用★：`math_adapter.py` 是零相依,
> 系統內建的 `python` 直接跑 `python math_adapter.py --selftest` 就會印
> `round-trip:834 局 byte 完全相同 / 0 局不符`。

Mac 上是用 venv（`./.venv/bin/python3`）；Windows 直接用 `python` 即可（把腳本裡的 `./.venv/bin/python3` / `../.venv/bin/python` 換成 `python`）。

---

## 3. ★唯一的程式路徑修正（重要）

`server.py` 撈到的 AES key 預設寫到 **`/tmp/jili_grab.json`**（Unix 路徑，Windows 沒有 `/tmp`）。
用環境變數 `GRAB` 覆寫成 Windows 路徑，**server 和 finish 兩邊要用同一個路徑**。例如：

```
set GRAB=%TEMP%\jili_grab.json
```

其他輸出檔（`webcap_exchanges.jsonl`、`webcap_grv.jsonl`、`webcap/`）都在 `games/696/` 下、用的是相對路徑，跨平台沒問題。

---

## 4. 編排腳本在做什麼（給 AI 移植的邏輯；可寫成 .ps1 或手動跑）

### webcapture.sh（開始擷取）
1. **VPN 關** → 確認出口是台灣（TW）。*(產 token 的站 gamejar.cc 會擋巴西 IP)*
2. `python jili_login.py 696 --json` → 拿到**真 token 的 game_url**（裡面有 `ssoKey`）。
3. **改 hosts（split）**：只把 **document host** 指到本機，api host 留給真站：
   - Windows hosts 檔：`C:\Windows\System32\drivers\etc\hosts`（**要系統管理員**才能改）
   - 只加一行：`127.0.0.1 uat-wbgame.jlfafafa3.com`
   - **不要**加 `uat-wbwebapi` / `uat-wbslot-fd` / `uat-wbslot-platform`（這些要走真站）
   - 改完刷新 DNS：`ipconfig /flushdns`
4. **開 server（capture 模式，要系統管理員 = 綁 443）**：
   ```
   set GRAB=%TEMP%\jili_grab.json
   set PORT=443 & set TLS=1 & set VERBOSE=1 & set INJECT_BUNDLE=1 & set CAPTURE=1 & set LIVE_DECODE=1
   python routex\server.py
   ```
   看到 `listen https://localhost:443` 就緒。
5. **VPN 開 → 巴西（BR）**。*(真 /fg5/req 只收巴西出口)*
6. **開普通 Chrome**（拋棄式 profile、放行自簽憑證、關 QUIC），連**步驟 2 的 game_url**：
   ```
   "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
     --user-data-dir=%TEMP%\jili-webcap ^
     --ignore-certificate-errors --disable-quic ^
     --no-first-run --no-default-browser-check ^
     "<步驟2 的 game_url>"
   ```

### 進遊戲後（人工）
- 點進遊戲真實畫面，用**遊戲內建 autoplay** 轉到要的局數（幾千幾萬）。
- 盯 **server 視窗**：每局先印 `★ [capture] seq=… resp=…B`（首次帶 `+KEY` = 記憶體撈到 key，或看到 `grv#…` 備援 = 有 key、穩了）。
- **★即時解碼(新)**：拿到 key 之後，每 spin 一局，server 視窗會【當場】印出這一局解出來的可讀格式：
  ```
  ┌── [decode] seq=18  type=0 (spin)  ret=0  sig_ok=True ──────
      { "type":0, "kind":"spin", "round_id":"…", "balance":…, "total_win":…,
        "base_bet":…, "ante":…, "multiplier":…, "win_lines":…, "board":[…],
        "reels":[…], "paylines":[…] }
  └────────────────────────────────────────────
  ```
  → **spin 一次就能在 cmd 直接看到這一局的格式，不必等收工**（欄位同 `pretty.jsonl`）。
  預設開；要關掉純看擷取數就 `set LIVE_DECODE=0`。key 還沒到的前幾筆會先存原始封包、稍後可批次補解。
- **★別開 DevTools**（會觸發遊戲的 Jscrambler 反除錯、弄壞遊戲、跟一般網路錯難分）。

### webcapture_finish.sh（解碼；批次匯出，現在為選用）
> 即時解碼已能在 server 視窗逐局看到結果；這步只在你想把整個 session 一次匯成檔案（`pretty.jsonl` 等）時才需要。
1. 把 `games/696/webcap_exchanges.jsonl`（每行一筆）轉成 JSON 陣列 `games/696/webcap/fg5_exchanges.json`。
2. 解密（key 來源：優先 `%GRAB%`，沒有就退 `games/696/webcap_grv.jsonl`）：
   ```
   cd routex
   python decrypt_capture.py --exchanges ..\games\696\webcap\fg5_exchanges.json --grab %TEMP%\jili_grab.json --out ..\games\696\webcap\responses.jsonl
   cd ..
   ```
   *(若 `%GRAB%` 沒 key 檔，改用 `--grv ..\games\696\webcap_grv.jsonl` 取代 `--grab ...`)*
3. 語意化：`python webcap_pretty.py 696`
4. 匯出原封不動封包：`python webcap_backend_raw.py 696 --grab %TEMP%\jili_grab.json`
5. **★轉成機率介面★**：
   ```
   python webcap_math_view.py 696 --exch-raw games\696\webcap\exchanges_ordered.jsonl --out %MATH_OUT%
   python math_adapter.py --selftest
   ```

### 產出

**★★★ 機率要的就這一個目錄 ★★★**

- **`games/696/math/<局號>.json`** ← 輸入 `spinReq` / 輸出 `data`，照 `games/696/math_696.proto` 填。
  擷取當下就會即時落檔（server 視窗也即時印同一份），不必等收工。
- `games/696/math/all.jsonl` ← 同內容一行一局
- `games/696/math/INTERFACE.md` ← 欄位表 + 每條的實證依據 + 實扣倍率（算 RTP 必看）

**以下是工程層產物，機率不用看：**

- `games/696/webcap/backend_raw/spins/*.json` ← 後端原封不動封包（三層 hex）
- `games/696/webcap/pretty.jsonl` ← 舊的熟視圖（改名/丟欄位/自算，只當參考）
- `games/696/webcap/exchanges_ordered.jsonl` ← 原始 decoded（除錯用）
- 線路層欄位定義見 `games/696/fg5_696.proto`。

### 盯進度

```
python math_progress.sh 的等效：直接跑 bash（Git Bash / WSL）：
  ./math_progress.sh --all
```

它會印:側錄是否還活著、總局數、倍率規則有沒有反例、賠付表缺什麼、各注額樣本夠不夠。
**第一行是 `● 活著` 才表示還在錄**；變成 `○ 停了` 就是現在轉的都沒被錄到。

---

## 5. 平台差異速查（Mac → Windows）

| 項目 | Mac（現況） | Windows（要換） |
|---|---|---|
| Python | `./.venv/bin/python3` | `python`（先 `pip install cryptography requests`） |
| 提權（綁 443 + 改 hosts） | `sudo` | 用「系統管理員」開終端機 |
| hosts 檔 | `/etc/hosts` | `C:\Windows\System32\drivers\etc\hosts` |
| 刷新 DNS | `dscacheutil -flushcache; killall -HUP mDNSResponder` | `ipconfig /flushdns` |
| key 檔路徑 | `/tmp/jili_grab.json` | `set GRAB=%TEMP%\jili_grab.json`（server+finish 同值） |
| 環境變數 | `env A=1 B=2 cmd` | `set A=1 & set B=2 & cmd` |
| 機率輸出目錄 | `MATH_OUT=games/696/math` | `set MATH_OUT=games\696\math`（server 與 finish 同值） |
| Chrome 路徑 | `/Applications/Google Chrome.app/...` | `C:\Program Files\Google\Chrome\Application\chrome.exe` |
| VPN 切換 | `scutil --nc start/stop <UUID>`（Surfshark WG） | 用 Surfshark app 手動切，或該 VPN 的 CLI |

---

## 6. 三個一定要記住的成敗關鍵

1. **token 會過期**（十幾分鐘）：進遊戲後別拖，儘快開 autoplay。遊戲若跳 **MSG 304「網絡不穩定」**，最常見就是 token 逾時 → 重新產 token 再開一次。
2. **`MATH_OUT` 要一路帶著**：server 起動時帶了什麼，收工（finish）就要帶一樣的，
   不然「擷取當下即時落的檔」和「收工重產的檔」會散在兩個目錄。
3. **hosts 一定要 split**：只有 `uat-wbgame` 指本機，其餘三個 host 留給真站（走 VPN）。若不小心把四個都指本機，就會連到「假 server」而不是真站（擷取到的不是真結果）。server 若偵測到 `/fg5/req` 打到本機會印警告 502。

---

## 7. 遊戲卡在 JILI splash + 一直 `[404] /fg5/assets/.../*.webp`（換平台貼圖）

現象：server 視窗狂洗 `[404] /fg5/assets/main/native/…​.webp (missing asset?)`，遊戲停在 JILI logo/進度條。

原因：`game_site_backup` 是在 Mac 抓的，壓縮貼圖只存了 Apple GPU 用的 `.astc`；**Windows 一般 GPU 的 Chrome 會改要同一張圖的 `.webp`**，本機 mirror 沒有 → 404 → loader 卡住。

修法：跑補檔工具，把缺的 `.webp` 從真站抓進 mirror（**需 VPN=BR**）：
```
python fetch_missing_assets.py
```
- 用 DoH 直連真站，**hosts 就算已 split（uat-wbgame→本機）也照抓**，不用動 hosts。
- 整批補完（約 38 個）遊戲就能載過 splash。
- 若往下玩又冒出零星 `.webp` 404：把 server 視窗那幾條路徑直接當參數貼上精準補：
  ```
  python fetch_missing_assets.py /fg5/assets/game/native/xx/yyyy.webp  [更多…]
  ```
- 只想先看要補什麼：`python fetch_missing_assets.py --list`

（另有 server 端 `ASSET_FALLBACK=1` 的即時補洞，但本站資產只在 doc host、CDN 不供應，故預設關、用不到；以上工具才是正解。）

---
