# JILI 696 route X — 本地 mock harness

在本機用**真實 Chrome for Testing** 把 JILI 網頁老虎機（gameID **696**，迦罗战神500 / Fortune Garuda 500）跑起來，接自架 mock server。**協定已 100% 破解、遊戲端到端可玩、spin 可回放。**

---

## 快速開始

```bash
./setup.sh     # 換機器第一次:建 .venv、裝 frida/cryptography、裝 Chrome for Testing、寫 /etc/hosts
./run.sh       # 全自動:開 mock + 遊戲 → 等載好 → 開 patcher → 自動 reload → 進遊戲
./stop.sh      # 收工:關 mock + patchwasm + CfT
```

`./run.sh` 全程你只需：**輸兩次 Mac 密碼**（mock、patcher 兩個視窗各一次）。其餘（等 999.2、按 Enter、Cmd-R）都自動。進遊戲後直接轉 spin。

**前置需求**：macOS Apple Silicon、`python3`、`node`/`npx`、sudo 權限。

---

## 運作原理（為什麼需要這三件套）

遊戲的 fg5 crypto（Rust wasm）內建**真 server 的 X25519/Ed25519 公鑰**，回應是
`Ed25519_sig(64) ‖ nonce(12) ‖ AES-256-GCM(key, …)`，`key = X25519(client_eph, server_pub)`。
我們沒有真 server 私鑰，所以：

1. **mock server**（`routex/server.py`）：用**我們自己的**金鑰對簽名/加密，並回放解密出來的真實 session（config → init → spin → 餘額）。
2. **patchwasm.py（Frida）**：
   - 把 wasm 內建的 8 塊公鑰 chunk（linear `1048576`）改成 mock 公鑰 → **Ed25519 簽章驗證**過關。
   - **`FIX_SHARED`**：搶不贏「patch pub 早於遊戲導 shared」的時序（shared oracle 已證死），改成趁**回應停頓**把遊戲導出的 shared（linear `1108480`）**直接覆寫**成 mock 算的正確值 → **AES-GCM 解密**過關。
3. **`/etc/hosts`** 把四個遊戲網域指到 `127.0.0.1`（Jscrambler domain-lock 要求真網域，不能用 localhost）。

> `SSO_DELAY` 讓 patcher 先掛好；`HS_DELAY` 是覆寫 `@1108480` 的窗口。詳見 memory `jili-patch-mechanism-solved`。

---

## 檔案

| 路徑 | 作用 |
|---|---|
| `run.sh` / `stop.sh` / `setup.sh` | 一鍵啟動 / 停止 / 備環境 |
| `patchwasm.py` | Frida：patch 公鑰 + FIX_SHARED 覆寫 shared |
| `routex/server.py` | mock server（TLS、handshake、有序回放） |
| `routex/fg5.py` | 協定 crypto（簽名/加密/protobuf） |
| `routex/mockkeys.json` | mock 金鑰對；`routex/gen_and_patch.py` 產生 |
| `routex/decrypt_capture.py` | 用側錄的臨時私鑰離線解密整段 session |
| `games/696/exchanges_ordered.jsonl` | **解密後的完整有序 session**（回放來源） |
| `games/696/responses.jsonl` / `init_sequence.jsonl` | 依 type / 依序的回應樣本 |
| `game_site_backup/` | 遊戲靜態資源鏡像 |
| `JILI-NOTES.md` | 逆向過程逐項證據（歷史） |

---

## 疑難

- **一直轉 / 卡住** → mock 沒回放對；貼 mock log 的 `kind=spin` / `poll*` 幾行來看。
- **999.2** → patcher 沒趕上：確認 mock 視窗有 `FIX_SHARED @1108480 <-`、遊戲有自動 reload；沒 reload 就手動 Cmd-R。
- **掛不到 renderer** → 只開一個 CfT 分頁；`./stop.sh` 清乾淨再 `./run.sh`。
- **別開 DevTools**（觸發 Jscrambler 自我防禦）。

整套是**非永久**的：關掉 patchwasm/mock 就失效，需重跑 `./run.sh`。
