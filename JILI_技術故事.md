# 破解 JILI：一場從「以為破不了」到「純網頁跑通」的技術長征

> 這份不是規格書，是**故事**。
> 記錄我們（使用者 dyson + Claude）從 2026-08-27 到 09-02，怎麼一路撞牆、被自己的誤判帶偏、又被使用者的一句話撬開缺口，最後把一個防護專業級的老虎機遊戲，從「加密破不了」做到「開瀏覽器就連自建 mock、直接能玩」。
>
> 中間有兩次「以為結束了」：第一次以為只能擷取數據、做不出真 mock；第二次以為只剩 Frida 陪跑這條非永久的路。結果兩次都又往前捅破了一層。
>
> 目標遊戲：JILI gameID 696「Fortune Garuda 500」，端點 `/fg5/req`。

---

## 序：敵人是誰

我們要做的事很單純：一台**自建的 mock server**，讓 JILI 原封不動的前端連上來、以為在跟真伺服器講話，這樣就能逐款擷取、還原、甚至自己出結果。

但 JILI 這站的防護是**專業級**的，光是站在門口就吃了一輪閉門羹：

- **Playwright / CDP 一律不能用**——防護會偵測自動化瀏覽器，然後**靜默中止**遊戲載入。你不會看到錯誤，遊戲就是永遠卡在 loading。最後靠 `mitmproxy + 真實 Chrome` 才騙得過（網路層攔截、沒有 CDP 痕跡）。
- **存取條件苛刻**：遊戲站只收巴西出口 IP（要 VPN），`game_url` **開過一次就失效**（得靠 LoginGame API 現產現用），而且產 token 的站台會**擋巴西 IP**——於是「拿 token」要關 VPN、「開遊戲」要開 VPN，光是把這條管線接通就是一場硬仗。

這些只是門票。真正的敵人在裡面。

---

## 第一幕：搞清楚「我到底在找什麼」

一開始最大的障礙不是技術，是**觀念混亂**。使用者問了一句很關鍵的話：

> 「私鑰說在記憶體，又說加密在 bundle 裡，到底專攻哪裡？我在找那把 key 嗎？」

這一問逼出了整個專案的地基。任何加密都是這個式子：

```
密文 = 演算法(明文, 金鑰)
```

**兩個零件是分開放的：**

| 零件 | 放在哪 | 我們手上有沒有 |
|---|---|---|
| 演算法（cipher 的程式碼） | 混淆過的 JS bundle 裡 | 有，但被包死 |
| 金鑰（key material） | runtime 才生、只在記憶體 | 沒有 |

在此之前，兩條攻擊線一直在打**兩個不同的零件**卻混為一談：「離線窮舉全滅」是因為**缺 key**，不是演算法神秘；「反混淆撞牆」是想挖**演算法**，被 jscrambler 擋。

更關鍵的一次認知修正：如果它走的是 **ECDH**（後來證實了），那「那把 key」**根本不存在於 bundle**——

```
client 開臨時金鑰對 (priv, pub)      ← priv 只在記憶體；pub 就是明文送出的 f4
shared_secret = ECDH(client_priv, server_pub)   ← 這才是真正加解密的 key
```

所以 `f4`（那 32 bytes）**是公鑰、不是金鑰**。之前在 bundle 裡 grep 32-byte 常數想找靜態 key，註定白費——**根本沒有靜態 key**。

> **教訓一**：動手前先分清楚你缺的是「演算法」還是「金鑰」。這兩件事的攻法完全不同，混在一起會白繞好幾天。

---

## 第二幕：五條路，五道牆

搞清楚方向後，我們把所有「免反組譯」的招數一條條試過去。**五條路，五道牆**，而且每一道牆都親手撞過、確認死因，不是道聽塗說。

### 路 A：離線暴力破解密文
拿擷取到的密文，離線試 AES / ChaCha20 / RC4 / XOR / SM4 配 f4 的各種衍生，加上強驗證（整段要能解析成 protobuf）。
**全滅。** 因為缺金鑰（見第一幕）。這不是演算法神秘，是零件缺一個。

### 路 B：靜態反混淆，從 bundle 挖演算法
想直接讀混淆 JS 裡的 cipher。撞上 **jscrambler** 的完整手法：
- 連 `XMLHttpRequest`、`crypto`、`subtle` 這些 **API 名字都被藏進「解碼表」**，執行期才現解 → 靜態 grep 全 0 命中。（這也解釋了為什麼 hook `crypto.subtle` 會被抓：名字要現解，jscrambler 一併校驗。）
- 字串解碼器是「執行期建表 + 自我參照」，離線把它抽出來單獨跑會**無限迴圈 / OOM**——我們用了新招（真 Function scope 讓 hoisted 宣告成真物件 + `with(proxy)` 兜住裸全域）繞過前人卡住的點，結果**用不同路徑複現了同一道牆**：dispatch 迴圈的退出條件依賴「已正確解碼的字串比對」，而正確解碼又需要真實環境 → dummy proxy 讓它永遠達不到退出。

### 路 C：原生層 hook crypto（Frida）
想法很正：不管 JS 怎麼混淆，最後解密一定會呼叫瀏覽器底層 BoringSSL 的 `EVP_AEAD_CTX_open`，在原生層攔就能拿明文，jscrambler 在 JS 層看不到 Frida。
**撞牆，死因確認：**
- Frida 找到的 `EVP_AEAD_CTX_open` 位址在 `0x1d...`，那是**系統 dyld cache 的 libboringssl**，遊戲根本不呼叫它。
- Chrome 自己那份 BoringSSL 是**靜態編譯進 framework、符號全 strip**，只剩 3 個 export。
- 想用「常數指紋」定位（cipher 通常有特徵常數表）也不行——**arm64 用硬體加密指令（AESE / PMULL / NEON），根本不碰那些常數表**。

### 路 D：JS 層注入 hook（改 hook 原生 `XMLHttpRequest`，不碰 `crypto.subtle`）
想在遊戲讀網路回應那一刻攔下、印出呼叫堆疊。這是最戲劇性的一條——在 console 貼 hook，報錯：
```
typeof XMLHttpRequest        → undefined
typeof Array.prototype.forEach → Array is not defined
```
也就是說，**遊戲啟動時先把 `Array`、`XMLHttpRequest`、`window.frames` 這些最核心的全域各偷藏一份私有的，然後把全域刪光**。它自己用私有那份跑，任何事後想靠全域 hook 的 JS 全部陣亡。這叫**焦土反 tamper（scorched-earth anti-tamper）**。

### 路 E：DevTools 原生斷點
既然 JS 全域被毀，那用瀏覽器**原生**的 XHR 中斷點總行了吧——它在 jscrambler 投毒層「底下」。
**撞牆：** 一設中斷點、遊戲一被暫停，就噴一堆 `p.apply is not a function`、遊戲直接崩。原因是那個混淆 bundle 靠「執行期一個迴圈不斷解碼字串」在跑，**對時序極度敏感，一被 breakpoint 打斷，解碼狀態就錯亂、連鎖自毀**。

> 這裡埋下一個貫穿全篇的伏筆：**這遊戲只要「執行被打斷」——不管是 JS hook 還是 pause——就自毀。而且，一開 DevTools 本身就會觸發 jscrambler 反除錯，把 `index.22de5.js` 弄壞。** 這條「DevTools 是毒」的教訓，後面害我們吃了大虧。

### 路 F：被動讀 heap（唯一沒踩雷的）
前面五條不是被偵測、就是自毀。只有「**被動讀記憶體**」——不 hook、不暫停——遊戲偵測不到。這條能走，但一開始也連踩三個坑：

1. **掃餘額全找不到**：拿畫面餘額去 heap 搜各種編碼全 0。後來發現使用者**多念了一位**（999971.532 → 其實是 999971.53），用對的值一搜，餘額確實以 `double` 存在。
2. **原始明文活不過 1.4 秒**：解密出的原始 protobuf 一解析成物件就沒人用了，**下一次 V8 GC（不到 1.4 秒）就被回收/搬移**。連拍 40 秒 35 張 heap，沒有一張抓到原始回應——它活不過一個 GC 週期。
3. **連餘額都不在回應裡**：更致命，回應**根本不帶絕對餘額**（伺服器只回「這把贏多少」，餘額是 client 自己算 `舊−注+贏`）。拿餘額當錨點，再怎麼追都追不到原始回應。

到這裡，我們寫下了一句聽起來像投降的結論：*所有免反組譯的招都試盡了，ROI 已建議收手。* 但實際上——真正的突破就在下一句話。

---

## 轉折一：使用者說「用單號查」

這是整場的第一個關鍵轉折，而且是**使用者提的**。他說：不要拿餘額，用**單號**（那串 `23932-989600-00770696`）當錨點。

這個想法比餘額好太多：

1. 是**字串** → 沒有「double 還是整數、乘幾倍」的編碼歧義。
2. 每次 spin **亂跳** → 一定是伺服器在回應裡發下來的（client 生不出來）。
3. 會**顯示在畫面** → 代表遊戲**留著它**，不像原始 protobuf 那樣被秒回收。
4. 格式**獨特** → 幾乎不會誤判。

一搜，撞到了一個意料之外的東西——

### 大發現：遊戲自己把解密回應快取成 JSON

順著單號在 heap 附近找，撞到這個：
```json
{"type":0,"ret":0,"error_msg":"","data":[10,158,1,10,5,...,105,236,81,184,...]}
```

**遊戲自己把每一筆「解密後」的回應，存成 JSON 快取在 heap 裡**，那個 `data` 陣列**就是解密後的原始 protobuf 位元組**。

這等於遊戲**把自己解好的答案抄在旁邊給我們看**，完全繞過加密：
- 不用破 crypto。
- 不用跟 1.4 秒的 GC 賽跑（這份 JSON 快取是**持久**的）。
- 只要搜 `{"type":` 就全抓到。

把 `data` 當 protobuf 一解，欄位跟畫面上的值**全部對上**：餘額、總中獎、單號、下注、三條中獎線、盤面符號⋯⋯（單號當初搜「字串」失敗，是因為它在 protobuf 裡其實是 **varint 數字**，顯示時才加 `-`。使用者念的數字是對的，只是儲存型別跟我猜的不一樣。）

### 請求端：又一句話點破

回應解完了，但 mock 還缺一半——它得看得懂 client 送進來的 spin 請求。先想從 heap 撈請求，只找到「設定類」訊息，**spin 請求本身撈不到**。使用者這時做了一個乾淨的實驗，並提示：

> 「把下注改成 100，但**不要 spin**，你再 dump 對照看看。」

結果：**沒有任何新請求出現**。這一下就證明了——**改注是純 client 動作、不送伺服器**；下注額和額外下注是**跟著 spin 那一刻一起送**的，而 spin 請求跟原始明文回應一樣是瞬時的，heap 留不住。

解法轉去 **netlog**（Chrome 內建的線路記錄，含 request body）：玩、設注、開額外下注、spin，然後**關掉 Chrome 視窗**（netlog 要視窗關閉才寫完整），離線解出明文請求。請求端也對上了：`f2.f1 = 下注額`、`f2.f26 = 額外下注`，跟回應 `f23.f26` 完全鏡射，而且**每把 spin 都自帶下注資訊，mock 不用維護 session 狀態**。

> **教訓二**：**攻「它不得不留下/送出的東西」，而不是「它努力藏的東西」。** 加密破不了、hook 全自毀，但遊戲**必須把回應解密來用**——解密後那份就在記憶體，它甚至自己快取成 JSON。
>
> **教訓三**：**具體錨點 >>> 盲目掃描。** 餘額（會格式化、還可能不在回應裡）害我繞很久；使用者用「單號」這種伺服器發的、獨特的、遊戲會留著的值，一下就逼出答案。

### 第一次「以為結束了」

到這裡，我們有了完整協定的**內容**：回應 schema、請求 schema、行為覆蓋、原始資料、工具鏈。逐款擷取的目標達成了。

但這裡有個**天花板**寫得很誠實：這是「擷取解密後的回應內容」，**它不解開 crypto**。所以做得出「還原數據」，**做不出「讓真 JILI client 直接連的 mock」**——因為 mock 沒辦法產出前端解得開的密文。

當時甚至評估過「複製 crypto 讓真前端連 mock」（Path A），試了三種朋友建議的標準快試法（tag 驗證爆破、keystream 爆破、f4 錨定爆破），**全空**，結論是「Path A 不划算，別再 grind」。

**看起來這就是終點了。** 結果不是。

---

## 轉折二：crypto 根本不在 JS 裡——它是 Rust WASM

就在「靜態分析定論」來回反覆的過程中（一度誤判成 WebCrypto、又用「全檔幾乎沒有 async/Promise」推翻 WebCrypto、再繞到自訂 JS cipher⋯⋯），一個**決定性突破**出現了：

從 heap dump 裡抽出一個 **wasm-bindgen（Rust 編譯）的 WASM 模組**。它的 data section 裡的 Rust crate 路徑，直接把整套 crypto **明明白白寫在那裡**：

- **金鑰交換 = X25519 ECDH**（`curve25519-dalek 4.1.3`，字串 "Cannot decompress Edwards point"）→ 昨天的 ECDH 推論**正確**。
- **AEAD = AES-256-GCM**（`aes-gcm 0.10.3` + GHASH）。
- **訊息 = protobuf 3.7.2**，回 JS 用 `serde-wasm-bindgen`（= heap 那個 JSON 的來源）。
- exports：`login / send / start`；imports 含 `fetch`（**WASM 自己發 `/fg5/req`**）、`getRandomValues`。

這**一舉推翻了先前所有判斷**——crypto 不在混淆的 `index.22de5.js`、不是 WebCrypto、不是自訂 JS cipher。**它全在這個 Rust WASM 裡。** 這也解釋了為什麼之前所有「在 JS heap 撈 raw 32B 金鑰」全空：金鑰在 **WASM 的線性記憶體**裡，不在 JS heap。

> **教訓四**：**別把自己的推論當結論。** 這段路上我們一度斷言 WebCrypto、又斷言自訂 JS cipher，都錯。真相是「用不同工具（heap dump 抽 WASM）看，而不是在同一個死角裡愈鑽愈深」才挖出來的。標準庫（X25519 + AES-256-GCM）反而是好消息——**標準的東西可以離線重建**。

---

## 第三幕：離線 harness——把整個協定完全破解

既然 crypto 是標準庫、而且整包 WASM 就在手上，我們做了一件關鍵的事：**在 Node 裡蓋一個離線的「真 WASM oracle」（`harness_run2.js`）**，忠實重建 wasm-bindgen 的 runtime（heap、closure、Promise、fetch/Response、getRandomValues），讓這顆真 WASM 在**完全離線、不開遊戲**的情況下跑 `login()` + `send()`。

這顆 harness 成了**唯一的驗證器**——我可以餵任意一個候選回應進去，看真 WASM 吐出什麼錯誤碼，從而反推它到底在檢查什麼。靠它，協定被一根一根釘死：

- **RNG = OsRng 直用**，`getRandomValues` 首次 32B 就是 client 的 ephemeral 私鑰。固定 RNG → 私鑰、client_pub(f4) 都能複現並用 scalarmult 驗證通過。
- **server_pub 是 WASM 內建常數**（不是握手下發的），而且用 **XOR 0xAA 混淆**藏在四段常數裡。抽出來 = `26aa760e…da17`。
- **shared = X25519(client_priv, 內建server_pub)**，而且這把 shared 在 WASM 記憶體 `@1108480` **實地找到**（count=1）→ 證明模型與抽取都正確。

過程中還發現回應**不是**裸的 `nonce‖ct‖tag`，而是前面有個 **64-byte header**。餵各種候選進 harness，看錯誤碼從 `1301`（總長不足）→ `1304`（header 驗證失敗）→ `1307`（AEAD 解密失敗）怎麼跳，就能精確定位「卡在哪一關」。最後確認那 64 bytes 是 **Ed25519 簽章**。

**完整協定（100% 破解）：**
```
回應 = Ed25519_sig(server_ed_priv, M)[64]  ‖  nonce[12]  ‖  AES-256-GCM(key, nonce, 明文)[ct‖tag]
       其中 M = nonce ‖ ct
       key = X25519(client_ephemeral_priv, 內建 server_X25519_pub)   ← 直用，無 KDF
       AAD = 空
```

harness 端到端驗證成功：把 harness 內建的兩把 pub patch 成我們自己的 keypair，餵一個用我們私鑰簽 + 加密的 mock 回應進去 → **真 WASM 驗章、解密、解析全過，resolve 出 `{type:0,ret:0,…}`。**

> ⚠️ 這裡還抓到一個陰險的 bug：一開始以為明文欄位是 `{f1=type, f2=ret, …}`，因為只用全零的測試回應測、每個欄位都落在**預設值**，剛好 resolve 成空物件而沒露餡。用真 spin（type0 + 183B）逐欄探測才發現正確欄位號是 `f3=type, f5=data, f6=error_msg, f7=ret`。**用錯欄位號會讓每個真實 payload 靜默變空。**

---

## 第四幕：Route X——「能解」不等於「能假冒」

破解完，出現一個必須講清楚的**不對稱**（Model C）：

- **解密**真伺服器的回應，只需要 `X25519(client 臨時私鑰, server 公鑰)`——兩者都拿得到（私鑰從 heap 撈、公鑰是內建常數）。**所以我們能解封包。**
- **假冒**伺服器發回應，需要 **server 私鑰**（簽章 + ECDH）。**在真站上，永遠拿不到。**

所以 mock 只能用**自己的 keypair** 簽/加密，然後——**必須讓遊戲的 WASM 改用我們的公鑰**來驗章、來導 shared key。這就是那道最後的牆：**把 WASM 記憶體裡那 8 個「內建 server 公鑰 chunk」覆寫成我們的公鑰。**

我們把 mock server（`routex/`）整個做出來了，能讓真前端載入、走完 `/fg5/req` 握手。過程中還修掉兩隻攔路虎：
- **MSG 999.1**：除了 `/fg5/req`，還有一條 `wss://…/lifeservice/ws2` 保活 WebSocket，mock 原本只有 HTTP、upgrade 一路 404。補上純標準庫 WS 後，999.1 → 999.2。
- **config 格式**：握手要一份 type 1 config（貨幣、餘額、bet 選單、限額），加上外層必帶的 `f1 = 伺服器毫秒時間戳`（缺了遊戲會重握手）。

但最後就是卡在 **MSG 999.2**：遊戲 WASM 內建**真** server 公鑰，會**拒絕** mock 用「自己 keypair」簽的回應 → 遊戲一直重握手 → 逾時。

要破這關 = 覆寫那 8 個內建公鑰 chunk。三條路試下來：

| 路 | 結果 |
|---|---|
| 靜態換 `crypto.wasm` 檔 | ✗ 遊戲根本不發 `.wasm` 請求 |
| 靜態改 bundle 裡的 wasm | ✗ wasm 是 JS **自訂編碼**執行期解出的，**不在任何送出的檔案裡**（含 zip/XOR 徹底搜過） |
| JS shim hook `WebAssembly.instantiate` | ✗ **Jscrambler 反竄改偵測到 → 弄壞 `index.22de5.js` → 卡 loading** |
| **Frida 改記憶體公鑰** | ◐ **唯一還能動的** |

---

## 「以為結束了」：只剩 Frida，而且非永久

於是我們走上 Frida 這條**唯一活路**。環境本身就是一連串陷阱，全踩過才通：

- 一般的 `/Applications/Google Chrome`（hardened runtime 簽章）**連 root 都 attach 不上**（`PermissionDeniedError`）。必須用 **Chrome for Testing（CfT）+ `--no-sandbox`**。
- **即時** Frida `readByteArray` 讀 WASM 小窗會失敗；但**整段 range 讀成檔、離線讀**完全 OK——這是撈私鑰當初能成功的關鍵（dump 成 1.3GB 檔 → 離線以 f4 為錨搜到臨時私鑰 → 解全部 38 筆、簽章全效）。
- **別開 DevTools**（會觸發 Jscrambler 反除錯），診斷只能靠 `beacon → mock log`。

然後撞上一個以為是死結的東西：**pub-patch 搶時序搶不過。**

`patchwasm.py` 明明把 8 個 chunk 覆寫成 mock pub 了（bytes 確認在位），但遊戲導出的 X25519 shared（讀 `@1108480`）**從來沒等於** mock 該有的 shared——`SSO_DELAY` 從 5 拉到 12 都沒翻。用一個「shared oracle」（每輪印遊戲導出的 shared、跟 mock 期望的比對）**證死了這條路**：遊戲要嘛在實例化當下就導完 shared（早於我們能 patch fresh 實例），要嘛 X25519 讀的是另一份 pub 副本。**靠時序搶 pub，贏不了。**

### 突破：不搶 pub，改覆寫 shared

轉念——**繞開 X25519**。讓遊戲照樣導它那把「錯的」shared 寫進 `@1108480`；我們在 mock 端算出**正確**的 shared（`X25519(mock_priv, client_pub)`，數學上恆等於遊戲該有的 AES key），**趁回應停頓的空檔，直接把 `@1108480` 覆寫成正確值**，遊戲 decrypt 當下即時讀到對的 key。（Ed25519 那 8 chunk 的 pub-patch 仍要留，因為驗章每次重讀內建 pub，這步不吃時序。）

跑通了。**真實遊戲端到端：handshake 被接受 → `init[1..15]` 整條初始化序列被消化 → 餘額出現 → 素材開始載 → 不再 999.2。**

這是巨大的一步——但它有個**先天缺陷**：整套**非永久**。Frida 得全程陪跑，關掉 patcher / mock 就失效，每次開遊戲都要重來一遍「先讓遊戲 settle 到 999.2 → 再起 patchwasm → Cmd-R」。

**這一度就是我們認定的終點：協定全解、真遊戲能跑，但代價是外掛陪跑。** 交接文件都寫好了，一句話總結是「唯一活路 = Frida 記憶體 patch（非永久）」。

---

## 「結果又突破了」：純網頁版——真兇根本不是 hook

09-02 這場的目標很明確：**把 Frida 拿掉，做成純 server 端、開瀏覽器就生效的版本。** 而這一場，幾乎全靠**使用者的幾句話**一次次把方向撬開。

### 先繞了一大圈冤枉路

核心誤區：我一直以為死因是「我動了 `WebAssembly` / `Function.prototype.toString`」，於是拼命做**原生性偽裝**——per-function toString 偽裝、全域接管 toString + WeakMap、把 prototype/name/length 全對齊原生⋯⋯每一版都死在 `index.22de5.js`，而我每次都**把帳算錯**，歸因給最可疑的那樣東西，然後下一版再改別的地方。

我甚至一度自傷：hook `WebAssembly.Module` 時忘了複製 `Module.imports` 這個**靜態方法**（SystemJS 要用），把引擎自己的 wasm 弄死了，還誤判成「7dcc1 在盯 Module」。

### 使用者的關鍵提示（真正推進的，是這幾句）

**① 「Frida 都 patch 得掉、本地能跑，表示這塊沒被校驗，網頁 patch 理論上也行；而且收/解封包都過 wasm，表示它有跟 JS 溝通、有傳 reference。」**
→ 確立「純網頁理論上可行」，並點出「只要拿到 instance 就能讀寫 `exports.memory`」。

**② 「他把 wasm 轉二進位再 Jscrambler 包；檢查的應該是 `WebAssembly.instantiate/Instance` 存不存在。」**
→ 促成我去測**沒測過的 API**（`compile` / `compileStreaming`）。這條雖然當場死（還自傷了 Module.imports），但逼我去 heap 逆向那條 wasm 載入鏈。

**③ 「怎麼可能 Jscrambler 比 index.html 早？在外面包住轉發不就行？」**
→ 打掉我「搶第一就隱形」的錯誤心智模型。正解是：**搶第一只讓你先動手，但改動留在 DOM/HTML 是持久證據，晚跑的稽查照樣看得到。** 這句話其實已經指向「載體」問題。

**④ 「那他到底檢查什麼？我們不是有 dump 記憶體，可以離線查嗎？」**
→ 促成 **heap 逆向**，撈出兩個關鍵事實：
  - heap 裡讀得到的那個 `toString.call(x) + "{ [native code] }"` 檢查，其實是 **Google Tag Manager 的遙測**（只回報、不弄壞遊戲）——**紅鯡魚**！真兇（Jscrambler）是混淆碼，不以可讀字串躺在 heap。
  - **真實的 wasm 載入鏈**（SystemJS plugin，可讀）：`compileStreaming(resp)` → `Module.imports(module)`（靜態）→ `instantiate(module, imports)`。這直接告訴我「該 hook `compile`」以及「別碰 `Module` 靜態方法」。

**⑤ ★決勝的一句★（在我做的 inert 對照組——連自我 `removeChild` 都試了還是死之後）：**
> **「他到底怎麼識別的？不可能啊，一直會有載他的載體，他怎麼切得乾淨的呢？」**

這句話點破全局。我因此把整份 `index.html` 讀完（確認**沒有 SRI、沒有 hash、沒有 nonce**），然後猛然意識到：

### 真兇：不是 hook，是「多了一個注入的 `<script>` 元素」

我用 bisection（二分對照）證了出來——做**惰性對照組**：注入一個**純註解、什麼都不做、甚至注入後立刻自我移除**的 `<script>`：

| 對照組 | 做的事 | 結果 |
|---|---|---|
| baseline | 完全不注入 | **活到 `/fg5/req`** |
| A2 | 只發 1 個 beacon，其餘全不做 | 死 22de5 |
| A3 | 純註解 `<script>`，不執行、不發 beacon | 死 22de5 |
| A4 | 注入後**立刻 `removeChild` 自我移除** | 還是死 22de5 |

**差別只在那個多出來的 `<script>` 元素。** 自我移除沒用——它比對的是**載入當下 / 重抓的 HTML**，不是 22de5 當下掃 DOM。

換句話說：**之前 v3/v4/v6 的 WebAssembly hook、換 FPT、toString 偽裝，全都沒被抓——它們是被「注入 script」這個載體連累了。** 我苦練了好幾天的原生性偽裝，全是在對付一個根本不存在的敵人。

### 正解：不加元素，改一個它本來就會載的檔

破法就是使用者一直在指的方向——**用現有載體**：不加任何新 `<script>`，而是改一個遊戲本來就會載入的 bundle 的**內容**。

選 `polyfills.bundle`：**最早載入、無 SRI、不是 Jscrambler 保護的**遊戲檔。把 wasm-patch shim **prepend 進它的內容**，**HTML 一字不改、DOM/script 結構完全不變**。手法是 hook `WebAssembly.compile` / `compileStreaming`，在**編譯前**的 bytes 裡 find&replace 那 8 個 pub chunk。

**兩跑定案：**
- **C1**（把惰性 beacon prepend 進 polyfills）→ 一路衝到 `/fg5/req` 999.2，跟 baseline 一樣 → **證明改現有 bundle 內容不被抓。**
- **C2**（把完整 compile-hook byte-patch prepend 進去）→ **`init[…]` 整條消化、無 999.2 → 可以玩。**

而且這個做法比 Frida **更乾淨**：pub 在**編譯前**就換成 mock pub → 編出來的 module 天生內建 mock pub → 遊戲自己導的 X25519 shared **天生就是對的 AES key**，Ed25519 驗簽也一起過。**免 Frida、免 CfT、免時序賽跑、免覆寫 shared。**

```bash
cd routex
sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 ../.venv/bin/python3 server.py
# 開遊戲（任何 Chrome 皆可，不用 Frida、不用 CfT、別開 DevTools）
# mock log 看到 compile d=8（crypto 被 patch）+ init[...] = 通了
```

**Frida 正式退役。**

---

## 尾聲：可以帶走的教訓

1. **先分清楚缺的是「演算法」還是「金鑰」**——攻法完全不同，混在一起白繞好幾天。
2. **攻「它不得不留下/送出的東西」，別攻「它努力藏的東西」**——加密破不了，但遊戲必須把回應解密來用，那份就在記憶體、甚至被它自己快取成 JSON。
3. **具體錨點 >>> 盲目掃描**——一個「伺服器發的、獨特的、會被留著的值」（單號），勝過一整套熵過濾爆破。
4. **別把推論當結論**——ECDH、WebCrypto、自訂 JS cipher⋯⋯我斷言過好幾次都錯；換工具（heap 抽 WASM）看，才挖出「crypto 是 Rust WASM」。
5. **做乾淨的對照組**——我最大的浪費來自「一版改好幾樣、死了亂歸因」。惰性對照組（A2/A3/A4）一出，真兇立刻現形。
6. **「搶第一」不等於「隱形」**——你先執行，但你留下的痕跡（多的 `<script>`、被換的 global）是持久證據，晚跑的稽查回頭一看就發現。要嘛不留痕跡，要嘛用它本來就有的東西。
7. **反竄改的第一道牆，常常是「注入本身」，不是你注入的內容**——與其苦練原生性偽裝去騙檢查，不如根本不新增元素，改現有、無 SRI、非保護的載體。
8. **在編譯前改 bytes > 在記憶體改**——byte-patch 讓 shared「天生就對」，省掉整個時序賽跑。
9. **DevTools 是毒**——Jscrambler 反除錯一開就弄壞 bundle，而且跟其他死法長得一模一樣，害我第一次就誤判。診斷改用 beacon。

---

### 一句話總結這趟長征

> JILI 的防護是專業級的：焦土反 tamper、Jscrambler 自毀、crypto 藏進 Rust WASM、內建公鑰讓你「能解卻不能假冒」。我們兩次以為到頂了——第一次以為只能擷取數據，結果從 heap 抽出 WASM、離線把協定完全破解；第二次以為只剩 Frida 陪跑，結果被使用者一句「載體怎麼切乾淨」點破，發現真兇不是 hook 而是「多注入的那個 `<script>`」，改成 prepend 進現有 bundle，做出了**開瀏覽器就能玩的純網頁版**。
>
> **每一次往前捅破一層，靠的都不是更用力地鑽同一個死角，而是使用者一句話換一個視角。**

---

*相關文件：`PROTOCOL_SOLVED.md`（crypto 規格）、`PROGRESS_0831.md`（Frida 階段交接）、`WEBSHIM_JOURNEY_0902.md`（純網頁版詳細歷程）、`games/696/GAME_FORMAT_SPEC.md`（應用層格式）。*
