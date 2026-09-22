# JILI /fg5/req 協定 — 完全破解(2026-08-29)

**狀態:crypto 100% 破解,route X 已用真 WASM 端到端驗證成功。**
harness `harness_run2.js`(patch 兩把內建 pub 成自己的)餵入 mock 回應 → 真 WASM 驗章+解密+解析 →
resolve `{"type":0,"ret":0,"error_msg":"","data":[]}`。

## 完整協定
### 傳輸
- HTTP/2 POST `https://<gs反轉>/fg5/req`(gs 來自 game_url query,反轉字串);sso 登入走 `https://<be反轉>/sso-login.api`(`key=<ssoKey>&lang=..`,回 JSON 含 `token`)。
- WASM 自己 fetch(host imports 有 fetch/url);前端只呼叫 `login(ssoKey)`、`send(seq,ptr,len)`。

### 請求(明文 protobuf,client→server)
```
f1 = seq (varint)
f2 = message (依動作;spin: f2.f1=bet(f64), f2.f26=ante, f2.f25=spin旗標)
f3 = token (20B, sso-login 回應的 token)
f4 = client ephemeral X25519 pubkey (32B)   ← 每場一組,getRandomValues 首 32B = 私鑰
```

### 回應(server→client)
```
[0:64]   = Ed25519 簽章 (R:32 ‖ s:32),訊息 M = response[64:]
[64:76]  = nonce (12B, 隨機)
[76:]    = AES-256-GCM 密文 ‖ tag(16B)
```
- **AES-256 key = X25519(client_ephemeral_priv, 內建server_X25519_pub) 直用(無 KDF/雜湊)**
- **AAD = 空**
- 解密後明文 = protobuf(serde-wasm-bindgen → JS `{type,ret,error_msg,data}`)。
  **⚠ 修正(2026-08-31,真 WASM 逐欄探測驗證):欄位號是 `f3=type(varint), f5=data(bytes), f6=error_msg(string), f7=ret(varint)`,不是 f1~f4!**
  舊記的 `{f1=type,f2=ret,f3=error_msg,f4=data}` 是錯的——當初只用全零的 `"0800"`(f1=0)測,所有欄位都落在預設值,剛好 resolve 成 `{type:0,ret:0,"",[]}` 而沒被抓到。用錯欄位號會讓每個真實 payload 靜默變空(type/data 都收不到)。
  探測法:餵 `fN=值` 的回應進 harness,看 resolve 出來哪個 key 變動 → f3→type、f5→data、f6→error_msg、f7→ret。已用真 spin(type0+183B)、balance(type2+15B)驗證 type 與 data 都正確送達。
  data = 遊戲負載(spin 結果等,見 SCHEMA.md;實際 spin 明文長 = 總長-64-12-16)。

### 內建金鑰(WASM 常數,XOR 0xAA 混淆)
- **X25519 server pub** = `26aa760e99da9a40f3ab907f0d7b07e17b36e6a199e8400abde61af01a08da17`
  - 記憶體位址(8B×4,存前先 XOR 0xAA):`1052760, 1052800, 1052840, 1052880`
  - 用途:client 算 shared = X25519(client_priv, 這把) = AES key。**server 私鑰不可得 → mock 要 patch 成自己的 pub。**
- **Ed25519 verify pub** = `81c785c85653e6a1e92c9359646e23f662f5615975ae7faa6a5721358018ff8c`
  - 記憶體位址:`1052920, 1052960, 1048576, 1053032`(注意第三段在資料段起點 1048576!)
  - 用途:驗回應簽章。**server 簽章私鑰不可得 → mock 要 patch 成自己的 Ed25519 pub。**

### 驗證流程(dcmp 6633-6768)
1. `len<64` → 1301;拆 [0:64] header
2. f_fg 解 header 兩半 → f_fe(載入內建 Ed25519 pub A)→ f_kc(1303)→ f_tb(Ed25519 群驗證,1304)
3. 剩餘 `<12` → 1305;拆 12B nonce
4. once_cell 未初始化 → 1202/1201;f_ic 用 shared@1108480 建 AES-GCM context(1306)
5. f_ec = AES-GCM 解密,失敗 → 1307;成功 → 解析 protobuf → resolve

## Route X 部署(Model C:必須 patch WASM)
1. **改前端載入的 crypto.wasm 兩把內建 pub → mock 自己的 keypair pub**
   - 目前用 harness runtime patch(env `PATCH_X25519`/`PATCH_ED25519`)驗證過。真部署要改**檔案**:
     WASM data 段的 8 個 8-byte 位置(memory addr 見上,需換算 file offset;或直接在 mitm 攔截 crypto.wasm 回應時改 bytes)。
   - 值 = mock_pub[i*8:i*8+8] XOR 0xAA,寫回對應位址。
2. **mock server**(任何語言,標準庫 x25519+aes-256-gcm+ed25519+protobuf):
   - 收 /fg5/req 請求(明文 protobuf),讀 f4=client_pub、f1=seq、f2=動作。
   - `shared = X25519(mock_x_priv, client_pub)`;`key = shared`。
   - 組回應明文 protobuf `{type, ret:0, data:<遊戲結果>}` → `nonce=random12` → `ct=AESGCM(key).encrypt(nonce, pt, b"")`。
   - `M = nonce‖ct`;`sig = Ed25519_sign(mock_ed_priv, M)`;回 `sig‖nonce‖ct`。
   - server_X25519_pub/Ed25519_pub = mock 自己的(已 patch 進 client)。
3. **交付/前端**:serve `game_site_backup` 靜態檔(含 patched crypto.wasm)+ 攔 /fg5/req + sso-login.api(回假 token)。

## 已驗證的 mock 範例(harness 端到端)
- mock keypair:x25519 priv=0x42*32、ed25519 priv=0x24*32(見 /tmp/mockkeys.json)。
- 回應 `Ed25519_sign(0x24…, nonce‖ct) ‖ nonce ‖ AESGCM(X25519(0x42…,client_pub)).encrypt(nonce, "0800", "")` → resolve `{type:0,...}`。
- 產生器邏輯見本 session 的 python(可搬進 mock server)。

## 工具
- `harness_run2.js` — 離線真-WASM oracle(patch + 餵回應驗證)。env:`SSO PATCH_X25519 PATCH_ED25519 RESPFILE MARKER DUMPMEM V`。
- 內建金鑰抽法:XOR 0xAA of consts(位址見上);Ed25519 pub 抽取見 dcmp f_fe 12243-12250。
