# Pappu — JILI 200／平台 4103

本遊戲的程式、靜態資產、數學模組、擷取與驗證都留在 games/200/，不建立另一份專案或 ZIP。

## 本地 replay

在專案根目錄執行 `.venv/bin/python -B replay_200.py`。預設即時讀 math，亦可加 `--source wire` 或 `--rounds <原始單號>`；所有帳號與餘額為本地合成，不需 VPN／真站 token。詳細操作與驗證見 `REPLAY.md`。

## 給機率團隊

- pappumath/game/g4103/setting_4103.go：機率團隊填版本、聯合結果權重、TargetRTP 與容許誤差。
- pappumath/README.md：比照 124 的本地 Go 呼叫、含本金賠率、共同房間結果及測試。
- math/INTERFACE.md、math_200.proto：乾淨逐局介面與已確認規則。
- math/<單號>.json：六局自己的成功下注／結算樣本，沒有 token、accountID、原始請求或 bytes。
- math_adapter.py：乾淨 math 與完整 Pappu Command 雙向轉換；pappu_200.proto／math_schema.json 是工程線路規格。

正式機率設定刻意留空，未填或 RTP 逐格驗收不符時回錯誤，不偷偷使用測試權重。server 直接呼叫 Go module，不經 RPC。多人桌每局只抽一次，再用同一 Outcome 結算各玩家。

## 已驗證資料

2026-11-06，IDR 來源，六局已確認自己的下注／回應與原始 wagers，累計 12 次下注請求；另有 11 次旁觀結果，不算成功 math 樣本。六局皆驗過完整請求／回應／RoomEnd frame byte round-trip、自己的 uid 與 clientCheckNum、賠付公式及餘額變化。math_validation.json 有彙整，math_sources.json 只記錄不含憑證的來源索引。

Pappu 基礎淨賠率 9，含本金回收 10；線路 bonus 是最終含本金回收，不借用 124 的倍數公式。單號 644919319188238536 的陀螺下注 200,000，回收 2,000,000。20／30 倍的出現不代表 isBonus=true。特殊模式、多重 reward、完整機率分布未建立，不假設已覆蓋。

本版傳輸是明文 protobuf WebSocket／TLS，原始 Command 只有 type/data，已驗的已知 frame 無獨立應用層簽章欄位。不捏造驗章成功；以完整 codec、原始表示、下注／房間及金額關聯驗證。未知欄位／特殊結構保留原始資料，拒絕發布共享 math。

## 驗證

在 pappumath/ 執行：

```sh
go test ./...
go test -race ./...
```

在專案根目錄執行：

```sh
.venv/bin/python -B games/200/verify_math.py
.venv/bin/python -B games/200/finish_capture.py
```

Python 測試會用原始 JavaScript codec 檢查修改後的回應及乾淨 proto，另驗原封包還原、整數精度、未知欄位、自己與他人下注分流、同單號衝突保護。JavaScript 驗證共用已安裝於 games/545/runtime 的第三方 protobufjs runtime，不讀取其他遊戲的 schema。

## 下一次擷取

擷取帳號 JFS-IDR／ys3／SGJ22IDR → try → tryplayer003idr，已核對對應 token 與 /pappu/index.html?gameID=200。專用憑證只在被忽略的 capture_config.local.json，共用 config.json 保持原來帳號。

1. 關 VPN，執行 .venv/bin/python games/200/login_capture.py，取得新的單次 URL。
2. 執行 .venv/bin/python -B -u games/200/capture_server.py，建立獨立 session。
3. 連 Brazil／São Paulo，確認後執行 .venv/bin/python -B games/200/open_capture.py。瀏覽器保留憑證檢查，安全警告由操作人員處理。不要開 DevTools。
4. 由操作人員下注。每次已確認的自己下注到房間結算後，立即經 round_export.Collector 轉換、完整 round-trip、金額驗證，先保存 session 原始表示，再原子發布 math/<單號>.json。
5. 關閉本次專用視窗與 server 後，執行 finish_capture.py 作重驗／補轉／彙整；即時輸出使用同一 exporter，不依賴 finish 才首次輸出。

原始 frames.jsonl、verified_decoded.jsonl、math_wire/、math_export/、錯誤及 Chrome profile 留在 webcap/<session>/，不進版本控制。已被機率修改的同單號不覆蓋，原始結果保留並記錄 math_conflicts.jsonl。

首次載入會從真站補靜態資產，可能停留在 JILI Logo；先查 capture.log。服務只聽 127.0.0.1:8200。重啟只關本款已記錄 PID，重新取 URL／建立新 session；必要時 open_capture.py --profile <舊session/chrome-profile> 可沿用操作人員的瀏覽器設定檔。每次登入不混用 session，流程不會 pkill 其他 Chrome。

## WebP 全專案批次驗證（2026-11-09）

現行版本已辨識的 WebP 180/180 檔通過格式、尺寸及 loopback HTTP 驗證。含保留歷史版本的完整目標為 180/180。詳見本款 texture_validation.json 與根目錄 artifacts/texture_webp_batch_20261109.json。 未覆蓋的 import packs／binary packs 分別為 2/6，仍列在報告；尚未做 Windows 實機完整畫面驗收。

## Git checkout / local-only files

Login config, authenticated captures, current_session pointers, profiles, logs and ZIPs are local-only. Original archive members and archive_manifest.json are tracked; replay reconstructs its ZIP load bundles locally. Install root npm dependencies and `npm ci --prefix games/545/runtime` before original-codec checks. See the root README for setup.
