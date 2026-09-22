# JILI 696 純網頁版破解歷程（2026-09-02）

> 目標：把「要靠 Frida 陪跑」的 mock，收斂成**純 server 端、開遊戲就生效**的純網頁版。
> 結果：**成功**。`INJECT_BUNDLE=1` 把 shim 塞進 `polyfills.bundle`，hook `WebAssembly.compile`/`compileStreaming` 在編譯前改 8 個內建 server 公鑰 chunk → 遊戲導的 X25519 shared 天生就對 → handshake 通、`init[...]` 整條消化、無 999.2。**免 Frida、免 FIX_SHARED、免時序賽跑。**
>
> 這份記錄一路上的**阻礙（含各種混淆/反偵測）**、我**繞的冤枉路與誤判**，以及**使用者的關鍵提示**如何一步步把我導到正解。

---

## 一、擋在「理解」前面的混淆層（obfuscation / anti-understanding）

破解之前，光是「看懂它在幹嘛」就有好幾層阻礙：

1. **字串反轉（reversed strings）**：遊戲 URL 的參數把 host 名整個反過來寫，前端再反轉回去組 API URL。例：
   - `be=moc.2afafaflj.ipabewbw-tau` → 反轉 → `uat-wbwebapi.jlfafafa2.com`
   - `gs=moc.1afafaflj.df-tolsbw-tau` → `uat-wbslot-fd.jlfafafa1.com`
   - `domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau` → `uat-wbslot-platform.jlfafafa3.com`
   一開始看到這串會以為是亂碼，其實只是 `reverse()`。

2. **內建金鑰 XOR 0xAA 混淆**：wasm 裡的 X25519 / Ed25519 公鑰不是明文，是每個 byte XOR 0xAA。要先解混淆才對得上。

3. **wasm 不在任何送出的檔案裡**：crypto.wasm 是 bundle 用**自訂編碼**在執行期解出來的，靜態搜（含 zip/XOR）翻遍所有送出檔都找不到。所以「靜態換檔」這條從頭就死。

4. **Jscrambler 把遊戲 bundle 整個混淆**：`index.22de5.js` 等是控制流平坦化 + 變數極短命名（`cF`/`aF`/`tm`/`SE`/`TE`/`Ub`/`yb`/`Rl`…），肉眼幾乎讀不動。

5. **Jscrambler 反除錯（anti-debug）**：**一開 DevTools，它就弄壞 `index.22de5.js` 報 `SyntaxError`、卡 loading**。這條最陰——它讓「想看 console 診斷」本身變成另一個死因，還跟別的死法長得一模一樣，害我 session 第一跑就誤判（那次 DevTools 是開的，SyntaxError 其實是反除錯，不是 shim 的問題）。

6. **Jscrambler 焦土化（self-defending）**：偵測到竄改就**把自己的碼替換成垃圾**（自毀），表現就是卡在某個 bundle。這是後面所有「靜默卡死」的來源。

---

## 二、核心密碼牆（在此之前已解，本 session 的起點）

- **能解、不能偽造（Model C）**：解真伺服器回應只要 `AES key = X25519(client 臨時私鑰, 內建 server 公鑰)`——兩者都拿得到，所以**能解封包**。但**假冒伺服器發回應**要 **server 私鑰**（簽章 + ECDH），在真站永遠拿不到。
- 所以 mock 只能用**自己的 keypair** 簽/加密 → 必須讓遊戲 wasm **改用我們的公鑰驗章/導 shared** → 這就是那道「patch wasm 內建 8 個 pub chunk」的牆。
- 舊解法：**Frida 從 OS 層改記憶體**（能通，但要外掛陪跑、非永久）。本 session 想拿掉它。

---

## 三、我繞的冤枉路（web-shim 的一路誤判）

核心誤區：**我一直以為死因是「我動了 WebAssembly / FPT / toString」，於是拼命做原生性偽裝**。實際上每次都是死在別的地方，但我把帳算錯了。

| 版本 | 我做了什麼 | 結果 | 我當時的（錯誤）結論 |
|---|---|---|---|
| v1/v2 | hook `instantiate/Instance`，per-fn toString 偽裝 | 死 22de5 | 以為 toString 露餡 |
| v3 | 全域接管 `Function.prototype.toString` + WeakMap | 死 22de5，`FPT-probe` 沒響 | 以為不是主 realm toString，改猜跨 realm |
| v4 | method-shorthand，把 prototype/name/length/hasOwnProperty 全對齊原生 | 死 22de5 | 以為 property 破綻都補了還死，猜 cross-realm/checksum |
| v5 | 改 hook `Module/compile/compileStreaming` | 死更早（7dcc1） | **誤判「7dcc1 盯 Module」**——其實是我**自己把 `Module.imports` 靜態方法弄不見**，SystemJS 用它、壞了引擎 wasm。自傷。 |
| v6 | 只 hook `compile/compileStreaming` 改 bytes（修好 Module.imports） | 死 22de5 | 以為 compile 也被盯 → 一度想放棄回 Frida |
| Test A | **只換 FPT、完全不碰 WebAssembly** | 死 22de5 | 「換 FPT 就死」——但仍是注入 script 送進去的，confound |
| Test A2 | 惰性：只發 1 個 beacon，其餘全不做 | **也死 22de5** | ⚠ 開始警覺：連惰性都死 |
| Test A3 | 純註解 `<script>`，不執行、不發 beacon | **也死 22de5** | 確認：**只要注入就死，跟我的碼無關** |
| Test A4 | 注入後**立刻 `removeChild` 自我移除** | **還是死 22de5** | 不是 22de5 當下掃 DOM（移除沒用） |

**這一路的教訓**：我反覆被 **confound（混淆變數）** 咬——每一版都同時動了好幾樣東西，死了就歸因給最可疑的那個，卻沒做乾淨的對照組。直到被逼著做 inert 對照（A2/A3/A4），才發現**真正的兇手一直是「多了一個注入的 `<script>` 元素」**，而不是 hook / FPT / toString。之前 v3~v6 的 WebAssembly hook、Test A 的 FPT，**其實從來沒被抓，是被「注入 script」這個載體連累**。

---

## 四、使用者的關鍵提示（真正推動進度的，是這幾句）

我卡在黑箱 A/B 時，是使用者的幾個提問一次次把方向撬開：

1. **「Frida 都 patch 得掉、本地能跑，表示這塊沒被校驗，網頁 patch 理論上也行；而且收/解封包都過 wasm，表示有跟 JS 溝通、有傳 reference」**
   → 確立「純網頁理論上可行」，並點出「拿到 instance 就能讀寫 `exports.memory`」。（我補充了關鍵不對稱：Frida 不受沙箱、不需 instance 參照；JS 一定要透過 hook 拿 instance。）

2. **「他把 wasm 轉 2 進制再 Jscrambler 包；檢查應該是 `WebAssembly.instantiate/Instance` 存不存在；焦土化後名字不一樣所以卡了」**
   → 促成去測**沒測過的 API**（`Module`/`compile`）。這條雖然當場死（且我又自傷 Module.imports），但**逼我去 heap 逆向那條載入鏈**，撈出真相（見下）。

3. **「怎麼可能 Jscrambler 比 index.html 早？在外面包住轉發不就行？」**
   → 打掉我「搶第一就隱形」的錯誤心智模型。正解是：**搶第一只讓你先動手，但改動留在 DOM/HTML 是持久證據，晚跑的稽查照樣看得到。** 這句話其實已經指向「載體」問題了。

4. **「那他到底檢查什麼？我們不是有 dump 記憶體，可以離線查」**
   → 促成 **heap 逆向**（`/tmp/heap_696.bin`）。撈出兩個關鍵事實：
   - heap 裡讀得到的 `Function.prototype.toString.call(x) + "{ [native code] }"` 檢查，其實是 **Google Tag Manager 的遙測**（`lj("jsp",...)` 只回報、不弄壞遊戲）——**紅鯡魚**，不是兇手。真兇（Jscrambler）是混淆碼、不以可讀字串躺 heap。
   - **真實 wasm 載入鏈**（SystemJS plugin，可讀）：`compileStreaming(resp)`（或 `resp.arrayBuffer().then(compile)`）→ Module → `Module.imports(module)`（靜態）→ `instantiate(module, imports)`。並看到 crypto.wasm 有 70 個 import（wasm-bindgen）。← 這直接告訴我「該 hook compile」以及「別碰 Module 靜態方法」。

5. **★決勝的一句★ —「他到底怎麼識別的，不可能啊，一直會有載他的載體，他怎麼切乾淨的呢」**（在 Test A4 自我移除也死之後）
   → 這句點破全局。我因此去把整份 `index.html` 讀完（確認**沒有 SRI、沒有 hash、沒有 nonce**），並猛然意識到：
   - **所有 WebAssembly-hook 的死，都是死在「多了一個 `<script>` 元素」這個載體**，不是死在 hook。
   - 破法就是**你說的「用現有載體」**——**不加新元素，改一個遊戲本來就會載的 bundle 的內容**（`polyfills.bundle`：最早載、無 SRI、非 Jscrambler 保護的遊戲檔）。HTML 一字不改、DOM/script 結構不變 → 環境檢查沒東西可抓。

---

## 五、突破與正解

照著「用現有載體」的方向，兩跑定案：

- **Test C1**（把**惰性 beacon** prepend 進 `polyfills.bundle`，HTML 不改）→ **一路衝到 `/fg5/req` 999.2**（跟 baseline 一樣）。**證明改現有 bundle 內容不被抓。**
- **Test C2**（把**完整 compile-hook byte-patch** prepend 進 `polyfills.bundle`）→ **`init[9..12]` 整條消化、無 999.2 → 可以玩。**

### 最終方案
1. **載體**：`INJECT_BUNDLE=1` → server 把 `routex/wasm_patch_shim.js` **prepend 進 `polyfills.bundle.5adbf.js` 的內容**（不加新 `<script>`、HTML byte-identical）。
2. **手法**：hook `WebAssembly.compile`/`compileStreaming`，在**編譯前的 bytes** find&replace 8 個 pub chunk（`crypto.wasm`→`crypto.patched.wasm` 那 8 筆）。compileStreaming 內部 downgrade 成 buffered 再 patch。**不碰 `Module`（保住 `imports` 靜態方法）、不碰 `instantiate`/`Instance`、不換 FPT、不做 toString 偽裝**（實測 22de5 沒查 compile 原生性）。
3. **為何天生免 FIX_SHARED/時序**：pub 在**編譯前**就換成 mock pub → 編出來的 module 內建 mock pub → 遊戲自己導的 X25519 shared = 對的 AES key，Ed25519 驗簽也一起過。比 Frida「導錯 shared 再覆寫」乾淨。

### 跑法
```bash
cd routex
sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 ../.venv/bin/python3 server.py
# 開遊戲（任何 Chrome 皆可，不用 Frida、不用 CfT、別開 DevTools）
# mock log 看到 cs d=8 / compile d=8（crypto 被 patch；引擎 wasm 是 d=0 正常）+ init[...] = 通
```

---

## 六、可帶走的教訓

1. **「搶第一」不等於「隱形」**：你先執行，但你留下的痕跡（多的 `<script>` 元素、被換的 global）是持久證據；晚跑的稽查回頭一看就發現。要嘛不留痕跡，要嘛用它本來就有的東西。
2. **反竄改的第一道牆常是「注入本身」，不是你注入的內容**：與其苦練原生性偽裝去騙 hook 檢查，不如**根本不新增元素**——改現有、無 SRI、非保護的載體（這裡是 polyfills.bundle）。
3. **做乾淨的對照組**：我最大的浪費來自「一版改好幾樣、死了亂歸因」。惰性對照組（A2/A3/A4）一出，真兇立刻現形。
4. **在編譯前改 bytes > 在記憶體改**：byte-patch pub 讓 shared「天生就對」，省掉整個時序賽跑與覆寫。
5. **hook wasm 相關 API 時，別忘了靜態方法**：`WebAssembly.Module.imports/exports/customSections` 是 SystemJS 要用的，換 `Module` 沒複製它們會自傷（v5 的坑）。
6. **DevTools 是毒**：Jscrambler 反除錯一開就弄壞 bundle，且與其他死法難分。診斷改用 beacon → mock log（`new Image().src='/__wasmpatch__/<msg>'`）。
7. **heap dump 能看混淆碼，但要挑**：讀得到的 `[native code]` 檢查是 gtag 紅鯡魚；真兇不以可讀字串存在。但 heap 也給了無價情報——真實 wasm 載入鏈，直接指出該 hook 哪個 API。

---

*相關檔案：`routex/wasm_patch_shim.js`（C2 正解）、`routex/server.py`（`INJECT_BUNDLE` 模式）、memory `jili-patch-mechanism-solved.md`（「純網頁版跑通」節）。*
