# 696 重播「約一個月後失效」修復指南（date-lock + MSG 8）

> 給接手的工程師 / AI：如果**以前能重播、現在打開就卡**，八成是這個問題。照「Windows 一鍵」做即可。

---

## TL;DR（Windows）

```powershell
cd <解壓後的資料夾>        # 內含 routex\、games\696\、replay_win.ps1
.\replay_win.ps1           # 會跳 UAC → 自動把系統時鐘撥回擷取日 → 跑重播 → 收工自動還原時鐘
```

- 只播指定局：`.\replay_win.ps1 24126-883680-00240696`（可逗號多局）
- 收工：在 mock log 視窗按 **Ctrl+C**（會**自動還原系統時鐘**），再跑 `.\stop.ps1` 還原 hosts。
- **★全程別開 DevTools★**（會觸發 Jscrambler 防護、卡住 loader）。

成功長相：mock log 出現 `handshake` → `kind=init[...]` → `spin[...]`；遊戲畫面正常、**沒有** dateLock 也**沒有** MSG 8，能連續轉。

---

## 症狀 → 這份文件治的就是它

重播舊 build 時，遊戲會出現以下**任一**（都在 handshake 前後把遊戲擋住）：

1. mock log 出現 client 主動 POST `/webservice/event/jscrambler`，內容 `{"Type":"dateLock",...}`，並伴隨 `/v2/notifications` 的 `Code violation: j-002-00003`。→ **Jscrambler Date-Lock（日期鎖）到期**。
2. 遊戲彈出系統訊息「**发现设备时间异常，请检查并校准您的设备时间 (MSG 8)**」。→ **遊戲內建校時檢查**。

兩者**都是時間觸發的**：build 打包時烤進去，約**一個月後**才生效，所以當初擷取當天完全碰不到、也沒人處理過。跟帳號、協定、你的工具**都無關**。

---

## 原理（給 AI 除錯用，照做不需要懂）

- **Date-Lock** 讀「裝置當下時間」跟烤進 bundle 的到期日比 → 過期就觸發反制。
- **MSG 8** 比對「**裝置時間** vs **伺服器回應裡的時戳**（mock server 每筆回應的信封 f1 = server_time_ms）」→ 差太多就判「設備時間異常」。
- 重播用的是**當初擷取（2026-09-11）**那份錄好的資料。要同時騙過兩道鎖，只要讓**整台機器的真實時鐘回到 2026-09-11**：
  - 裝置時間 = 09-11 → 在 date-lock 窗內（過）。
  - 是**真實 OS 時鐘**（不是 JS 竄改）→ Jscrambler self-defending 偵測不到（**別用 JS 改 Date，會被判 GameDebugging**）。
  - 本機 mock server（python）和 Chrome **同讀這個系統時鐘** → server 回應 f1 也是 09-11 = 裝置時間 → MSG 8 過。
- `replay_win.ps1` 就是：記錄真實時間 → `Set-Date` 撥回 09-11 + 停 w32time 自動同步 → 跑既有 mock server + Chrome → 收工（含 Ctrl+C）在 `finally` 自動把時鐘還原、重開同步。

**關鍵心法：server 和瀏覽器「兩邊」都必須看到同一個過去時鐘。** 系統時鐘一次搞定兩邊。

---

## 若一鍵不行（除錯順序）

1. **還是 MSG 8** → 代表 server 回應時戳沒跟著變（server 沒讀到撥回的系統時鐘）。確認：
   - `replay_win.ps1` 的 `Set-Date` 有成功（視窗有印「① 撥回系統時鐘 → 2026-09-11…」）。
   - server 是**本機 python**、且在時鐘撥回**之後**才啟動（本腳本順序已保證）。
   - 驗證 server 送出的時戳：啟動時多帶 `DEBUG_TS=1`（`$env:DEBUG_TS="1"` 再跑），mock log 會印 `[ts] envelope f1 = … (2026-09-11…)`；若印的是**今天日期**，就是系統時鐘沒撥到 / server 讀到真實時間。
2. **還是 dateLock** → 系統時鐘沒真的變早，或 09-11 仍晚於鎖定日。把日期再往前調：`$env:FAKE_DATE="2026-09-05 12:00:00"; .\replay_win.ps1`。
3. **卡在 JILI splash、狂 404 `/fg5/assets/*.webp`** → 這是**跨平台貼圖**問題（不是時間鎖）：mirror 只存了 Mac 的 `.astc`，Windows GPU 要 `.webp`。跑 `python fetch_missing_assets.py`（需巴西 VPN）補檔，詳見 `HANDOVER_WINDOWS.md`。
4. **找不到 Chrome / python** → 設 `$env:CHROME="C:\path\to\chrome.exe"`；確認 `python` 在 PATH。

---

## 隔離版：不動系統時鐘/hosts、可【同時玩真遊戲】（`replay_win_isolated.ps1`）

`replay_win.ps1` 是**全機**做法（改系統時鐘 + 改 hosts），所以**重播進行中，同一台機器沒辦法同時連 JFS 玩真的**（系統時鐘被撥到 09-11、遊戲域名被導到本機 mock）。

如果要**同機同時玩真遊戲**，改用 **`replay_win_isolated.ps1`**（per-process 隔離，不動系統時鐘、不動 hosts、免 admin）：
- 時間用 **RunAsDate** 只騙 `python server` 和 replay `chrome` 兩個進程；DNS 用 Chrome `--host-resolver-rules` 只導向這個 Chrome 實例。
- → 另開一個**正常的 Chrome** 就能同時連 JFS 玩真遊戲，互不干擾。

前置：
1. 下載 **RunAsDate**（x64，https://www.nirsoft.net/utils/run_as_date.html），放本資料夾或設 `$env:RUNASDATE`。
2. ★先在 RunAsDate GUI 勾一次「**Inject the date/time into child processes**」★——Chrome 遊戲 JS 跑在 renderer 子進程，不勾的話子進程沒被騙時鐘 → 照樣 dateLock。
3. `.\replay_win_isolated.ps1`（參數同上）。

兩個要現場驗的坑：
- **RunAsDate 子進程注入沒生效** → 進遊戲出 dateLock。去 GUI 勾好再跑。
- **`--host-resolver-rules` 在某些 Windows 不穩**（這正是 `replay.ps1` 當初改用 hosts 的原因）。若 replay Chrome 一直連不到本機 mock（splash 卡死、mock log 沒 `[GET]`），就退回 `replay_win.ps1`（全機版，但就不能同機玩真的了）。

> 只想穩、不需要同機玩真的 → 用 `replay_win.ps1`；真遊戲需求就拿**另一台裝置**連 JFS。要同機共存才用這支隔離版。

---

## 這次改了什麼 / 沒改什麼

- **沒有改任何協定或 crypto**；重播資料、pub-patch、mock server 邏輯全不動。
- 唯一新增：`replay_win.ps1`（Windows 一鍵，含時鐘撥回+還原）。舊的 `replay.ps1` 仍在，但**單獨跑它現在會撞雙鎖**——請改用 `replay_win.ps1`。
- Mac 對應版：`replay_cft.sh`（用 Chrome for Testing + libfaketime 撥時鐘，免改系統時鐘；Mac 專用）。

## 注意
- ⚠ 撥系統時鐘會影響**整台機器**的時間（其他 app / 憑證 / 排程），僅重播期間；`replay_win.ps1` 結束會自動還原。建議用專用機器 / 環境。
- ★別開 DevTools★。收工 `Ctrl+C` → 自動還原時鐘 → 再 `.\stop.ps1` 還原 hosts。
- 日期只要落在「build 到期日之前、且接近擷取日」都行；預設 2026-09-11。未來若又鎖，先試把 `FAKE_DATE` 往前調。
