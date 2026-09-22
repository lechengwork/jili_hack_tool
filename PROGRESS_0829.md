# JILI Path A 進度(2026-08-29 — 離線 harness 突破)

## 一句話狀態
**做出離線 WASM oracle（`harness_run2.js`）**,能在 node 裡完整驅動 `login()`+`send()` 的 wasm-bindgen async future,
用**可控 getRandomValues → 已知 ephemeral 私鑰**當真 client。已釘死 crypto 模型與回應格式,只剩「64-byte header 內容」未解。

## 決定性成果(全部離線,無需開遊戲)
### harness_run2.js — 離線 crypto oracle(核心交付物)
- 忠實重建 wasm-bindgen runtime:heap、closure(`makeMutClosure`)、Promise::new(executor 走 `export_6`)、
  `.then`/queueMicrotask、fetch/Request/Response(json + **arrayBuffer**)、URL/URLSearchParams、getRandomValues。
- 關鍵修正(上個 session 卡點):`export_1=malloc`、**`export_2=realloc`(不是 executor!)**、`export_0` 設 global、
  `export_4=dealloc(closure dtor)`、`export_5/6` = closure invoke,**callee 索引存在 struct+16**(decompiler `call_indirect(a,c,b[4])` 最後運算元才是 table idx)。
- 流程:`start()`→ `login(ssoKey)` 打 **sso-login.api**(host 來自 game_url 的 `be` 反轉字串)→ 拿 token →
  `send(seq,ptr,len)` 打 **/fg5/req**,自動做 X25519 keygen + 建請求 + 收回應解密。
- 跑法:`SSO=<40hex> RESPFILE=<回應bin> node harness_run2.js`;可設 `DUMPMEM=/path` dump 線性記憶體、`MARKER=<hex>` 掃明文。

### 已釘死(證據充分)
- **RNG = OsRng 直用**(rand_core os.rs,無 ChaCha/StdRng)。getRandomValues 首次 32B 就是 **ephemeral 私鑰**(不是 HashMap seed)。
  harness 固定 RNG → 私鑰 = `1112131415…2f30`,client_pub(f4)=`4d27bcee3135c494…5498d07c`(= scalarmult_base 驗證通過)。
- **Model C 確認:server_pub 是 WASM 內建常數(不是握手下發)**。換 server_priv 不影響結果 → client 不讀我 prefix。
- **內建 server_pub = `26aa760e99da9a40f3ab907f0d7b07e17b36e6a199e8400abde61af01a08da17`**
  = XOR 0xAA of 四段常數 `mem[1052760:8]‖mem[1052800:8]‖mem[1052840:8]‖mem[1052880:8]`(dcmp ~5769-5784,f_im 複製常數→a+640→XOR0xAA→f_ne 轉場元素)。
- **shared = X25519(client_priv, 26aa76…) = `4944669d4bd6d805ef097d8cccde6c5f519dd0206754e84df90c76e012cca85f`**,
  **此 shared 在 WASM 記憶體 @1108480 找到(count=1)→ 抽取正確、模型正確**。旁邊 @1108532 = client_priv(once_cell 快取)。

### 回應格式(dcmp 6633-6760,f_lh(13xx) 錯誤碼對應表)— **關鍵新發現**
回應 **不是**裸 nonce‖ct‖tag,而是:
```
[0:64]   = HEADER (64B)          ← f_fg/f_tb 驗證;失敗 = 1302/1303/1304
[64:76]  = nonce (12B)           ← 前置 if(len<64)=1301, 拆完 if(rest<12)=1305
[76:]    = ciphertext ‖ tag(16)  ← f_ec = AES-GCM 解密;失敗 = 1307
```
- 錯誤碼:1301=總長<64;1302/1303/1304=header 驗證失敗;1305=header 後不足 12;1306=?;1307=AEAD 解密/認證失敗;
  1001=response.ok=false;1201/1202=once_cell 未初始化。
- 實測:我所有裸 nonce‖ct‖tag 回應都卡 1304(header 驗證),真實擷取回應卡 1307(到解密但我 harness 是別的 session key)。
  → 證明「到 1307 = header 過關、進到解密」。

## 唯一剩下的未知量:64-byte HEADER 內容
- 處理鏈:`f_fg`(func187,1302)→ 57B copy + `f_fe`/`f_kc`(1303)→ 188B copy + `f_tb`(func71,1304)→ 才進 nonce/decrypt(`f_ec` func82)。
- **f_fg(a,b,c) 已讀**:只檢查 `c==64`(否則旗標),然後把 64B header **重排複製**到 a+1
  (順序:d[16]=b[0]; d[48]=b[32]; 中間 8-byte 塊搬移 → 疑似把 header 拆成兩個 32B 半 + 交錯)。**f_fg 本身不是簽章驗證,只是 parse/copy**。
- 真正驗證在 **f_tb(func71 @dcmp 3285)**(1304 卡點,含 188B copy)與 **f_ec(func82 @7554)**。
  header 疑似:兩個 32B(server ephemeral pub + MAC/point?)。**尚未確認是否為可離線偽造(用 shared 產生)還是需 server 簽章私鑰**。
- **下一步(依序)**:
  1. 讀 `f_tb`(dcmp 3285)+ `f_ec`(dcmp 7554)+ `f_kc`(8396)+ `f_fe`(12233),看 header 兩半怎麼用、有沒有用到「只有 server 有的私鑰」。
  2. 若 header 只用 shared/公開資訊 → mock 用標準庫產生 header,route X 完成。
  3. 若 header 需 server 私鑰簽章 → 除了 patch WASM 內建 server_pub(`26aa76…`)成自己的 pub,還要 patch 驗章公鑰。
  4. **harness 是唯一驗證器**:產一個候選 `header(64)‖nonce(12)‖ct‖tag` 回應餵進去,錯誤碼從 **1304→1307** = header 過關;**1307→resolve/其他** = 解密也過關(用正確 shared+framing)。
- **重要**:先前所有 KDF/AAD/framing 窮舉都卡在 1304(header),**不是**因為 KDF/AAD 錯 → KDF/AAD 仍未定,要過了 header 才能定。

## 檔案
- `harness_run2.js`(oracle)、`mock_fg5.py`(產回應)、scratchpad `findpriv.py`/`brute_kdf.py`(掃私鑰/窮舉)。
- `/tmp/wmem.bin`(harness send 後的線性記憶體 dump)、`/tmp/heap.bin`(舊:fg5_exchanges 同場 renderer heap,含 client_pub×32)。
- dcmp 關鍵行:回應處理 6560-6768;X25519 5600-5860;error 碼 `f_lh(13xx)`。
