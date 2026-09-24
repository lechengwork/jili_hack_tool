# JILI 124（7up7down / 七上七下・Extra Pay）抓封包 — 操作手冊（給數學／機率團隊，Windows）

照著做就能 **自己抓 124 的封包**，重點看 **Extra 會出現哪些倍率**。
全部指令都在資料夾 `C:\lechengwork\dyson\jili` 底下用 **PowerShell** 執行。

> 每次開新的 PowerShell 視窗，先切到這個資料夾：
> ```
> cd C:\lechengwork\dyson\jili
> ```

> **指令跟 696 一模一樣，只是換遊戲號**：抓 = `.\webcapture.ps1 124`、匯出 = `.\webcapture_finish.ps1 124`。
> （696 是 `.\webcapture.ps1 696`；號碼決定走哪套，腳本自動分派，你不用記兩個腳本名。）
>
> 幕後：124 的後端是【明文 WebSocket、沒有加密】，所以不用金鑰、不用解密、不用等記憶體
> —— 抓到就直接看得到骰子、賠率、extra 倍率。跟 696 的 route-X 是兩套協定，但**你不用管**。

---

## 0. 前置準備（只需做一次）

1. 裝 **Python 3.10+**，然後：
   ```
   pip install requests
   ```
   （124 不需要 `cryptography`，因為沒有加密。）
2. **抓封包需要 VPN**：裝官方 **WireGuard for Windows**，匯入 Surfshark 的**巴西** `.conf`。細節見 `HANDOVER_WINDOWS.md`。
3. 若 PowerShell 擋腳本（紅字「執行原則」），這台先跑一次：
   ```
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```

---

## 1. 抓封包

1. `cd C:\lechengwork\dyson\jili`
2. `.\webcapture.ps1 124`   （跟抓 696 同一個指令，只是號碼換 124）
3. 跳 **UAC** 按「是」；VPN 會自動切（台灣產 token → 巴西擷取）。
4. 自動開的 **Chrome** 會進 **124 七上七下（骰子）** 遊戲——一看畫面是骰子就知道抓對了（696 是 slot 轉輪）。
   **下注 / 開骰**，或開 **autoplay** 連續轉到你要的局數。**★別開 DevTools★**。
5. 盯著另一個 **server 視窗**：每局會印
   ```
   [ws] SEND   NNB
   [ws] RECV   NNB   (total=… send=… recv=…)
   ```
   看到 `[ws]` 逐筆進來 = 有抓到。**沒看到就是 WS 沒連上**（見下面疑難排解）。
6. 轉夠了，匯出：
   ```
   .\webcapture_finish.ps1 124
   ```
7. 收工：`.\stop.ps1`

### 抓到的東西放哪（★你要交出去 / 要看的都在 `games\124\math\`）

- **`EXTRA_SUMMARY.json`** ← ★**先看這個**：extra 的**值域**（實測出現過哪些倍率）、
  **每一格各個倍率各出現幾次**、以及**每格的 E[extra]**（平均額外倍率）。
- **`<round_id>.json`** ← 每一局一個檔：骰子、每格（畫面順序）的
  含本金賠率 `base_odds`、這局的 `extra`、`final_odds`、你的下注/中獎/賠付。
- **`all.jsonl`** ← 每局一行，方便你一次讀進來跑統計。
- **`INTERFACE.md`** ← 欄位表（算 RTP 必看）。**完整規格與注意事項**（例如 position 對照的坑）在
  `games\124\EXTRA_MULT.md`。

> 原料（別刪）：`games\124\webcap_ws.jsonl` 是側錄的原始 WS 封包，`.\webcapture_finish.ps1 124` 讀它。
> 每次 `.\webcapture.ps1 124` 會**清空**它重抓；要累積多輪就先把它複製走。

---

## 2. Extra 是什麼（一句話）

`extra` = 每局**隨機**灑在 13 個注區的**額外倍率**，乘在該格的顯示賠率上，
**跟骰子結果、跟你下不下注都無關**，開獎才回。沒蓋到的格子 `extra = 1`。

- 目前實測值域 = **{1, 2, 5, 10}**（1 = 沒蓋）。截圖佐證至少還有 **3**，只是樣本沒抽到。
  **你抓越多局，值域和頻率越完整** —— 這正是要你自己抓的原因。
- 賠付公式（工具每局都自動驗，全對才輸出）：
  `win = Σ(中獎格) 下注 ×（顯示賠率 × extra ＋ 1）`。
- 你真正要設計的是**每格的 E[extra]**（各格命中率/賠率不同，extra 機率不能一視同仁）。
  `EXTRA_SUMMARY.json` 已用你抓到的局數把每格的 E[extra] 算好，直接拿來對目標 RTP。

---

## 疑難排解

| 症狀 | 解法 |
|---|---|
| server 視窗**完全沒有 `[ws]`** | ①遊戲要真的**進到牌桌並下注/開骰**才有 WS 遊戲封包。②確認 VPN 在**巴西**。③server 視窗看有沒有 `[shim] ws-capture-shim installed`（有=shim 注入成功）。把 server 視窗整段貼給我。 |
| server 視窗有 `[shim]` 但沒 `[ws]` | WS 沒連上真站（Origin/VPN）。確認在**巴西**、token 沒過期（重跑 `.\webcapture.ps1 124`）。 |
| server 狂洗 `[404] …​.webp`、遊戲卡 splash | 缺跨平台材質。**VPN 開巴西**後跑 `.\fetch_assets.ps1`（會掃缺圖去真站補）。 |
| 遊戲跳「連線中斷 / MSG202」 | token 過期或 VPN 掉，重跑 `.\webcapture.ps1 124`。 |
| Chrome 找不到網站 / 憑證錯 | 用最新版腳本（已用 hosts + 自簽憑證 + `--ignore-certificate-errors`）。 |
| PowerShell 紅字「執行原則」 | 先跑 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`。 |
| `wscapture_finish` 說「賠付公式對不上」 | 先別發樣本，把訊息貼給我（可能是抓到殘缺 frame 或協定變動）。 |

---

## 一句話總結

- **抓封包**：`.\webcapture.ps1 124` → 進遊戲下注/開 autoplay → `.\webcapture_finish.ps1 124`。
- **要看的**：`games\124\math\EXTRA_SUMMARY.json`（extra 出現哪些倍率、每格頻率/E[extra]）。
- 收工：`.\stop.ps1`。
