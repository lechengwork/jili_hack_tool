# JILI Mock Server — Pipeline 規範

對照 `habanero/PIPELINE.md`。差異來自 JILI 的三個特性：Cocos Creator 3.6 前端、
後端域名走 URL query param（反轉字串）、遊戲 JS 經 jscrambler 混淆。

## 目錄結構

```
jili/
├── config.json            # 站台設定：域名、登入 API、apiId
├── games.json             # gameID → 遊戲名（16 個種子，之後自動擴充）
├── jili_capture.py        # Step 1: 擷取靜態資源 + 後端流量
├── game_analyze.py        # Step 2: 判定協定 + 產出 game_config.json
├── gen_server.py          # Step 3: 檢查資料 + go build
├── run_game.py            # 一鍵 capture + analyze
├── .venv/                 # python3.12 + playwright + requests
├── games/
│   ├── shared/            # 跨遊戲共用（astarte2 大廳、smallicon 圖示）
│   │   ├── astarte2/
│   │   └── smallicon/
│   └── <GAMEID>/
│       ├── static/fg5/    # 該遊戲的 Cocos build
│       ├── traffic_raw.json   # Step 1 產出，中間檔
│       └── game_config.json   # Step 2 產出，server 用來 replay
└── jili_server/
    ├── main.go        # 路由 + 啟動
    ├── panel.go       # 面版 + 擷取 API
    ├── static.go      # 遊戲掃描 + 靜態檔服務
    ├── handler.go     # HTTP replay + WS replay
    ├── tls.go         # 自簽憑證（首次啟動自動產生）
    ├── gameconfig.go  # JSON 結構
    └── .gitignore     # 執行檔與憑證不入庫
```

## 四步 Pipeline

### Step 0 — 環境（只需做一次）

```bash
cd /Users/dyson/Downloads/jili
python3.12 -m venv .venv
./.venv/bin/pip install playwright requests
./.venv/bin/python -m playwright install chromium
```

### Step 1 — 擷取資源

```bash
./.venv/bin/python jili_capture.py GAMEID [--url URL] [--spins N] [--headless]
```

- 開 Playwright Chromium 進遊戲
- 靜態資源依 URL path 落地：`/astarte2/*` 和 `/smallicon/*` 進 `games/shared/`，
  其餘進 `games/<GAMEID>/static/`
- `gs` / `platform` / `be` 三個後端 host 的所有 HTTP response → `traffic_raw.json`
- WebSocket frame（文字與二進位都收）→ `traffic_raw.json`
- 沒錄到任何後端流量會 exit 3 並提示原因

**入口三選一**（優先序）：
1. `--url "<含 ssoKey 的完整遊戲 URL>"`
2. `config.json` 的 `login.enabled=true` → 自動呼叫 LoginGame 換 game_url ← **主要路徑**
3. `config.json` 的 `manual_url.url`

#### LoginGame（推薦）

```
POST http://<api-host>/api/LoginGame
authorization: bearer <JWT>
{"device":1,"language":"zh-CN","player_id":"tryplayer001usd","game_id":"111000696"}
→ {"game_url":"https://uat-wbgame.jlfafafa3.com/fg5/?ssoKey=...&gameID=696..."}
```

- 回傳的 `game_url` **只能用一次**，所以不要手動存起來重複用。
  自動登入每次跑都換一張新的，這正是要走這條路徑的原因。
- `body` 內的值支援 `{gameid}` 與 `{gameid:06d}` 佔位符。
  `game_id` 預設 `111{gameid:06d}`（696 → `111000696`），
  **這是從單一樣本推得的**，若其他遊戲對不上就改 `config.json`。
- `token_path` 取到的值若以 `http` 開頭，就直接當完整遊戲 URL 用，不再自行組裝。

#### VPN

遊戲站需要**巴西**出口。Surfshark 的 macOS 版只有 GUI、沒有 CLI，
所以 VPN 要自己在 app 裡連。連上之後是系統層生效，
capture 的 Playwright 瀏覽器會自動走它，不需要額外設定。

確認目前狀態：

```bash
scutil --nc list                       # 看 Surfshark 是否 Connected
curl -s https://ipinfo.io/json         # 看出口國家是否 BR
```

### Step 2 — 分析

```bash
./.venv/bin/python game_analyze.py GAMEID [--verbose]
```

- 判定傳輸協定（HTTP / WS）與主迴圈 endpoint
- WS 二進位 frame 會做格式嗅探：SFS2X / protobuf / gzip / zlib / JSON-in-binary
- 輸出 `game_config.json`（含完整 replay 資料）
- 協定判不出來會 exit 3

### Step 3 — Build

```bash
./.venv/bin/python gen_server.py [GAMEID] [--run]
```

### Step 4 — 啟動

```bash
cd jili_server && ./jili_server
```

面版：`https://localhost:8443`

| 環境變數 | 預設 | 說明 |
|----------|------|------|
| `PORT` | `8443` | 監聽埠 |
| `TLS` | `1` | `0` 關閉 TLS（多半會讓遊戲連不上，見下） |
| `PROJECT_DIR` | `..` | 專案根目錄 |
| `SERVER_URL` | `https://localhost:$PORT` | 對外 URL |

## 面版

`GET /` 的遊戲列表，分「已擷取 / 未擷取」兩區：

- 已擷取 → 點卡片直接開遊戲，badge 顯示 replay 模式與筆數
- 未擷取 → 卡片上的「擷取」鈕，呼叫 `POST /api/capture/:gameid` 在背景跑 `run_game.py`
- 右下角浮出即時 log 視窗，輪詢 `GET /api/capture/:gameid/status`
- 頂端輸入框可貼「含 ssoKey 的完整遊戲 URL」，自動解析 gameID 後開始擷取
  （清單裡沒有的遊戲用這個）

## Server 架構

### 路由

gin 的 catch-all `/*path` 不能和同層具體路徑並存，所以 GET 一律走單一 catch-all，
在 handler 內部分派：

| 條件 | 行為 |
|------|------|
| `/<id>/webservice/event/*` | 回 204（遙測 stub） |
| WebSocket Upgrade 標頭 | WS replay |
| path 在 `http.replay` 裡 | HTTP replay |
| 其他 | 靜態檔 |

POST 沒有衝突問題，直接掛 catch-all。

### Replay 模式

- **HTTP**：`path → [依序的回應]`，每個 path 各自維護游標，循環播放
- **WS**：取 frame 最多的那條連線，client 每送一個 frame 就推出下一批 RECV frame，
  播完循環

### Shared Fallback

`games/<id>/static/` 找不到 → 退到 `games/shared/`。
`astarte2/` 與 `smallicon/` 只存一份，所有遊戲共用。

### NoRoute Fallback

遊戲 JS 用絕對路徑請求時，從 `Referer` 推斷所屬遊戲；再不行退到 `games/shared/`。

## 與 habanero 的關鍵差異

| 項目 | Habanero | JILI |
|------|----------|------|
| 前端引擎 | 自家 PIXI | Cocos Creator 3.6 |
| 後端域名來源 | index.html 內嵌 JSON（要 patch） | **URL query param，反轉字串**（不用 patch） |
| 協定 | HTTP POST `/pf` | **未知**（要靠 capture 判定） |
| JS 保護 | 無 | **jscrambler**（含反除錯與內建物件竄改） |
| 進入方式 | demo 站免登入 fun mode | 需 ssoKey |
| Server scheme | HTTP | **必須 HTTPS**（遊戲 JS 寫死 `https://`） |
| 遊戲識別 | keyname 字串 | 數字 gameID |

### 為什麼一定要 HTTPS

`index.html` 有三處把後端 URL 寫死成 `"https://" + 反轉還原的域名`：

```js
let gs = GetLinkParameterByName("domain_platform").split("").reverse().join("");
let url = "https://" + gs + "/webservice/event/trigger?";
```

所以 mock server 走純 HTTP 的話，遊戲 JS 會去打 `https://localhost:8443/...` 而失敗。
`tls.go` 在首次啟動時自動產生 `localhost` 自簽憑證，瀏覽器第一次要按「進階 → 繼續前往」。

### 反轉字串

JILI 把域名反著存進 query param：

```
gs=moc.1afafaflj.df-tolsbw-tau   →  uat-wbslot-fd.jlfafafa1.com
domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau  →  uat-wbslot-platform.jlfafafa3.com
be=moc.2afafaflj.ipabewbw-tau    →  uat-wbwebapi.jlfafafa2.com
```

面版產生的遊戲連結會把這幾個參數換成 `reverse("localhost:8443/<gameid>")`，
所以遊戲的後端請求會自然落回 mock server。

## 目前狀態與已知問題

- **協定未確認**：`uat-wbgame.jlfafafa3.com.har` 只有 4 筆 jscrambler 遙測，
  沒有任何遊戲流量。要跑一次 Step 1 才知道 JILI 走 HTTP 還是 WS。
- **遊戲卡在 main bundle**：靜態資源齊全、Cocos 引擎完整啟動
  （`cc.game` / `cc.assetManager` 就緒，`internal` + `main` bundle 都載入，
  `virtual:///prerequisite-imports/main` 也註冊成功），但
  `assets/main/index.22de5.js:1:257192` 拋
  `TypeError: Cannot read properties of undefined (reading 'random')`。
  最可能是缺後端／平台上下文，等有真實 capture 再驗證。
- **jscrambler 會竄改內建物件**：連 Playwright 的 `page.evaluate` 都會被弄壞
  （`argsAndHandles.slice is not a function`）。用 Playwright 檢查頁面狀態時，
  對 `response` 事件掛 listener 會干擾量測，改用頁內
  `performance.getEntriesByType('resource')` 比較可靠。
- **遊戲清單只有 16 個**：從 `smallicon/Icons/*.jpg` 的檔名推出來的。
  抓到平台的遊戲列表 API 後再補進 `games.json`。
