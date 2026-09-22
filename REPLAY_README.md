# JILI 696 工具更新包（每局雙檔 + 單檔重播 + domain-lock 免 hosts）

疊在你**現有的擷取包**上（同一個 `jili/` 資料夾）。
**不含 `config.json`（帳號不動）、不含錄製資料（自己重抓）、不含 crypto wasm（用你包裡原本那套）。**

```
unzip -o jili_replay_update.zip      # 覆蓋到你的 jili/ 上層
```

## 換了 / 加了什麼
| 檔 | 用途 |
|---|---|
| `routex/server.py` | 重播引擎：`REPLAY=<exchanges>` 單檔推導 init+config+spins；`REPLAY_SPINS=<dir>` 每局回放 |
| `webcap_pretty.py` | 批次收尾也輸出每局雙檔（與 live 一致） |
| `spins_split.py` | 舊 capture 補切每局雙檔 |
| `web_own.sh` | **Mac 一鍵重播**（免 sudo/免改 hosts；已含 domain-lock 繞過） |
| `routex/dl_domlock_solve.py` | domain-lock forge/verify（純 python，跨平台；Windows 也能用） |
| `stop.sh` / `DOMLOCK_SOLVED.md` | 收工腳本 / domain-lock 原理文件 |
| `games/696/fg5_696.proto` | spin 完整結構 schema |

## 每局兩個檔（分析 vs 回放）
每把 spin 落**兩份**，檔名=局號（單調遞增＝順序）；live 擷取 / 批次收尾 / `spins_split.py` 三路一致：
```
games/696/webcap/spins/<局號>.json       純分析、無 raw（機率團隊研究用）
games/696/webcap/spins_raw/<局號>.json   含 raw：{round_id,idx,type,ret,raw}（回放用）
```

## 擷取（spin＝連正式站）
照原 `webcapture.sh`：doc host 指本機、`/fg5/req` 走真站，shim 側錄+讀 key 當場解 → 自動產 `spins/`+`spins_raw/`。

## 重播（連本地 mock）——★推薦：domain-lock 已解，免 sudo/免改 hosts★
前端有 Jscrambler DomainLock，但已用「路徑④：鑄一個撞中白名單的自有子網域」繞過，**零改 bundle**。

> ★本包已附回放資料★：`games/696/webcap/spins_raw/`（829 局）＋ `exchanges_ordered.jsonl`，
> 不用先跑擷取就能直接播。
>
> ★指定局號★：加 `REPLAY_ROUNDS=<局號>[,<局號>…]`（可給片段；**依你給的順序播**），
> 不然預設照局號順序循環播全部 829 局。

### Mac：一行搞定
```
REPLAY=games/696/webcap/exchanges_ordered.jsonl \
REPLAY_SPINS=games/696/webcap/spins_raw \
./web_own.sh <你的base域名>

# 只播指定幾局：
REPLAY=games/696/webcap/exchanges_ordered.jsonl \
REPLAY_SPINS=games/696/webcap/spins_raw \
REPLAY_ROUNDS=24126-883680-00240696,24126-544640-00800696 \
./web_own.sh <你的base域名>
# 例：REPLAY=games/696/webcap/exchanges_ordered.jsonl ./web_own.sh mydomain.com
```
它會：鑄撞中子網域 → 起 mock（8443、免 sudo、INJECT_BUNDLE=1）→ 開拋棄式 Chrome（`--host-resolver-rules` 全映到 mock）。
盯 mock 視窗：看到 `kind=init[...]`、**沒有** `/webservice/event/jscrambler`（DomainLock）＝過了。**別開 DevTools。**

### Windows：同原理，手動三步（也免改 hosts）
```
:: 1) 鑄一個撞中白名單的自有子網域（記下印出的 host）
.venv\Scripts\python routex\dl_domlock_solve.py preimage <你的base域名> 1

:: 2) 另開視窗起 mock
set REPLAY=games/696/webcap/exchanges_ordered.jsonl
set PORT=8443 & set TLS=1 & set INJECT_BUNDLE=1
.venv\Scripts\python routex\server.py

:: 3) 開 chrome.exe（拋棄式 profile，全映到 mock）；<host>=第1步印出的
chrome.exe --user-data-dir=%TEMP%\jili-own --host-resolver-rules="MAP * 127.0.0.1:8443" ^
  --ignore-certificate-errors --disable-quic --no-first-run ^
  "https://<host>/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&gameID=696&iu=true&legalLang=true&skin=0"
```

### 每局回放（用 raw 檔）
```
REPLAY=…/exchanges_ordered.jsonl REPLAY_SPINS=games/696/webcap/spins_raw ./web_own.sh <base>
```
（`REPLAY_SPINS` 指 **spins_raw**（含 raw）；init 仍取自 `REPLAY`。）

server 啟動印 `[replay] N spin` / `[initseq] M（第一筆 type=1）`，兩個非 0＝單檔推導成功。

## 小提醒
- `INJECT_BUNDLE=1` 用你包裡的 `mockkeys.json`+`wasm_pub_patches.json` 改 pub（同擷取那套）；若 log 出現 `.wasm`(crypto) 404，回報我補 patched wasm。
- domain-lock 繞過是**client 端**；本地 mock 重播不檢查後端 Origin，沒問題。
- spin 依序回放、跑完循環；餘額只有 spin 前/後一次翻轉（盤面順序精準）。
