# 807 真站擷取 SOP（Windows）

給第一次 clone 本專案、要在 **Windows** 上擷取 807 封包的人。照本文件由上到下操作即可。
遊戲：807 Fortune Garuda 1000（迦羅战神1000），入口 `/fg1000/`。
實測環境：Windows 11 / Python 3.12 / 中文語系(cp950)。

---

## A. 前置安裝與設定（只做一次）

1. **安裝軟體**
   - Python 3.12（安裝時勾選 Add to PATH）
   - Google Chrome
   - WireGuard（VPN，需能連巴西節點；隧道設定由你自備）
2. **安裝 Python 套件**（擷取只需這兩個；若要重新編譯 proto 才需 `grpcio-tools`）
   ```powershell
   python -m pip install cryptography requests
   ```
3. **設定帳號 `config.json`**（放專案根目錄，與 `jili_login.py` 同層）
   - 參考 `games\807\login_config.example.json`，把 `login` 區塊與 `login_accounts` 併入根目錄 `config.json`。
   - 填入你自己的 agent JWT（純 token，不含 `bearer `）與 player_id。
   - **`config.json` 內含真 Token，絕對不要 `git add` / 提交。**
4. **VPN 節點**
   - 取得入口要用**台灣出口**（巴西會回 403）；玩遊戲要用**巴西 São Paulo 出口**。
   - WireGuard：**停用巴西隧道 = 台灣出口**；**啟用巴西隧道 = 巴西出口**（你人在台灣時）。

> Windows 相容性（UTF-8 編碼、Chrome 自動尋找、UTF-16 入口檔處理）已內建於本專案腳本，Mac 亦相容，無需額外調整。

---

## B. 重要觀念（先讀）

- 每行指令**整段複製貼上**，不要只打檔名（只打 `capture_server.py` 會報「無法辨識」）。
- 全程用 **3 個 PowerShell 視窗**：終端 A（伺服器）、終端 B（遊戲）、終端 C（監看）。
- **入口 ssoKey 一次性**：遊戲一開就消耗。被踢掉／重連時務必**重新取得入口**。
- **終端 A 啟動後不要關**：只要它不重啟，封包都進**同一個 session 資料夾**；重啟會開新夾、拆散資料。

---

## C. 首次啟動（完整流程）

### 步驟 0：開三個視窗，各自切到專案資料夾

終端 A、B、C 各貼一次：

```powershell
cd C:\lechengwork\dyson\jili_hack_tool
```

（路徑依你 clone 的位置調整。）

### 步驟 1：台灣出口，取得入口（終端 A）

WireGuard **停用巴西隧道**，確認出口是台灣：

```powershell
python -c "import json,urllib.request;print('exit =', json.loads(urllib.request.urlopen('https://ipinfo.io/json',timeout=8).read())['country'])"
```

要印 `exit = TW`。取得入口（`--account` 換成你 config 裡的帳號名）：

```powershell
python jili_login.py 807 --account usd --json > games\807\login_session.local.json
```

回 403 或拿到 null → 確認是台灣出口後重試。

### 步驟 2：切巴西出口

WireGuard **啟用巴西隧道**，確認：

```powershell
python -c "import json,urllib.request;print('exit =', json.loads(urllib.request.urlopen('https://ipinfo.io/json',timeout=8).read())['country'])"
```

要印 `exit = BR`。

### 步驟 3：啟動擷取伺服器（終端 A）

```powershell
python games\807\refresh_assets.py
python -B -u games\807\capture_server.py
```

看到這行代表成功，**此視窗全程保持開啟**：

```
[807 capture] session=C:\...\games\807\webcap\20261104-xxxxxx; listen=https://127.0.0.1:8807
```

（`REQUIRES split /etc/hosts` 是通用提示，807 不用理會。）

### 步驟 4：打開遊戲（終端 B）

```powershell
python -B -u games\807\open_capture.py --seconds 43200
```

跳出專用 Chrome 進入遊戲（獨立視窗，不影響日常 Chrome）。保持開啟。

### 步驟 5：啟動監看（終端 C）

```powershell
python games\807\watch_fields.py --max-new-rounds 0 --out games\807\monitor_usd
```

### 步驟 6：確認擷取接上，開始轉

進遊戲後先別轉，先確認（任一視窗）：

```powershell
python -c "import json,os;s=open(r'games\807\current_session.txt',encoding='utf-8').read().strip();f=os.path.join(s,'exchanges_ordered.jsonl');rows=[json.loads(l) for l in open(f,encoding='utf-8')] if os.path.exists(f) else [];print('session=',s);print('封包',len(rows),'簽章OK',sum(1 for r in rows if r.get('_sig_ok')))"
```

有封包且簽章 OK 後即可轉輪。**三種模式都轉**：普通 / 1.5× / 8×（畫面自行切換）。

---

## D. 每次 SPIN 的封包記錄到哪（即時 math）

每抓到一局，終端 A 會印一行，例如：

```
[807 decode] seq=.. type=0 ret=0 payload=..B signature=OK math=OK file=C:\...\games\807\math\<局號>.json
```

**只有成功的 SPIN（type0 / ret0 且簽章通過）** 會即時解碼、驗簽、codec round-trip 驗證後，**同時寫到兩個位置**：

| 位置 | 說明 |
|---|---|
| `games\807\math\<局號>.json` | **主資料集**，與既有 2399 樣本同一夾，累積用；這是最終要的機率資料 |
| `games\807\webcap\<session>\math\<局號>.json` | 本次 session 的副本 |

其他規則：

- 原始加密封包**一律**先存進 `webcap\<session>\exchanges.jsonl`（即使該局無法轉 math）。
- **無法解碼 / 未知結構**的回應**不會**寫成 math（避免假資料），改記到 `webcap\<session>\math_errors.jsonl`，終端 A 顯示 `math=ERROR ...`；原始封包仍保留。
- **既有 math JSON 不會被覆蓋**：同局已存在且內容相同→略過；若內容不同→報錯並保留原檔（不會蓋掉你手改過的資料）。

所以轉一局後，可直接到 `games\807\math\` 看到新局號的 `.json` 檔，不需等收尾。

---

## E. 被踢掉 / 重複登入後的「精簡重連」

遊戲跑一段時間會被後端踢掉（session 逾時或重複登入）。**不需要重跑整套**：

> **終端 A、終端 C 保持開著不要關。** 只做下面三步。

1. 終端 B：`Ctrl+C`（關舊遊戲視窗）。
2. VPN 切台灣 → 拿新入口 → 切回巴西（前後各確認 `exit = TW` / `BR`）：
   ```powershell
   python jili_login.py 807 --account usd --json > games\807\login_session.local.json
   ```
3. 終端 B 重開遊戲：
   ```powershell
   python -B -u games\807\open_capture.py --seconds 43200
   ```

新遊戲會重連並把封包存進**同一個 session**，資料不被拆散。

---

## F. 收尾（玩夠了）

依順序：

1. 終端 B：`Ctrl+C`（關遊戲）。
2. 終端 A：`Ctrl+C`（停伺服器）。
3. 終端 C：等讀完最後一筆，`Ctrl+C`。
4. 封存並重新驗簽（在 session 底下產生 `export\`，含驗簽後的 `exchanges_ordered.jsonl` 與 `summary.json`）：
   ```powershell
   python games\807\finish_capture.py
   ```

即時 math 已在擷取當下寫好；`finish_capture.py` 主要做封存與重新驗簽。

---

## G. 輸出位置總表

| 路徑 | 內容 | 機密 |
|---|---|---|
| `games\807\math\*.json` | **機率主資料集**（含既有樣本 + 本次即時新增） | 否 |
| `games\807\webcap\<session>\exchanges.jsonl` | 原始加密封包 | 是 |
| `games\807\webcap\<session>\exchanges_ordered.jsonl` | 解密＋驗簽後可讀版 | 是 |
| `games\807\webcap\<session>\math\*.json` | 本次 session 的 math 副本 | 是 |
| `games\807\webcap\<session>\math_errors.jsonl` | 無法轉 math 的局（原始保留） | 是 |
| `games\807\webcap\<session>\key.json` / `grv.jsonl` | session 金鑰 / client 隨機值 | **高度機密** |
| `games\807\webcap\<session>\export\` | `finish_capture.py` 封存產物 | 是 |
| `games\807\monitor_usd\` | 監看偵測到的新欄位事件 | — |

- 目前 session 記在 `games\807\current_session.txt`。
- `webcap/`、`runtime/`、`current_session.txt`、`login_session.local.json`、`monitor*/` 皆已 gitignore。
- **不要提交** `config.json`、金鑰、原始請求。

---

## H. 常見錯誤對照

| 畫面 / 訊息 | 意思 | 處理 |
|---|---|---|
| `無法辨識 'capture_server.py'…` | 少打 `python` 和路徑 | 整段貼 `python -B -u games\807\capture_server.py` |
| `MSG 999.1 无法连接服务器` | 連不到真站 | 確認出口＝BR；確認 hosts 無 `jlfafafa` 殘留（見下） |
| `MSG 999.2` | 登入成功但真站 WebSocket 回 502（後端故障） | 本機無法修，隔段時間重試；持續則記單號/時間交平台 |
| `MSG 103` + 黑畫面 | sso-login 被真站打回（入口已消耗或後端不穩） | 拿**新入口**重連 |
| 跑一陣子被踢、重開說無法連接 | 入口一次性、被重用 | 用「精簡重連」（E 節） |
| `ConnectionRefused` / `10061`（開遊戲時） | 終端 A 伺服器沒在跑 | 先完成步驟 3 再開遊戲 |
| `807 capture shim is missing` | 伺服器還沒就緒 | 等終端 A 印 `listen=...` 再執行步驟 4 |
| 終端 A 出現 `math=ERROR` | 該局結構無法轉 math | 原始封包已保留；回報該 payload 供分析，勿當成資料缺失 |
| `UnicodeDecodeError: 'cp950'…` | 用到未含 Windows 修正的舊腳本 | 確認 clone 的是含 Windows 修正的版本 |
| F12 打不開 / 開了卡死 | 遊戲反偵錯 | 改用 `open_capture.py --netlog <路徑>` 錄網路紀錄 |

---

## I. hosts 檢查 / 清理（偶爾需要）

檢查殘留（回 `0` 代表乾淨）：

```powershell
(Get-Content "$env:WINDIR\System32\drivers\etc\hosts" | Select-String 'jlfafafa').Count
```

若非 0，用**系統管理員** PowerShell 清掉（只刪 `# jili-replay` 標記行）：

```powershell
$h="$env:WINDIR\System32\drivers\etc\hosts"; (Get-Content $h) | Where-Object { $_ -notmatch '#\s*jili-replay\s*$' } | Set-Content $h -Encoding ASCII
ipconfig /flushdns
```

> 不要用 `stop.ps1` 清理，它會順便斷掉 WireGuard VPN。

---

## J. 備註

- 用 INR 帳號改 `--account inr`，並先在 `config.json` 補 INR 的 JWT／player_id；監看輸出可改 `--out games\807\monitor_inr`。
- astc 圖檔不用處理：桌機 Chrome 只載 webp/png，不會請求 astc。
- 離線回放／驗證（不需真站、不需 VPN）：`python replay_807.py`、`python games\807\verify_mock.py --source math`、`python games\807\verify_math.py`。
