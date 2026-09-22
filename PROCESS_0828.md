# JILI 逆向全過程 — 2026-08-28

> 這份記錄 8/28 這場從「破加密」一路撞牆、到最後靠**單號當錨點**繞過整個加密的完整過程。
> 盡量把技術名詞解釋清楚，看不懂的地方標了【解釋】，可以直接問。
> 目標遊戲：gameID 696「Fortune Garuda 500」。

---

## 0. 我們到底要什麼

要做 JILI 老虎機的 **mock server**（逐款擷取），核心是搞懂 `/fg5/req` 這個請求的**回應長什麼結構**：
- **請求（client→server）是明文** protobuf：我們早就能讀（f1 序號、f2 押注、f3=20B token、f4=32B key）。
- **回應（server→client）是加密的**：這就是要破的東西。

【解釋 protobuf】：Google 的二進位資料格式。一筆資料由很多「欄位」組成，每個欄位有編號（f1、f2…）和型別（數字/字串/巢狀）。比 JSON 省空間，但不是給人讀的。

---

## 1. 為什麼這麼難：加密模型

任何加密都是 `密文 = 演算法(明文, 金鑰)`。兩個零件分開放：

| 零件 | 放哪 | 我們有沒有 |
|---|---|---|
| 演算法（cipher 的程式碼） | 在混淆 JS bundle 裡 | 有，但被 jscrambler 包死 |
| 金鑰 | runtime 才生、只在記憶體 | 沒有 |

離線試各種對稱演算法（AES/ChaCha…）配 f4 全失敗 → 推論它走 **ECDH**。

【解釋 ECDH】：一種「雙方各自算出同一把金鑰、但金鑰本身從不在網路上傳」的機制。client 開一對臨時鑰匙（私鑰 priv、公鑰 pub），把 pub（就是 f4 那 32 bytes）明文送出；真正的加解密金鑰 = `ECDH(client_priv, server_pub)`，只在記憶體。**所以 f4 不是金鑰、是公鑰；去 bundle 裡 grep 金鑰註定白費**，因為根本沒有靜態金鑰。

---

## 2. 六條路線，五條牆（今天全部親手驗證）

### 路線 A：離線暴力破解密文
拿擷取到的密文，離線試 AES/ChaCha/RC4/XOR/SM4 配 f4 各種衍生 + 強驗證（整段要能解析成 protobuf）。
**全滅。** 因為缺金鑰（見上）。這不是「演算法神秘」，是「零件缺一個」。

### 路線 B：靜態反混淆，從 bundle 挖演算法/schema
想直接讀混淆 JS 裡的 cipher 或 protobuf 定義。
**撞牆。** jscrambler 的手法：
- 連 `XMLHttpRequest`、`crypto`、`subtle` 這些 API 名字都藏進「解碼表」，執行期才現解 → **靜態 grep 全 0 命中**。
- 字串解碼器是「執行期建表 + 自我參照」，離線抽出來單獨跑會無限迴圈 / OOM。
- 今天再確認：四個 bundle grep 不到任何 protobufjs 指紋 → schema 也被藏死。

### 路線 C：原生層 hook crypto（Frida）
【解釋 Frida】：一個能「注入到已在跑的程式、攔截任意函式」的工具。它在**原生層（機器碼）**動作，比 JS 層低，jscrambler 在 JS 層的自我防護看不到它。

想法：不管 JS 怎麼混淆，最後解密一定會呼叫瀏覽器底層的加密函式（BoringSSL 的 `EVP_AEAD_CTX_open`），在那裡攔就能拿到明文。
**撞牆，死因今天才完全確認：**
- 我用 Frida 找到一個 `EVP_AEAD_CTX_open`，但它的位址在 `0x1d...` → 那是**系統的 libboringssl**（macOS 內建那份），**遊戲根本不呼叫它**。
- Chrome 自己那份 BoringSSL 是**靜態編譯進 framework、而且符號被 strip（拿掉名字）**，只剩 3 個 export → 找不到「實際在跑的那個解密函式」。
- 昨天還試過用「常數指紋」定位（cipher 通常有特徵常數表），但 arm64 用**硬體加密指令**（AESE/PMULL），根本不碰那些常數表 → 定位不到。

【解釋 strip】：編譯時把函式的名字（符號表）拿掉，只剩機器碼。像一本書把目錄撕了，內容還在但你不知道哪一頁是哪一章。

### 路線 D：JS 層注入 hook（DevTools console / 擴充）
想在遊戲讀網路回應的那一刻攔下來、印出呼叫堆疊，找到解密函式。用的是「hook 原生 XMLHttpRequest」而不是 `crypto.subtle`（後者會被抓）。
**撞牆，而且是最戲劇性的一條：** 在 DevTools console 貼 hook 程式，報錯：
- `typeof XMLHttpRequest` = **undefined**
- `typeof Array.prototype.forEach` = **Array is not defined**

也就是說遊戲啟動時，**先把 `Array`、`XMLHttpRequest`、`window.frames` 這些最核心的全域「各存一份私有的、然後把全域刪光」**。它自己用私有那份跑，任何事後想用全域來 hook 的 JS 全部陣亡。

【解釋】：想像一個人進門後把所有工具各偷藏一把，然後把公用工具櫃清空。他自己有工具照用，但你這個後來的人打開櫃子什麼都沒有。這叫**焦土反 tamper（scorched-earth anti-tamper）**。

### 路線 E：DevTools 原生斷點
既然 JS 全域被毀，那用 DevTools 內建的「XHR 中斷點」——這是瀏覽器原生功能，在 jscrambler 投毒層「底下」，不靠 JS 全域。
**撞牆：** 一設中斷點、遊戲一被暫停，就噴出一堆 `p.apply is not a function`、遊戲直接崩。

【解釋】：那個混淆 bundle 是靠「執行期一個迴圈不斷解碼字串」在跑的（很脆弱、對時序敏感）。一旦被 breakpoint 暫停打斷，解碼狀態就錯亂、連鎖崩潰。**結論：這遊戲只要「執行被打斷」（不管是 JS hook 還是 pause）就自毀。**

### 路線 F：被動讀記憶體（唯一活路）
前面五條不是被偵測、就是自毀。只有「**被動讀 heap**」不 hook、不暫停，遊戲偵測不到。

【解釋 heap】：程式執行時存放資料的記憶體區。遊戲解密完的回應、餘額、盤面，都在這裡（是「解析後的物件」形式）。Frida 可以把這塊記憶體整塊 dump 下來，純讀、不干擾。

**這條能走，但一開始撞了三個坑：**

#### 坑 1：掃餘額，全找不到
拿畫面餘額（你報 999971.532）去 heap 搜各種編碼（double、乘 100/1000 的整數、字串…）全 0。
- 後來發現：**你多念了一位**，實際是 999971.53（2 位小數）。用對的值一搜，餘額確實以 **double** 存在！（`999973.57` 命中 20 處）
- 但**只找得到「解析後的餘額 double」和「顯示字串」，找不到「原始 protobuf 回應」**。

#### 坑 2：原始明文活不過 1.4 秒
為什麼找不到原始回應？因為它是**瞬時的**。
【解釋 V8 GC】：瀏覽器的 JS 引擎叫 V8。它會「垃圾回收（Garbage Collection）」——定時把不再用的記憶體清掉、還會**搬移**還在用的物件。遊戲解密出原始 protobuf → 立刻解析成物件 → 原始那塊就沒人用了 → **下一次 GC（不到 1.4 秒）就被回收/覆蓋**。

我做了「連續連拍」：每 1.4 秒 dump 一整塊 heap，連拍 40 秒 35 張。結果：**35 張裡沒有任何一張抓到原始 protobuf**。因為它活不過一個 GC 週期，比連拍間隔還短。

#### 坑 3：連餘額都不在原始回應裡
更關鍵：後來發現**回應根本不帶絕對餘額**（伺服器只回「這把贏多少」，餘額是 client 自己算 `舊-注+贏`）。所以拿餘額當錨點，**再怎麼樣都追不到原始回應**——它不在裡面。

---

## 3. 轉折點：你說「用單號查」

這是整場的關鍵。你提出用**單號**（那串 `23932-989600-00770696`）當錨點。這個想法比餘額好太多，理由：

1. **是字串** → 沒有「double 還是整數、乘幾倍」的編碼歧義。
2. **每次 spin 亂跳** → 一定是**伺服器在回應裡發下來的**（client 自己生不出來）。
3. **會顯示在畫面** → 代表遊戲**留著它**（不像原始 protobuf 那樣被秒回收）。
4. **格式獨特** → 幾乎不會誤判。

一搜，果然找到——但這裡有個轉折，見下一節。

---

## 4. 意外的大發現：遊戲自己把解密回應快取成 JSON

用單號（和中獎金額 6.48）去搜、順著找它周圍的資料時，撞到這個東西：

```
{"type":0,"ret":0,"error_msg":"","data":[10,158,1,10,5,...,105,236,81,184,30,133,235,25,64,...]}
```

**遊戲自己把每一筆「解密後」的回應，存成一個 JSON 快取在 heap 裡**，`data` 那個陣列**就是解密後的原始 protobuf 位元組**。

這等於**遊戲把自己解好的答案抄在旁邊給我們看**——完全繞過加密：
- 不用破 crypto
- 不用跟 1.4 秒的 GC 賽跑（這個 JSON 快取是持久的）
- 只要搜 `{"type":` 就全抓到

把那串 `data` 當 protobuf 一解，欄位跟你報的值**全部對上**：

| 欄位 | 值 | 意義 | 對照 |
|---|---|---|---|
| f6 (f64) | 999977.6525 | 餘額 | ✅ 你報 999977.652 |
| f3 / f1.f13 (f64) | 6.48 | 總中獎 | ✅ 你報 6.48 |
| f20 (varint) | 2393298960000770696 | 單號 | ✅ = 23932-989600-00770696 |
| f23.f1 (f64) | 0.3 | 下注 | ✅ 你報 0.3 |
| f1.f6[] ×3 | 每條 f4=2.16 | 3 條中獎線（3×2.16=6.48） | ✅ |
| f1.f2.f1 | [11,9,10,9,9,11,9,9,12,20] | 盤面符號 | ✅ |

**補充**：單號當初搜「字串」失敗，是因為它在 protobuf 裡其實是 **varint（數字）**，顯示時才加上 `-`。你念的數字是對的，是它的儲存型別跟我猜的不一樣。

---

## 5. 最終方法 + 工具

**方法**：全 dump 遊戲 renderer 的 heap → 搜所有 `{"type":N,"ret":0,"data":[...]}` → 把 data 當 protobuf 解析。

**工具**：`extract_responses.py`
```bash
# 1. 開遊戲（VPN→BR、新鮮 token）
./run_cft.sh "<game_url>"
# 2. 手動點兩顆按鈕進畫面，轉幾把（要驗證欄位就轉到中獎）
# 3. 一鍵抓 + 解碼
./.venv/bin/python -u extract_responses.py 696
#    → games/696/responses.jsonl + 螢幕摘要
```

已抓到 type:0（spin 結果，完整 schema）、type:2（餘額更新）。樣本在 `games/696/DECODED_RESPONSE_sample.md`。

**天花板**：這是**擷取「解密後的回應內容」**（供逐款還原遊戲行為/數據，去自建 mock）；它**不解開 crypto**，所以做不出「讓真 JILI client 直接連的 mock」——但對「逐款擷取協定/數據」這個目標，已經夠了。

---

## 6. 教訓

1. **具體錨點 >>> 盲目掃描**。餘額（會格式化、可能不在回應裡）害我繞很久；你用「單號 / 中獎金額」這種伺服器發的、獨特的值，一下就逼出答案。
2. **防護再強，資料終究要用**。加密破不了、hook 全自毀，但遊戲自己**必須把回應解密來用**——解密後那份就在記憶體，甚至被它自己快取成 JSON。**攻「它不得不留下的東西」，而不是「它努力藏的東西」。**
3. **對照已知值來確立欄位語意**：spin 一把會中獎的，記下中獎+餘額+單號，回頭對 protobuf 欄位，語意就定了。

---

## 7. 補完請求端(mock server 必須)

回應端解完後,mock server 還缺一半:**它得看得懂 client 送進來的 spin 請求**(怎麼發起 spin、下注多少、有沒有開額外下注)。請求是**明文** protobuf,理論上簡單,但踩了一個坑:

### 坑:改注不打伺服器
先想從 heap 撈請求(請求也被快取)。結果只找到「設定類」訊息(帶語言參數),**spin 請求本身在 heap 找不到**。接著讓使用者「把下注改成 100 但不 spin」,dump 對照——**沒有任何新請求出現**。

結論:**改注是純 client 端動作,不送伺服器**。那下注額和額外下注一定是**跟著 spin 那一刻一起送**;而 spin 請求跟原始明文回應一樣是**瞬時的**,heap 留不住 → 所以 heap 撈不到。

### 解法:netlog 錄線路
【解釋 netlog】:Chrome 內建的網路記錄功能。用 `--log-net-log=檔 --net-log-capture-mode=Everything` 啟動,它會把**線路上每個位元組**(含 request/response body)錄進一個 JSON。這是「線上實際送了什麼」的最權威來源。

流程:`run_cft_netlog.sh "<token>"` → 玩(設注、開額外下注、spin)→ **關 Chrome 視窗**(netlog 要視窗關閉才寫完整)→ `extract_fg5.py 696 --netlog <檔>` 解出明文請求。

> 注意:Everything 模式若在「載入階段」開,會把 30MB 資源下載也錄進去、拖垮 Chrome。但實測 spin 階段的量還好(9~40 筆 /fg5/req),檔案 ~150MB 可接受。

### 結果:請求端也對上了
做兩組對照(A: bet 100 + 8倍額外下注;B: bet 0.3 + 無額外下注),解出 spin 請求:

```
一般 spin (0.3):     f2{ f1=0.3,  f25={0,0,0} }              (76B)
8倍額外下注 (100):   f2{ f1=100.0, f25={0,0,0}, f26={f1:1} }  (81B)
```

- **f2.f1 (f64) = 下注額** ✅(0.3 / 100.0 = 使用者設的)
- **f2.f26 = 額外下注**(有=開,f26.f1=級別)✅ 跟回應 f23.f26 **完全鏡射**
- f3=token(20B)、f4=key(32B),整場固定

**這也解開了先前的矛盾**:下注/額外下注每把 spin 都在請求 `f2` 裡,伺服器據此算回應。mock server 直接讀請求的 f2.f1 / f2.f26 就好,不用維護 session 狀態。

---

## 8. 最終成果(696 完整)

| 面向 | 成果 | 檔案 |
|---|---|---|
| 回應端 schema | 餘額/中獎/單號/倍率/中獎線/盤面/額外下注/省略規則 | SCHEMA.md |
| 請求端 schema | spin(bet f2.f1 / ante f2.f26)、init、其他型態 | REQUEST_SCHEMA.md |
| 行為覆蓋 | base 中/沒中、1.5倍、8倍額外下注、倍率套用 | COVERAGE.md |
| 原始資料 | 請求+加密回應 / 解碼回應 | fg5_exchanges.json / responses.jsonl |
| 工具 | heap→回應 / netlog→請求 | extract_responses.py / extract_fg5.py |

**一句話總結**:JILI 的加密破不了、防護是專業級,但「攻它不得不留下/送出的東西」——**回應靠遊戲自己快取的 JSON(heap),請求靠 netlog 錄線路**——就完整還原了整個協定,完全繞過加密。逐款套這套流程即可。

---

## 9. 靜態分析 index.22de5.js:cipher 在哪?(定論:WebCrypto)

Path A 想「反混淆 + patch crypto」。照專業建議走**分層離線靜態分析**(不執行檔、不碰 anti-tamper),用 acorn 建 indexer:

- **index_bundle.js / index_bundle2.js**:把 1.48MB → 結構地圖。5450 函式、270 dispatcher;主解碼器 `Χ4M`(7572 callsites);解碼表 `Υ2Z`/`D5` 都 `=[arguments]`(表由外部傳入 → 離線抽 decoder 會 OOM 的根源);crypto 編排群聚在 offset **820K–980K**。
- **fingerprint.js(運算子指紋磨利版)**:找 cipher 特有旋轉常數(ChaCha {16,12,8,7}、SHA、AES sbox)。結果:**JS 裡完全沒有 cipher 簽名**;bitwise 密集全是 protobufjs/Long.js 雜訊。唯一靜態表(286 元素)反組譯後是 **Long.js 的 int64 WASM(mul/div/rem/get_high)**,不是 sbox。

**定論:cipher 不在 JS bundle,遊戲用 WebCrypto(crypto.subtle → 原生 BoringSSL 標準原語)。** 你沒法 patch 一個不在 JS 裡的 cipher。

**為何 blind K recovery 全空(非方法差)**:WebCrypto CryptoKey 是 opaque,raw key material 經 importKey/deriveKey 後離開 JS 可見記憶體。「heap 找 32B」前提本身錯。

**正確方向**:不找 K,找 WebCrypto 語義邊界(AST 形狀:Promise chain、TypedArray、演算法物件),從已知密文反向 data-flow slicing 追 algorithm/key/nonce/AAD/plaintext 五輸入,只做 820K–980K 群聚。→ crypto-oriented static indexer。
