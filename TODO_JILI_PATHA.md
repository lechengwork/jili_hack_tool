# JILI Path A 交接 TODO(2026-08-28 收尾,下個 session 接手)

> ⚠️ 2026-08-29 更新:重大進度見 **`PROGRESS_0829.md`**。已做出離線 WASM oracle（`harness_run2.js`),
> 確認 Model C（server_pub 內建 = `26aa760e…`,shared 已在記憶體驗證),並發現回應格式 =
> **header(64) ‖ nonce(12) ‖ ct ‖ tag**。唯一剩:解 64-byte header(f_tb dcmp3285 / f_ec dcmp7554)。
> 下面舊內容(路線 X/Y/Z、纯 nonce‖ct‖tag 的假設)多已被 harness 實測取代。

## 一句話狀態
JILI /fg5/req 的 crypto **已完全識別**:是一個 runtime 載入的 **Rust wasm-bindgen WASM 模組**,
用 **X25519(ECDH)+ AES-256-GCM + protobuf**。Path A 已從「不可能」縮到「普通實作 + 2~3 個小未知量」。
下一步是**建 mock server**(讓真前端能連),或先把小未知量釘死。

---

## ✅ 已確定(別再重查,證據充分)
- **crypto 不在 JS**:index.22de5.js(jscrambler)全檔僅 19 個 XOR、無 async → 不可能有對稱 cipher / WebCrypto。JS 裡的 bitwise 大戶是 **MurmurHash3(0xCC9E2D51)+ Long.js**(雜訊)。
- **crypto = Rust WASM**:heap 抽出,187KB,已存 `games/696/crypto.wasm`(validate ✅)。data section 的 Rust crate 路徑鐵證:
  - X25519:`curve25519-dalek 4.1.3`
  - AEAD:`aes-gcm 0.10.3` + `aes 0.8.4`(soft/fixslice32 = bitsliced,所以 heap 撈不到 raw key)+ `ctr 0.9.2` + `universal-hash`(GHASH)
  - 訊息:`protobuf 3.7.2`;回 JS:`serde-wasm-bindgen`(=heap 那個 `{"type":..,"data":[..]}` JSON)
- **框架**:回應 230B = `nonce(12) ‖ ciphertext ‖ tag(16)`,明文 202B(含 type/ret/error_msg + data)。
- **亂數**:`__wbindgen_start`(func75)啟動時呼叫 getRandomValues 播 32B → 全域 CSPRNG(once_cell);ephemeral key/nonce 從此抽(harness 實測確認)。
- **API/ABI**:exports `login(i32,i32)` `send(i32,i32,i32)` `send_to(i32,i32,i32,i32)` `start()` + malloc/free(export_0~6)。host imports 只有 rng+fetch+url/location+json+wbindgen glue(**無任何 crypto import** → 加解密全在 WASM 內)。
- **為何之前全失敗**:crypto 在 WASM(JS 無 cipher);AES key bitsliced + shared secret 用完即 drop(heap 撈不到 raw 32B);crackheap2 框架對但拿不到 key。

## ❓ 剩 2~3 個小未知量(有限、可窮舉)
1. **KDF**:AES-256 key = X25519 shared secret **直接用**,或經一次 hash(`func231` 是個 64-bit 壓縮函式,`c<<50^c<<46^c<<23`+Ch/Maj,疑似)。→ 二選一。
2. **AAD**:AES-GCM 的 associated data = 空 / header / 某段 metadata。
3. nonce:已確認隨機 + prepend(基本確定)。

## 📋 下一步任務(擇一路線)

### 路線 X:建 mock server + 實測敲定小未知量(建議,最快)
- [ ] 用標準庫做 mock server(Rust: x25519-dalek + aes-gcm + protobuf;或 Node: @noble/curves x25519 + node:crypto aes-256-gcm + protobufjs)
- [ ] server 端:收 login(含 client_pub = 請求 f4,32B 明文)→ 生 server keypair → `shared = X25519(server_priv, f4)` → AES key = shared(先試直用)→ 回應用 AES-256-GCM(nonce=random12 prepend, tag append)+ protobuf,server_pub 放回應對應欄位
- [ ] 讓真前端(game_site_backup + 這個 WASM SDK)連 mock,解不開就窮舉:{key: 直用 / SHA512(shared)截32} × {AAD: 空 / header} = 4 組
- [ ] 對照回應 schema:`games/696/SCHEMA.md`(餘額 f6 / 中獎 f3 / 單號 f20 / 倍率 f1.f12 / 額外下注 f23.f26 …);請求 schema:`games/696/REQUEST_SCHEMA.md`(bet=f2.f1, ante=f2.f26)

### 路線 Y:靜態把小未知量釘死(普通 WASM RE)
- [ ] 讀 `games/696/crypto.dcmp`(wasm-decompile C-like,19K 行)的 login 未來鏈:f258→f395→f188(key setup, k32/n12)→ 找 server_pub 從哪個 protobuf 欄位、shared→key 有沒有過 func231
- [ ] 讀 send 鏈:f250→f394→(async poll)→ AEAD encrypt 呼叫,看 nonce 來源 + AAD 參數
- [ ] 工具:Ghidra WASM plugin 會比手讀 dcmp 快很多(建議專業人用)

### 路線 Z:動態 harness(80% 完成,卡在 wasm-bindgen glue)
- [ ] `harness_run.js` 已能 instantiate + 跑 start(RNG 播種)+ 設定 login;但驅動 async future 需忠實重現 ~40 個 wbindgen glue(finicky whack-a-mole,每個錯的 import → unreachable)
- [ ] 若要走這條:考慮從 index.22de5.js 抽出遊戲「原本的 wbindgen glue」重用(混淆但邏輯在),比手寫準

---

## 📦 交付物清單(都在 games/696/ 或專案根)
- `games/696/crypto.wasm` — Rust crypto 模組(核心!)
- `games/696/crypto.wat` — 反組譯(57K 行)
- `games/696/crypto.dcmp` — wasm-decompile C-like(19K 行,可讀)
- `games/696/PROTOCOL_SPEC.md` — 協定規格 + 函式地圖 + 3 未知量指標
- `games/696/imports.json / exports.json / abi.json` — WASM surface
- `games/696/SCHEMA.md / REQUEST_SCHEMA.md / COVERAGE.md / DECODED_RESPONSE_sample.md` — 已解的回應/請求協定
- 工具(專案根):index_bundle.js / index_bundle2.js / fingerprint.js / crypto_index.js / crypto_index2.js / wat_trace.js / wat_tree.js / harness_surface.js / harness_run.js
- 一鍵開遊戲:`go.sh`(VPN 自動開關+產token+開遊戲);`extract_responses.py`(heap→解密回應);`extract_fg5.py`(netlog→明文請求)
- 記憶:jili-anti-reverse-engineering.md（含全過程）、jili-heap-extraction-method.md、PROCESS_0828.md

## 提醒
- 開遊戲:`bash go.sh 696`(需人手點兩顆按鈕進畫面)。
- 記憶裡「crypto 在 index.22de5.js」是舊的錯判,已更正為「crypto 在 Rust WASM」。
