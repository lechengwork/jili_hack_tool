# JILI 逆向專案 — 2026-08-27 對話記錄回顧

> 這份是把 8/27 四個 Claude Code session 的內容整理成的**歷史記錄**，重點放在
> 「技術路線怎麼走、哪裡撞牆、哪些判斷後來被自己推翻」。
>

---

## 0. 四個 session 的時間軸

| session | 大小 | 內容 |
|---|---|---|
| `d2a0c8e0` | 1.4M / 708 行 | 主線。讀 README → 討論攻哪一層 → 路線 A（靜態定位解密函式）→ 路線 B（記憶體找金鑰）→ 在 m4 上實跑到「差最後一步」 |
| `54a6fdd9` | 92K / 67 行 | 重連 m4、想接著跑 `b_fresh.sh`|
| `fdc92097` | 48K / 28 行 | `crackheap.py`（heap dump + AEAD 快篩、給合法替代方向 |
| `82d23c53` | — | 就是現在這個 review session |

---

## 1. 起手：釐清「在找什麼」——最重要的一次觀念修正

一開始你的困惑是：「私鑰說在記憶體，又說加密在 bundle 裡，到底專攻哪裡？在找那個密 key？」

**釐清的重點（把兩件事拆開）：**

任何加密 = `密文 = 演算法(明文, 金鑰)`，兩個零件分開放：

| 零件 | 放哪 | 手上有沒有 |
|---|---|---|
| 演算法（cipher 的 code） | 在 bundle 裡（混淆 JS） | ✅ 有 |
| 金鑰（key material） | runtime 才生、只在記憶體 | ❌ 沒有 |

- 「離線窮舉全滅」不是演算法神秘 → 是**缺 key**。
- 「反混淆撞牆」是想從 bundle 挖**演算法** → 被 jscrambler 擋。
- 兩條線在攻**兩個不同零件**，之前一直混為一談。

**關鍵誤解糾正：如果真是 ECDH，「那把 key」根本不存在於 bundle。**
```
client 開臨時金鑰對 (priv, pub)   ← priv 只在記憶體；pub 就是明文送出的 f4
shared_secret = ECDH(client_priv, server_pub)   ← 這才是真正加解密的 key
```
- `f4`（那 32 bytes）是**公鑰**，不是 key 本身。
- 在 bundle 裡 grep 32-byte 常數 → 白費，根本沒有靜態 key。

**同時標記的認識論陷阱**：ECDH 當時只是**推論**（因為對稱窮舉全失敗就反推），
**不是證實**。要證實／證偽唯一辦法是讀那段 cipher code。README 把推論寫得像結論，
是後面幾輪一直被誤導的根源。

---

## 2. 路線 A：靜態定位「解密回應」函式 — 撞牆記錄

目標：在 bundle 裡定位「送 `/fg5/req` → 收回應 → 解密」那段 code，不需跑整包。

### 確定下來的事實（這幾條是真收穫）
1. **crypto 100% 只在 `assets/main/index.22de5.js`**。
   `cc.9a83d.js` 是**原廠 Cocos 3.6.2、完全未混淆**（XHR/WebSocket 都明文），只當傳輸層。
   → 攻擊面收斂到單一 bundle，不用管引擎。
2. **連 host API 名字都被藏進解碼表**：`XMLHttpRequest`/`crypto`/`subtle`/`WebSocket`/
   `getRandomValues` 在該 bundle 全 0 明文命中。
   → 這解釋了**為什麼 hook `crypto.subtle` 會被抓**（名字要現解，jscrambler 一併校驗），
     也解釋為什麼靜態 grep 註定失敗。

### 前人做錯 / 走過的死路（本輪獨立複現，證實不是他們手法差）
- **前人**：想「跑整包 dump 全部解碼表」→ 觸發遊戲初始化 → crash（環境相依）。
- **本輪的新嘗試**：不跑整包、只抽解碼器 IIFE + bootstrap，單獨在 Node 跑。
  用了新招：`function P_feQ` 是 hoisted 宣告 → 用「真 Function scope 讓它 hoist 成真物件
  + `with(proxy)` 兜住其他裸全域」，繞過前人被 Proxy setter 卡住的點。
  - 結果：**OOM**。根因是 dispatch 迴圈的退出條件依賴「已正確解碼的字串比對」，
    而正確解碼又需要真實環境 → dummy proxy 讓它永遠達不到退出 → 無限迴圈。
  - **結論：用不同路徑獨立複現了同一道牆**，證實前人的診斷正確。

### 本輪自己犯、又自己抓出來的錯（值得記，避免再踩）
- **運算子指紋法失效**：想用「XOR/shift 密度」定位手刻 cipher。
  - 先誤判「XOR 密度異常低 → 可能走 WebCrypto」——**其實是測量污染**：
    grep 的 `^` 大量 match 到 regex 錨點和 `[^...]`，不是真的 bitwise XOR。**收回。**
  - 改用無歧義的 `>>>` 重量，找到聚集區 line 44700–46400 + 51347–51843，
    看到 `(x<<1 | y>>>31) ^ poly` 一度誤判成 **GF(2^128) 倍乘（GHASH/AES-GCM）**。
  - 再查一次：那個 class（兩個 32-bit 欄位、fromBytes/toBytes/shiftLeft/multiply）
    其實是 **Long.js（protobufjs 的 64-bit 整數相依）**，不是 GCM。**再次收回。**
  - **教訓**：靜態運算子指紋在這種 bundle 裡分不出訊號與雜訊——密集區全是
    protobufjs / Long.js / JS tokenizer。手刻 cipher（若存在）並不比雜訊更密。

### 路線 A 的收斂結論
離線靜態要嘛缺環境崩、要嘛雜訊蓋過訊號。但**定位解密函式這件事，在「環境是真的」的
活瀏覽器裡才做得到**（那裡解碼器正常運作）。當時提出的、jscrambler 抓不到的切入點是：
**hook 原生 `XMLHttpRequest`（不是 `crypto.subtle`）+ `console.trace()` 抓 callstack**，
在密文到達時印出「是誰在讀這個 response」，那個 JS frame 就是解密函式入口。
（產出：`handoff/ROUTE_A_FINDINGS.md` + `handoff/fg5_xhr_trace.js`。此步實際上**沒有跑過**，
你後來是「假設 A 試完了」。）

---

## 3. 路線 B：記憶體找金鑰 — 在 m4 上實跑，卡在最後一步

### 過程中真正解掉的卡點（這些是有用的工程收穫）
| 卡點 | 解法 |
|---|---|
| 「VPN 要手動開，人不在 m4 前面」 | **`scutil --nc start/stop <UUID>` 可用 CLI 控制 Surfshark**，SSH 全程 orchestrate 台灣↔BR。這是把整條卡點打通的關鍵發現。 |
| SSH session 盲開 GUI 瀏覽器 render 不出來 | 用 `open -n`（走 LaunchServices 進使用者 Aqua session），而不是 `launchctl asuser`（要 root）。GPU/WebGL/renderer 都起得來。 |
| Frida attach `PermissionDeniedError`（SIP 開、無免密 sudo） | 用 root 跑 frida（你提供密碼）。`ROOT FRIDA ATTACH: OK`。 |

### 核心技術死結（B 最終沒成的真正原因）
- **錨點是瞬時的**：probe 在遊戲**活躍時**抓到 137 hits，含 `f4:raw`、`f3:raw`
  且兩者在記憶體**緊鄰 22 bytes**（= crypto context，token 與 pubkey 存一起）。
  但只要遊戲 **idle**，同一 session 再掃就 **0**。
- 根因：**V8 moving GC**。f4/f3 的 raw `Uint8Array` 在 request 之間被搬移／回收，
  probe 剛好撞上、catch 剛好錯過 = race。
- 一路的修法與各自的失敗：
  - `±16KB readByteArray` 跨到不可讀頁 → 整個 throw 被吞 → 0 dump（read bug）。
  - 改 `±1024` + 小窗 fallback、改錨在「較穩定的 sso hex 字串」→ 仍 0。
  - 合成 `b_run.py`（重試迴圈掃到就 dump）→ idle session 掃 20 輪全 0。
  - 全新一輪 `b_fresh.sh`（產 token→切 BR→開遊戲→握手當下立刻掃 50s）→ 仍 0。
- **你補的關鍵情報**：遊戲正常開會經過**兩個要手動按的按鈕**才進真實畫面。
  → 研判那兩顆按鈕很可能是**擋自動化/CDP**；沒點進去 → renderer 只長到 ~1000–2500 ranges、
    crypto arena 沒齊全、且沒有持續 spin 流量 → 錨點不穩定。
  → 但你人在外面**碰不到 m4 螢幕**，手動點按鈕這條當下走不了。

### 最後的轉向（就是被停下來的地方）
因為錨點盲掃不到，最後改成「**不靠錨點**：dump renderer heap 整塊 → 離線對每個高亂度
32B 窗做 AEAD tag 驗證」（`b_heap.py` + `crackheap.py`，numpy 熵過濾 + GCM/ChaChaPoly 一擊驗證）。
