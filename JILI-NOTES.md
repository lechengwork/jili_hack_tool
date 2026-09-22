# JILI 逆向筆記

> 來源：`uat-wbgame.jlfafafa3.com.har` + `game_site_backup/` + 本機重放實測
> 樣本遊戲：**gameID 696 — Fortune Garuda 500**
> 日期：2026-08-27

## 站台架構

| 角色 | 域名 | 用途 |
|------|------|------|
| 遊戲前端 | `uat-wbgame.jlfafafa3.com` | Cocos build、大廳 bundle、遊戲圖示 |
| 遊戲服 (gs) | `uat-wbslot-fd.jlfafafa1.com` | 遊戲主邏輯 **（協定未確認）** |
| 平台服 | `uat-wbslot-platform.jlfafafa3.com` | 排行榜、我的最愛、信件、遙測 |
| Web API (be) | `uat-wbwebapi.jlfafafa2.com` | 推測為登入／帳務 **（未擷取到）** |

## 入口 URL

```
https://uat-wbgame.jlfafafa3.com/fg5/
  ?ssoKey=<TOKEN>
  &lang=zh-CN
  &apiId=1778
  &be=moc.2afafaflj.ipabewbw-tau
  &domain_gs=1afafaflj
  &domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau
  &gameID=696
  &gs=moc.1afafaflj.df-tolsbw-tau
  &iu=true&legalLang=true&skin=0
```

`be` / `domain_platform` / `gs` 是**字元反轉**後的域名。還原方式：

```js
GetLinkParameterByName("gs").split("").reverse().join("")
```

前端一律再加上 `https://` 前綴（寫死，見 `index.html` 的
`event/trigger`、`event/jscrambler`、`event/loading` 三處）。

## 前端結構

Cocos Creator **3.6** web-mobile build。

```
/fg5/
  index.html                    遊戲入口（35KB，含 SystemJS 啟動與遙測）
  index.7dcc1.js                SystemJS 入口模組
  application.959cc.js          Application 類別，呼叫 cc.game.init()
  cocos-js/cc.9a83d.js          Cocos 引擎 2.1MB
  src/
    polyfills.bundle.*.js
    system.bundle.*.js          SystemJS
    import-map.*.json           {"imports":{"cc":"./../cocos-js/cc.*.js"}}
    settings.*.json             cc.game.init 的 settingsPath
    zip-bundler/fflate.min.*.js
  assets/
    internal/                   Cocos 內建資源
    main/                       主遊戲 bundle（1.4MB，jscrambler 保護）
    game/                       遊戲資源，game.*.zip + native/（貼圖音效）
/astarte2/3.6/web-mobile/       大廳 bundle（跨遊戲共用，17MB）
/smallicon/Icons/<gameID>_cn.jpg  遊戲圖示
/smallicon/lang/zh-CN/strings.json  i18n（2499 條，無遊戲名對照）
```

### 啟動序列（實測）

```
index.html
 → src/polyfills.bundle.js
 → src/system.bundle.js
 → src/import-map.json          （SystemJS 自行 fetch）
 → index.7dcc1.js               （inline System.import）
 → application.959cc.js
 → cocos-js/cc.9a83d.js
 → src/settings.52a7a.json      （cc.game.init）
 → assets/internal/{config,index}.js
 → src/zip-bundler/fflate.min.js
 → assets/main/{config,index}.js
 ✗ TypeError: Cannot read properties of undefined (reading 'random')
      at assets/main/index.22de5.js:1:257192
```

錯誤發生時引擎其實已經完整就緒：`cc.game`、`cc.assetManager` 都在，
`internal` 與 `main` 兩個 bundle 都載入，`virtual:///prerequisite-imports/main`
也已註冊。所以**不是缺檔案**，是主 bundle 內部取不到某個物件。
最可能是缺後端／平台上下文（目前完全沒有 mock 後端）。

## jscrambler 保護

主 bundle 與大廳 bundle 都經過 jscrambler：

- 字串以 `\x`/`\u` 逃逸 + 執行期解碼表（全域 `P_feQ`）還原
- **會竄改內建物件**：頁面載入後 Playwright 的 `page.evaluate` 會壞掉，
  報 `argsAndHandles.slice is not a function`
- 有反除錯回報：偵測到會 POST 到
  `https://notification.jscrambler.com/v2/notifications`，
  以及 `https://<platform>/webservice/event/jscrambler`

使用者原本那份 HAR 裡就有一筆：

```json
{"title":"Real time notification",
 "description":"Code violation: j-016-00079",
 "body":{"0":"j-016-00079", ...}}
```

代表錄製當下 DevTools 開著就被偵測到了。要抓乾淨的流量，
建議關掉 DevTools 用 Playwright 側錄，或用系統層 proxy（mitmproxy）。

## 已擷取的平台 API（僅 3 筆，來自 backup）

```
POST /favoriteservice/OnLogin
  → {"cmdType":4,"content":{"Enabled":true,"Favorites":null,"Promotions":null,
                            "Expired":null,"DAU":null,"BigWined":false}}

POST /rankingservice/user/GetRankingListV2
  → {"Data":null,"DisplayData":null,"Error":"ranking not exist or begin",
     "NeedWebView":false,"ExtraWebView":0}

POST /rankingservice/user/GetMailList
  → {"Error":"","Mails":[]}
```

遙測（fire-and-forget，可忽略，mock server 回 204）：

```
GET /webservice/event/trigger?EventID=..&SSOKey=..&ApiId=..
GET /webservice/event/loading?EventNo=..&EventValue=..
POST /webservice/event/jscrambler   {"Type":"GameDebugging","GameId":696,...}
```

## 已知 gameID

從 `smallicon/Icons/` 檔名推得，共 16 個：

```
2, 9, 17, 30, 35, 38, 45, 47, 49, 51, 58, 102, 103, 106, 108, 696
```

只有 696 有完整資源（= Fortune Garuda 500，取自 `index.html` 的 `<title>`）。
遊戲名要靠擷取後從各自的 `<title>` 回填。

## 登入流程（LoginGame）

```
POST http://<api-host>/api/LoginGame
authorization: bearer <JWT>
Content-Type: application/json

{"device":1, "language":"zh-CN", "player_id":"tryplayer001usd", "game_id":"111000696"}
```

回應：

```json
{"game_url":"https://uat-wbgame.jlfafafa3.com/fg5/?ssoKey=c99e1844f8d567b581412d10dc02cee9a5b51e42&lang=zh-CN&apiId=1778&be=..."}
```

重點：

- **`game_url` 只能用一次**，開過就失效。所以自動登入比手動貼 URL 可靠得多。
- `game_id` 不等於 `gameID`：是 `111` + 六位補零的 gameID。
  `gameID 696 → game_id 111000696`。**此格式由單一樣本推得**，未經其他遊戲驗證。
- 回傳的 `game_url` 已經帶好所有反轉域名參數，不需要自己組。

### 網路需求

遊戲站要**巴西**出口 IP。Surfshark macOS 版只有 GUI（`/Applications/Surfshark.app`），
沒有 CLI 可以腳本化，要人工在 app 裡切。連上後系統層生效，
Playwright 會自動繼承，不用改 capture 腳本。

## 遊戲協定（2026-08-27 首次 capture 確認）

三層，全部走 HTTP POST + 一條保活 WS：

| 端點 | Host | 格式 | 用途 |
|------|------|------|------|
| `POST /sso-login.api` | wbwebapi (be) | form `key=<ssoKey>&lang=zh-CN` | ssoKey 換 session token（明文 JSON 回應） |
| `POST /fg5/req` | wbslot-fd (gs) | **protobuf 請求 / 加密回應** | 遊戲主迴圈 |
| `WS /lifeservice/ws2` | wbslot-fd (gs) | protobuf 握手 + JSON 心跳 | 保活，非遊戲邏輯 |

### sso-login.api 回應（明文）

```json
{"profile":{"aid":1661835,"apiId":1778,"coin":0,"betLevel":-1,"betValue":0,
            "account":"ix6tryplayer001usd...@api-1778.game","walletType":2},
 "token":"22dd0fb7fc2748e4b7bd6012a655b04880e55978",
 "response":{"error":0},
 "country":"Brazil","subDivision":"São Paulo"}
```

- `response.error=0` = 登入成功，`country=Brazil` = 伺服器確實看到 BR 出口。
- **`coin:0`** — 測試帳號餘額為 0。是否因此無法 spin 待確認。

### /fg5/req 請求（明文 protobuf，已解析）

```
08 01                              field1 = 1
12 3c  ┌ 0a "OS X"  12 "zh-CN"
       │ 1a 20 ┌ 0a "chrome" 12 "151.0.0.0" 1a "zh-CN"
       │       └ 20 1920  28 1080         ← 螢幕寬高
       └ 22 ""  2a "Macintosh"
1a 14  <token 20 bytes>                    ← sso-login 的 token（hex→raw）
22 20  <32 bytes>                          ← 疑似 client 產生的 session key
```

### /fg5/req 回應是加密的 ⚠️

95 bytes、高亂度、無 protobuf 結構。請求裡那 32 bytes 很可能是 client 每個
session 隨機產的 key。**若回應用它加密，單純錄下來重播會解不開**（key 每次不同）。
mock server 要嘛還原加密方案，要嘛讓 mock 接受 client 的 key。需要多筆
不同 spin 的 `/fg5/req` 樣本才能比對出結構——目前只有 1 筆。

### 首次 capture 觀察到的失敗（MSG 211）

遊戲畫面有載入，但只送出 1 次 `/fg5/req` 後，就進入每 ~5.6 秒一次的空
`GET /fg5/` 重試迴圈，最後跳「无法连接服务器 (MSG 211)」。可能原因（待排除）：
mitmproxy 破壞了加密 binary 通道 / 帳號 coin=0 / session key 交換沒完成。

## 登入流程（LoginGame）— 已在本地打通

```
POST https://aggregate.gamejar.cc/api/LoginGame
authorization: bearer <JWT>          （JWT 有效到 2034，存在 config.json）
origin: https://gamejar.cc            ← 要帶，API 認來源
{"device":1,"language":"zh-CN","player_id":"tryplayer001usd","game_id":"111000696"}

→ {"code":0,"message":"success","data":{"game_url":"https://uat-wbgame.../fg5/?ssoKey=..."}}
```

- **本地 `jili_login.py` 直接打就能拿 game_url，不用那個網頁。**
- `game_url` 只能用一次。
- **LoginGame 站台（gamejar.cc, Cloudflare）會擋巴西 IP** → 這支要在 VPN 關閉時跑。
  拿到 URL 後再開 VPN 擷取。（本地直打 API 繞過了網頁的 CORS/前端限制。）
- `game_id` = `111` + 六位補零 gameID。`token_path` = `data.game_url`。

## /fg5/req 協定細節（2026-08-27 no-proxy + --disable-quic 抓到 22 筆）

**抓法**：`--disable-quic` 強制走 TCP/H2（原生走 QUIC/H3，netlog 抓不到），
Everything netlog + 暖快取，不做 MITM → 遊戲能玩、又錄得到 /fg5/req 的解密後 h2 bytes。
用 `extract_fg5.py`（h2 框架 + HPACK 解析）拆出請求/回應。

### 請求 = 明文 protobuf

```
f1 varint    每筆不同（58,69,51,60,19,10...）→ 序號/nonce/動作碼
f2 bytes     選用小欄位（如 0x0800）→ 疑似押注參數
f3 bytes[20] token       整局固定（= sso-login 的 token）
f4 bytes[32] session key 整局固定，client 產生並帶上
```

init（stream 3）多帶 f2=裝置資訊(60B, "OS X"/"chrome"/"zh-CN")。

### 回應 = 加密

- 長度不定（101~327B），entropy 6.2~7.3（小樣本上限 ~6.7，符合加密）
- **用 client 帶上的 f4（32B）當 key 加密**，整局固定
- 要解密＝要 jscrambler JS 裡的加解密演算法（未逆向）

### 對 mock 的意義

- 請求可讀、可構造；**回應無法離線重播**（每局 key 不同、且加密）
- 真正離線 mock 仍卡在「逆向 f4→回應的加解密」這一關（工程量大）
- 已存 22 筆真實交換於 `games/696/fg5_exchanges.json` 供後續分析

## 回應加密 = 幾乎確定 ECDH（離線無解）2026-08-27

拿本 session 的 f4（32B）配下列全部試過，強驗證（整段完整解析成 protobuf + 22 筆全中）：
- AES-128/256 的 ECB/CBC/CTR（key=f4、f4[:16]、sha256(f4)、md5(f4)；IV=0/前綴/token/f4[16:]）
- ChaCha20（nonce 8/12，zero/前綴/token）
- RC4、循環 XOR、SM4（ECB/CBC，key=f4[:16] iv=f4[16:]）

**全部 0 命中。** 結論：
- f4 是 32 bytes、每 session 固定、client 產生、明文放在請求 field4 → 尺寸與行為完全吻合 **X25519 公鑰**。
- 回應應是 ECDH（server 臨時金鑰 × client 公鑰 → 共享祕密 → 對稱加密）。
- **解密要 client 私鑰，私鑰只在瀏覽器記憶體、從不傳出** → 光靠攔截到的封包，離線永遠解不開。

唯一出路：執行期從瀏覽器挖金鑰料（私鑰／共享祕密／或直接攔明文），
或看懂它的加解密後在 mock 重做。工具：`crack_fg5.py`、`crack_fg5b.py`（試解器，留存）。

## 待確認清單

| 項目 | 狀態 |
|------|------|
| 遊戲主協定 | ✅ HTTP POST /fg5/req（protobuf 請求/加密回應）+ 保活 WS |
| 登入 API | ✅ aggregate.gamejar.cc/api/LoginGame，本地打通 |
| 遊戲列表 API | ❌ 未知 |
| /fg5/req 回應加密方案 | ⚠️ 已知：client 帶 32B key(f4) 加密，演算法待逆向；22 筆樣本已存 |
| MSG 211/103/304 | ✅ 已解：MITM 觸發偵測(211)/token 過期作廢(103)/Everything netlog 過重(304)。no-proxy+新鮮單支token+輕量netlog 可玩 |
| 靜態資源完整性 | ✅ 696 完整（140 檔 + 134 共用），引擎能啟動 |
| Server 靜態服務 | ✅ 實測通過 |
| 面版 / 擷取流程 | ✅ 實測通過 |
| HTTPS 需求 | ✅ 已確認並實作 |

## Frida 執行期攔截（2026-08-27 進度）

**動機**：JS 注入被 jscrambler 的 JS 自我防護偵測（載入即停）。Frida 在原生層，
JS 防護看不到。且離線密碼學已證實無解（見上：無 keystream 重用、非 ECB、ECDH 換 key）。

**環境結論（本台 Mac）**：
- SIP **開著**（不動它）。Google Chrome 有 library-validation + hardened runtime → SIP 開著注入不進去。
- **Playwright 的「Google Chrome for Testing」（`~/Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64`）
  是 ad-hoc 簽章、無 library-validation（flags=0x20002）→ Frida SIP 開著也注得進去。** 版本 151 同 stable。
- **直接開**（非 CDP/Playwright 自動化）→ `navigator.webdriver=false`，jscrambler 不當自動化。
- frida 17.17 已裝在 `.venv`。

**已驗證**：`frida.attach(renderer_pid)` 成功，列出 1034 模組含 222MB
「Google Chrome for Testing Framework」（BoringSSL 靜態連結在內）。啟動要加 `--no-sandbox` 讓 renderer 可 attach。
renderer PID：`ps aux | grep chrome-mac-arm64 | grep type=renderer`。

**撞牆點**：
- Framework 符號全 strip（只 3 個 export）→ BoringSSL 的 EVP_AEAD_CTX_open / X25519 / RAND_bytes 都沒名字。
- hook 系統亂數（getentropy/CCRandomGenerateBytes/SecRandomCopyBytes/arc4random_buf）→ **WebCrypto 一次都不呼叫**，
  因為 BoringSSL 用自己的 CTR-DRBG（啟動 seed 一次後內部生成）。所以私鑰抓不到、系統層 hook 無效。
- 還不知道遊戲用 WebCrypto（→BoringSSL）還是純 JS（→V8），兩者 hook 目標不同。

**下一步（未做，專家級）**：
1. 記憶體特徵掃描定位 BoringSSL 加密函式：ChaCha20 常數 `expand 32-byte k`
   (65 78 70 61 6e 64 20 33 32 2d 62 79 74 65 20 6b)、AES sbox、curve25519 基點，找到後 hook。
2. 或找 EVP_AEAD_CTX_open 的指令 signature（版本相依）。
3. hook 到後跑真遊戲（CfT --no-sandbox + 新鮮 token + VPN），dump AEAD open 的 (key,nonce,plaintext)。
工具：`hook.js`(JS版，已被偵測不用)、Frida 探針在 scratchpad。

## Frida 深入結果（2026-08-27，撞專家牆）

**已達成**：
- Chrome for Testing 直開 → 遊戲能正常進畫面（非 CDP，jscrambler 不擋）。
- `frida.attach(renderer)` 成功；`Memory.scanSync` 在 framework 找到 BoringSSL 常數：
  ChaCha `expand 32-byte k`、AES sbox、Poly1305 clamp（固定 offset 0xc15f460 等，所有 renderer 相同）。

**決定性方法（正確但卡在定位）**：
  hook BoringSSL `EVP_AEAD_CTX_open`，dump 每次 (key, nonce, in, out)，
  用已知的 /fg5/req 密文（fg5_exchanges.json）比對過濾掉 TLS 雜訊 →
  比對中的那筆 output 就是明文、key 就是 ECDH 導出的對稱金鑰。

**卡點（專家牆）**：
- framework 符號全 strip；BoringSSL 常數只證明「lib 存在」，且 TLS 也用它 → 常數存取無法分辨 app vs TLS。
- 定位 `EVP_AEAD_CTX_open` 函式入口需反組譯 ADRP+ADD cross-ref / 函式 prologue，
  Frida 裡手刻 arm64 解碼不切實際。正解：離線用 Ghidra/IDA + BoringSSL signature 定位函式 offset，
  再回 Frida 用該 offset 下 Interceptor + 密文比對。這是獨立的離線 RE 工程。

**結論**：所有「不需離線反組譯」的招都已試盡。要破 /fg5/req 加密，
只剩「離線反組譯 framework 定位 AEAD 函式」這一條，屬專業級、以天計、不保證成功。

## 全案最終狀態
- ✅ 站台架構、URL 反轉、三後端、協定（sso-login → /fg5/req protobuf → 保活 WS）全逆向
- ✅ 本地產 token（jili_login.py，繞過網頁）、能玩配方（CfT/stable + 新鮮單支 token + no-proxy/--disable-quic）
- ✅ 靜態資源完整、22 筆 /fg5/req 樣本、確認回應 ECDH 加密
- ✅ Frida 可行性驗證（可 attach，jscrambler 看不到）
- ❌ /fg5/req 回應解密：離線數學不可能；執行期需離線反組譯定位 AEAD 函式（未完成）

## Frida hook 實作結果（2026-08-27，收斂到精準牆）

用常數 ADRP+ADD cross-ref 定位到 BoringSSL scalar ChaCha20（module+0x3b16200，
反組譯確認 x0=out,x1=in,x2=len,x3=key[32],x4=nonce）。Frida hook 成功掛上 4 個 renderer。
**但 spin 時 0 命中**（連 TLS 都沒觸發它）。

全 renderer rw- heap 掃 sigma 常數 = 0 → **排除純 JS tweetnacl/Salsa/ChaCha**。

**精準結論**：arm64 上 BoringSSL 用**硬體加密指令**（AESE/AESD/PMULL 做 AES-GCM、NEON 做 ChaCha），
這些函式**不引用 sbox/sigma 常數表**（那些是 x86 軟體 fallback 死碼）。
→ 「常數反查」在 arm64 定位不到實際在跑的加密函式。

**唯一可行的 hook 目標**：`EVP_AEAD_CTX_open`（cipher/硬體無關的 dispatch 層），
但它不錨定任何常數，定位需**離線 Ghidra/IDA 對 framework 做 call-graph / signature 分析**，
不是常數掃描或互動式 session 能完成。hook 到後用「輸出開頭是否 protobuf」濾掉 TLS 即可分離 app 解密。

工具留存：frida_scan.py、frida_chacha.py、scratchpad 的 xref.py/procscan*.py。
ChaCha scalar 函式 offset 0x3b16200 已知（未來若要試 NEON 變體從 0xc72a850 refs 找）。

## 定論：/fg5/req 加密是自訂純 JS cipher（非原生）2026-08-27

系統性 Frida 原生 hook（Chrome for Testing renderer）全部排除：
- WebCrypto scalar ChaCha20 (module+0x3b16200)：spin 時 **0 次呼叫**
- WebCrypto 融合 AES-GCM kernel (module+0x1c3c130, aes_gcm_dec_kernel)：**0 次呼叫**（連 TLS 都無——TLS 在網路服務行程，非 renderer）
- AES-CTR aes_hw_ctr32 (module+0xd4800)：74 次，但全是**分散位址單塊**（in==out 原地、輸出隨機）
  → 是 Cocos 資產解密，**非 /fg5/req**（那會是連續緩衝區、輸出 protobuf）
- renderer heap 掃標準 cipher 查表（AES sbox/Te0/Td0、SM4 sbox/CK、ChaCha sigma）：**全 0**

**結論**：/fg5/req 回應解密**不使用任何標準 BoringSSL 原生加密**，是 jscrambler 混淆 JS 裡的
**自訂/混淆 cipher**（查表被打散所以 heap 掃不到）。這解釋了：原生 hook 無效（加密不在原生層）、
JS hook 被偵測（jscrambler 自我防護）。**Frida 原生路線到此確定無效。**

唯一理論殘路：反混淆整個 jscrambler bundle 找出自訂 cipher 實作——數週專家工、極不確定，ROI 已無意義。
工具全留存（frida_scan/chacha/aesgcm + scratchpad 的 xref/procscan/aesrecon）。

## 反混淆嘗試結果（2026-08-27，同事 AST 工具鏈全試）

目標：反混淆 main bundle 抽出自訂 cipher / 字串表。工具都在 deobf/。
- synchrony（deobfuscator）：跑完但 `StringDecoder arrays=0` → jscrambler 非 obfuscator.io 標準字串陣列，零進展。
- webcrack：依賴 isolated-vm 原生編譯，node v26 gyp 失敗，無法安裝。
- Node VM 沙盒 + Proxy 攔解碼器（hybrid）：bundle 缺瀏覽器 API 早崩（.random/.bind whack-a-mole），
  P_feQ 字串表（5 表：192870/57123/168145/534367/ВА，各有解碼器 К0_lGMο/m$lO6Ya/a3αnove/v6ΟsvН$/Q8UХv5Q）
  在崩潰前未被填充，捕捉 0 字串。
- jsdom 全模擬：P_feQ 作用域脫出（"P_feQ is not defined"）+ jsdom EventTarget 內部崩潰，game engine 撐不住。

**根因**：字串解碼表初始化深度耦合完整瀏覽器 + Cocos engine 環境；離線缺 API 崩 / 觸發反沙盒。
要突破＝手工補完整環境 + 逐一還原變形邏輯，數週專家工，且多型保護（重 build 全作廢）。**ROI 歸零，收手。**

## === 全案結案 ===
攻不下的只有 /fg5/req 回應解密（ECDH + 自訂混淆 JS cipher + jscrambler 自保，專業級防護）。
其餘全部到手：擷取 pipeline / 面版 / 本地產 token / 能玩配方 / 協定全逆向 / 22 筆樣本 / ECDH 判定 /
完整 RE 工具（Frida + AST）與每步結論。方法論對「做別款」完全可複用。
