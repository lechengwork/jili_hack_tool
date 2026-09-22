# JILI /fg5/req 協定規格(逆向,2026-08-28)
來源:runtime 載入的 Rust wasm-bindgen 模組(games/696/crypto.wasm,187KB,heap 抽出;crypto.wat 為反組譯)。

## 已可靠確定(crate 證據 + 常數 + call graph)
### Key exchange
- **X25519 ECDH**(crate `curve25519-dalek 4.1.3`)。client 每 session 生 ephemeral keypair;client pubkey = 請求的 **f4(32B)**(明文)。
- server pubkey:由 server 在握手(login)回應下發。**[未定] 在回應的哪個 protobuf 欄位** → 見函式 f188/f377/f290。

### Key derivation
- **無 HKDF/SHA(crate 清單無 hkdf/sha2/hmac)** → AES-256 key **極可能 = X25519 shared secret(32B)直接用**。**[待反編譯確認資料流]**(f188/f290 k32)。

### AEAD 加密
- **AES-256-GCM**(crate `aes-gcm 0.10.3` + `aes 0.8.4` soft/fixslice32 bitsliced + `ctr 0.9.2` + `universal-hash` GHASH)。
- nonce = **12 bytes**(常數確認)。tag = **16 bytes**(常數確認)。
- 亂數:getRandomValues/randomFillSync 只在 `__wbindgen_start`(f75)呼叫 → seed 全域 CSPRNG(once_cell);ephemeral key/nonce 由此 PRNG 抽 → **nonce 應為隨機、每訊息一個**。
- **[未定] AAD 是空、header、還是某段 metadata** → 見 send 路徑 f229/f391/f242 的 aead encrypt 呼叫參數。

### Wire framing(數學吻合)
- 回應 230B = **nonce(12) ‖ ciphertext ‖ tag(16)**,ciphertext=202B(=解密後 wire 明文,內含 type/ret/error_msg + data(183B))。
- 訊息 = protobuf(crate `protobuf 3.7.2`)。回應解密後 = `{type,ret,error_msg,data}`(serde-wasm-bindgen 吐回 JS 的 JSON 即此)。

## 三個待反編譯釘死的未知量(給專業人的切入點)
1. **server_pub 來源**:login 回應的哪個欄位 → 反編譯 f258→f395→**f188**(+ f377/f290,k32/n12 標註)。
2. **nonce 構造**:確認隨機(從全域 PRNG)且 prepend,非計數器 → 反編譯 send f250→f394→**f229**→f391/f242(n12)。
3. **AAD**:aead encrypt 的 associated data(空/header/metadata)→ 同 f229/f391 的 encrypt 呼叫。

## 函式地圖(crypto.wat)
- exports:login=f258(param i32,i32)、send=f250(i32,i32,i32)、send_to=f246(i32,i32,i32,i32)、start=f75。
- login 鏈:f258→f395→f188[n12 k32]→f377→f388→f340→{f128/f142/f347 t16, f290 k32}。
- send 鏈:f250[aes n12 t16]→f394→f229[t16]→f377…;及 f252[n12 t16]、f391[n12 t16 k32]→f242。
- AES 函式:70 93 112 120 198 204 205 206 296 414 462;其上游 78 79 82 93 232 348 349 350。
- 亂數 import:getRandomValues=#37、randomFillSync=#35(僅 f75 呼叫)。

## mock 端要做的(拿到上述 3 未知量後)
server:收 login(含 client_pub f4)→ 生 server keypair → shared=X25519(server_priv,f4) → AES-256-GCM(key=shared, nonce=隨機12, aad=?)加密 protobuf 回應,框架 nonce‖ct‖tag;server_pub 放回應對應欄位。用任何語言的標準 x25519+aes-gcm 函式庫即可。
