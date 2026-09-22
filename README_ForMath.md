# JILI 696 抓封包 / 重播封包 — 操作手冊(給數學／機率團隊,Windows)

照著做就能 **① 抓封包**、**② 重播封包**、**③ 改參數看演出**。
全部指令都在資料夾 `C:\lechengwork\dyson\jili` 底下用 **PowerShell** 執行。

> 每次開新的 PowerShell 視窗,先切到這個資料夾:
> ```
> cd C:\lechengwork\dyson\jili
> ```

---

## 0. 前置準備(只需做一次)

1. 裝 **Python 3.10+**,然後:
   ```
   pip install cryptography requests
   ```
2. **（只有「抓封包」需要 VPN;重播不用）** 裝官方 **WireGuard for Windows**,匯入 Surfshark 的**巴西** `.conf`。細節見 `HANDOVER_WINDOWS.md`。
3. 若 PowerShell 擋腳本(紅字「執行原則」),這台先跑一次:
   ```
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```

---

## 1. 抓封包

1. `cd C:\lechengwork\dyson\jili`
2. `.\webcapture.ps1 696`
3. 跳 **UAC** 按「是」;VPN 會自動切(台灣產 token → 巴西擷取)。
4. 自動開的 **Chrome**:點進遊戲 → 開 **autoplay** 轉到你要的局數。**★別開 DevTools★**。
5. 轉夠了,匯出:
   ```
   .\webcapture_finish.ps1 696
   ```
6. 收工:`.\stop.ps1`

### 抓到的東西放哪

- **★給機率團隊(你要交出去的)→ `games\696\math\`**
  每局一個 `.json`(欄位全是數字、無密文)+ `INTERFACE.md`(欄位表,算 RTP 必看)。
  擷取時就即時逐局寫入;`webcapture_finish.ps1` 會再完整重產一次並做驗證。
- **原料(別刪,重播/解碼要用,都在 `games\696\` 底下)**:
  - `webcap_exchanges.jsonl`(原始側錄,finish 用)
  - `webcap\exchanges_ordered.jsonl` + `webcap\spins_raw\`(**重播**用)
  - `%TEMP%\jili_grab.json`(解碼金鑰,finish 用)
- 這些都集中在 `games\696\`,不影響系統其他地方。

---

## 2. 重播封包

VPN 關掉(重播不用)。

- **播全部**(用抓到的原始封包):
  ```
  .\replay.ps1
  ```
- **只播某一局**:
  ```
  .\replay.ps1 24182-490900-00600696
  ```

跳 **UAC** 按「是」→ 這個視窗會變成 log,Chrome 會自動開進遊戲照封包演出。
收工:視窗按 **Ctrl+C**,再 `.\stop.ps1`(還原 hosts)。

### 重播讀哪邊的封包
- 預設讀 `games\696\webcap\spins_raw\`(每局盤面)+ `webcap\exchanges_ordered.jsonl`(init/餘額)。
- **不是**讀 `math\`——因為 `math\` 是攤平成數字的分析檔、沒有遊戲要的原始位元組。

---

## 3. ★改參數看演出(改 math\ 的數字重播)

想「改自己的結果來演」就用 `-Source math`:它會把 `math\` 的每局**編回**遊戲能演的封包再播。

1. 打開 `games\696\math\<局號>.json`,改裡面的數字
   (例如 `data.board.multiplier`、`line_wins`、`window`、`total_win`…),**保持原本欄位形狀、別刪欄位**。
2. 重播:
   ```
   .\replay.ps1 -Source math
   ```
   只播某一局:
   ```
   .\replay.ps1 24182-490900-00600696 -Source math
   ```
3. 遊戲就會演出你改過的那局。

> 原理:`math\` ↔ 原始封包是**無損雙向**轉換(`math_adapter.py --selftest` 驗過 byte 完全相同),所以你在 `math\` 改什麼,重播就忠實演什麼。
> 建議第一次先原封不動 `.\replay.ps1 -Source math` 跑一遍確認正常,再開始改數字。

---

## 疑難排解

| 症狀 | 解法 |
|---|---|
| server 視窗狂洗 `[404] …​.webp`、遊戲卡 JILI logo | **VPN 開巴西**後跑 `.\fetch_assets.ps1`(掃缺圖→真站抓/補佔位圖,一口氣清零 404) |
| server 報 `ModuleNotFoundError: No module named 'pwd'` | server 換整包後又出現的 Windows 相容問題 → 找工程/AI 把 `routex\server.py` 的 `import pwd` 包成 try/except(或請 server 同事直接改) |
| 遊戲跳 **MSG 304「網絡不穩定」** | token 過期,重跑 `.\webcapture.ps1 696` |
| 遊戲跳 **MSG 103「无法连接服务器」**(重播) | 用最新版 `.\replay.ps1`(已把遊戲 API host 一起導到本機) |
| Chrome **找不到網站 / NXDOMAIN** | 用最新版腳本(已改 443+hosts,不靠會失效的 Chrome 旗標) |
| PowerShell 紅字「執行原則」 | 先跑 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

> ⚠️ **server 每次重發整包**會把 `game_site_backup`(圖)、`.ps1`、以及 `import pwd` 的修正洗掉。換包後通常要:① 再跑一次 `.\fetch_assets.ps1` 補圖;② 若 server 報 `pwd` 錯,重補那行修正。

---

## 一句話總結

- **抓封包**:`.\webcapture.ps1 696` → 轉局 → `.\webcapture_finish.ps1 696`;交付檔在 `games\696\math\`。
- **重播**:`.\replay.ps1`(原封)或 `.\replay.ps1 -Source math`(改 math 數字看演出)。
- 收工都用 `.\stop.ps1`。
