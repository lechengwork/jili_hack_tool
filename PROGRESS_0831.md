# JILI 696 進度 & 交接 — 2026-08-31

> 接手先讀這份。前情:`PROTOCOL_SOLVED.md`(crypto 規格)、`games/696/GAME_FORMAT_SPEC.md`(應用層格式)。

## TL;DR 現況

- **協定 / crypto / config / 遊戲格式:100% 解完 + 文件化。** ✅
- **Mock server（`routex/`）:完整實作**,能讓真前端載入、走到 `/fg5/req` handshake。
- **唯一卡點(MSG 999.2 handshake loop):** 遊戲 wasm 內建**真 server 公鑰**,會拒絕 mock 用「自己 keypair」簽的回應 → 遊戲一直重握手 → 逾時 999.2。
- **要破這關 = 把 wasm 記憶體裡那 8 個「內建 server 公鑰 chunk」覆寫成 mock 的公鑰。** 三條交付路:
  | 路 | 結果 |
  |---|---|
  | 靜態換 `*.wasm` 回應 | ✗ 遊戲不發 .wasm 請求 |
  | 靜態改 bundle 裡的 wasm | ✗ wasm 是 JS 自訂編碼解出,不在任何送出檔案(徹底搜過含 zip/XOR) |
  | JS shim hook `WebAssembly.instantiate` | ✗ Jscrambler 反竄改偵測到 → 弄壞 `index.22de5.js` → 卡 loading |
  | **Frida 改記憶體 pub** | ◐ **唯一還能動**,但「掃不到 chunk」,且**非永久**(每次開遊戲要重跑) |
- **下一步(接手就做這個):`dumpmem.py` dump 一份 mock session 記憶體,離線確認那 8 個 chunk 在不在、在哪區 → 修 `patchwasm.py` 的掃描。**

---

## 關鍵觀念(別再搞混)

**「找到的 key」是 client 臨時私鑰(讀用),不是 server 私鑰(寫用)。**
- **解密**真伺服器回應:`AES key = X25519(client 臨時私鑰, server 公鑰)`。client 臨時私鑰從 heap 撈到(那一場)、server 公鑰是 baked const → 兩者湊齊就能解。**這就是我們能解出封包的原因。**
- **假冒伺服器發回應**:需要 **server 私鑰**(簽章 + ECDH)。**在真伺服器上,永遠拿不到。**
- 所以 mock 用**自己產的 keypair**(`mockkeys.json`)簽/加密 → 需要遊戲 wasm 改用**我們的公鑰**驗章 → 就是那道 patch 牆。

## 環境陷阱(全都踩過,務必記住)

- **別開 DevTools** —— Jscrambler 反除錯偵測到 DevTools 就弄壞 `index.22de5.js`(開著報 `SyntaxError`,不開靜默卡 loading)。要看 shim 狀態改用 **beacon → mock log**(`★★★ [shim-report] ...`),不要用 console。
- **Frida attach:** 一般 `/Applications/Google Chrome`(hardened runtime 簽章)**連 root 都掛不上**(`PermissionDeniedError`)。**必須用 CfT(`Google Chrome for Testing`)+ `--no-sandbox`**。CfT 路徑見 `go.sh`。
- `patchwasm.py` 印 `renderers=0` 有時其實是「找到但 attach 失敗」(已改 log 會分辨:`found N but ATTACH FAILED`)。
- `patchwasm.py` renderer 過濾器已放寬(認 `Google Chrome` / `chrome-mac-arm64` / `Chrome for Testing`)。
- **443 要 sudo**;`/etc/hosts` 要有 4 個 host → 127.0.0.1(測 mock);要抓真站則反過來拿掉(`sed -i '' '/jlfafafa/d' /etc/hosts` + flush DNS)。
- **VPN 對測 mock 無影響**(loopback 不走 VPN,已測「關了也一樣」)。
- **wasm 掃 chunk 教訓:** 即時 Frida `readByteArray` 讀 WASM 區小窗會失敗;但**整段 range 讀(extract_responses/dumpmem 那種)或離線讀檔完全 OK**。所以撈私鑰當初是「dump 成檔 → 離線搜」才成功。

---

## 已完成(不用再碰)

- **crypto envelope 全解**(`PROTOCOL_SOLVED.md`;⚠ 回應明文欄位是 `f1=ts(ms), f3=type, f5=data, f6=error_msg, f7=ret` —— 舊筆記的 `{f1=type,f2=ret,...}` 是錯的)。
- **整段 session 離線全解**:`/tmp/heap_696.bin`(go.sh capture,1.3GB)裡以 f4 為錨撈到 client 臨時私鑰 `eeca1470...` → `key=X25519(priv, 26aa..17)=8f7995f5...` → `decrypt_capture.py` 解全部 38 筆,**簽章全效**。
- **config = type 1(223B)**:貨幣 `$`/`USD`、餘額、bet 選單 `[0.3,0.5,0.8,1,2,5,10,20,30,40,70,100]`、ante 倍率 `[1.0,1.5,8.0]`、限額 32.5。外層必含 **f1=server 毫秒時間戳**(缺了遊戲會重握手 → 這是之前 999.2 的其中一個 bug,已修)。
- **完整 init 序列**(`games/696/init_sequence.jsonl`,ex0-12 腳本化):type `1,58,69,51,60(ret=801),19,58,58,10,21,33,25,27`,之後 balance(2)。
- **`games/696/responses.jsonl`**:13 種真實型別的解密 payload。
- **格式文件**:`games/696/GAME_FORMAT_SPEC.md` + Artifact `https://claude.ai/code/artifact/31b47b7f-d72e-4d3e-b0ac-72bd170ad099`(前端/RTP 用)。

## Mock server 現況(`routex/`,全部端到端測過)

`server.py` 已實作:靜態站 + `/sso-login.api`(假 token,時間戳動態)+ **`/fg5/req`**(序列重播:handshake→type1 config always、spin→type0、其餘走 init_sequence,之後 poll→2/ack→25;每筆含 f1 時間戳)+ **`/lifeservice/ws2`**(保活 WebSocket:binary 握手→`{"error":0}`,心跳排掉,ping→pong)+ **shim 注入**(env `INJECT_SHIM=1`,**預設關**,因會觸發 Jscrambler)+ **`__wasmpatch__` beacon** log。

啟動:`sudo env PORT=443 TLS=1 VERBOSE=1 ../.venv/bin/python3 server.py`

## 檔案清單

| 檔 | 用途 |
|---|---|
| `routex/server.py` | mock 主程式 |
| `routex/fg5.py` | crypto 核心(protobuf + X25519/AES-GCM/Ed25519;build_plaintext 含 f1 ts) |
| `routex/decrypt_capture.py` | 離線解密 capture(`--grab /tmp/jili_grab.json` / `--priv` / `--key`);`--selftest` 過 |
| `routex/wasm_pub_patches.json` | **8 個 (orig→mock) pub chunk**(verified: find&replace `crypto.wasm`→`crypto.patched.wasm`) |
| `routex/crypto.patched.wasm` | patched wasm(mock pub);**遊戲沒載到它**(它自己從 bundle 解原版) |
| `routex/wasm_patch_shim.js` | JS shim(hook instantiate/compile)——**被 Jscrambler 擋,別用** |
| `routex/mockkeys.json` | mock keypair(x25519_priv=0x42*32, ed25519_priv=0x24*32 附近) |
| `games/696/init_sequence.jsonl` | 有序 init 回應(序列重播用) |
| `games/696/responses.jsonl` | 13 型別解密 payload |
| `patchwasm.py` | **Frida 記憶體 patch**(scan+write 8 chunk);**卡在掃不到 chunk** |
| `dumpmem.py` | **只 dump 記憶體到 `/tmp/mock_heap.bin`(不覆寫任何東西)** — 下一步用 |
| `grabkey.py` | Frida 撈 client 臨時私鑰(離線讀檔那招的即時版) |
| `games/696/GAME_FORMAT_SPEC.md` | 給前端/RTP 的格式規格 |

---

## 下一步(接手照這個做)

### 步驟 1:dump mock session 記憶體,離線查 chunk
```bash
# ① 乾淨 mock(不要 INJECT_SHIM)
cd /Users/dyson/Downloads/jili/routex
sudo env PORT=443 TLS=1 VERBOSE=1 ../.venv/bin/python3 server.py

# ② CfT + --no-sandbox 開遊戲(Frida 才掛得上),等 mock log 進 handshake loop
pkill -f 'chrome-mac-arm64'; sleep 1
open -n "/Users/dyson/Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app" --args \
  --no-sandbox --user-data-dir=/tmp/cft-mock-$(date +%s) \
  --ignore-certificate-errors --disable-quic --no-first-run --no-default-browser-check \
  --disable-features=ChromeWhatsNewUI \
  'https://uat-wbgame.jlfafafa3.com/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0'

# ③ dump(不覆寫 responses.jsonl)
cd /Users/dyson/Downloads/jili
sudo ./.venv/bin/python dumpmem.py     # -> /tmp/mock_heap.bin
```
然後離線檢查 8 個 chunk 在不在:
```bash
.venv/bin/python3 -c "
import json; d=open('/tmp/mock_heap.bin','rb').read()
for r in json.load(open('routex/wasm_pub_patches.json')):
    o=bytes.fromhex(r['orig']); print(r['orig'],'x',d.count(o))
"
```

### 步驟 2:依結果
- **8 chunk 都在(count>0)** → `patchwasm.py` 的 scanSync 有 bug/漏區,修它讓命中 → 跑 `sudo patchwasm.py`(先跑再開遊戲,趁 wasm 剛載入、first key 導出前 patch)→ 遊戲該接受 config、mock log 跳 seq=2、過 999.2。**成功 = 每次陪跑的可玩 mock(非永久)。**
- **chunk 不在(count=0)** → mock session 的 wasm pub 不在可掃記憶體(可能 decode 後 transient、或在非 rw- 區)→ Frida 也難。誠實回報,選項:
  - **Path B**:自建極簡前端,直接載 `crypto.patched.wasm`(harness 已證能跑)連 mock,但遊戲 UI 要重建(大工程)。
  - **停**:協定/crypto/文件已交付,真前端連 mock 這哩卡在 Jscrambler 反竄改。

### 已排除的路(別重試)
- 靜態換 .wasm / 改 bundle:wasm 是 JS 自訂編碼,不在任何送出檔案。
- JS shim:Jscrambler 自衛擋死。
- 開 DevTools 看 console:觸發 Jscrambler,反而弄壞遊戲。

---

## 一句話交接
**讀=解決;寫=卡在改 wasm 內建 server 公鑰。唯一活路是 Frida 記憶體 patch(非永久),當前卡在「掃不到那 8 個 chunk」→ 用 `dumpmem.py` dump 一份離線確認,再修 `patchwasm.py`。**
