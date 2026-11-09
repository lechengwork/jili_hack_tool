# Pappu／JILI 200：離線 replay

在專案根目錄執行：

```sh
.venv/bin/python -B replay_200.py
```

會啟動本機 8201 服務及 Pappu 專用 Chrome。關閉這個專用 Chrome 後，本次 launcher 也會收掉 server。不要再開擷取程序；不需要 VPN、sudo、改 hosts、真帳號或登入 token。此啟動器目前為 Mac Chrome 版。

頁面右上會標示「Pappu 本地重播・模擬餘額」。URL 裡的 local-replay-200 是合成識別，不是真站憑證。原站 hostname 只供原始前端相容；專用 Chrome 的 DNS 全導向 127.0.0.1:8201，API／WebSocket／動態資源被改送同一本機 HTTP origin，沒有上游補抓。正常保留瀏覽器憑證檢查。

## 內容與節奏

- 循環六局已驗的原始圖案與回收表，不使用尚未填寫的正式 Go 機率設定，也不把六局的出現頻率宣稱為 RTP。
- 還原登入初始化、選房、同步、7 秒下注期、下注回應、撤銷差額、統一結算、路單及下一局。實包下注約 7.5 秒，重播使用 7.6 秒；結果後保留 16 秒供前端演出。
- 本地起始餘額為 3,000,000 IDR；加注立即扣模擬餘額，撤銷退回，結算只加入當前下注應得的含本金回收。原始帳號的 postCoin 不套用到本地新下注。
- 可以依自己的本地下注測圖案；回收 = 中獎區實際下注 × 該區 return_odds。沒下注也會開獎，回收是 0。
- 可使用原介面的續押／自動／雙倍／清除；math 模式與 wire 模式均用同一組本地下注／錢包規則。超過餘額、下注期結束、負數最終下注或單區超過本地 4,000,000 限制會拒絕。
- 所有原站可選房號共用這個離線資料池與模擬規則，不宣稱已重現每個真房間的限紅或多帳號共桌。每個本地 WebSocket 為隔離的測試玩家。

## 調整 math 並立即看結果

預設每局結算前重讀 games/200/math/<原始單號>.json，主要控制 winner、pic、return_odds。單號、幣別與十二格順序須合法；只接受已建立規則的普通單圖案結果。replay/server.log 及本機 /__replay_status 會列 source_round，方便知道這局用了哪個檔。

JSON 的 bets／total_win／net_win 是原始參考局的資料，仍必須內部一致；replay 回前端時會改用這次實際下注重算回收及餘額，不將參考贏分強塞到不同下注。修改 winner／return_odds 後，可用 helper 重算原局衍生欄位：

```sh
.venv/bin/python -B games/200/recalculate_math.py games/200/math/644919241425842376.json --winner 2 --write
```

也可加 --odds，提供完整十二個逗號分隔的含本金回收值。0 正規化成基礎 10；20 代表總回收 20 倍，不再加本金或乘基礎賠率。實際 --write 會改這份機率 JSON；原始捕獲的工程表示仍留在原 session。

只看某一局以便反覆調整：

```sh
.venv/bin/python -B replay_200.py --rounds 644919241425842376
```

測試其他資料夾、避免動到機率的正式調整檔：

```sh
.venv/bin/python -B replay_200.py --math-dir /absolute/path/to/math
```

無效 JSON、未知特殊模式或金額不一致時，會暫停該測試玩家的結算並記錄錯誤，不偷偷改用舊資料。修好後重開 replay。不要修改這次實際已鎖注的數量來控制回收。

## 原始結果模式

```sh
.venv/bin/python -B replay_200.py --source wire
.venv/bin/python -B replay_200.py --balance 10000000
.venv/bin/python -B replay_200.py --no-browser
```

wire 模式從 replay_samples.json 使用原始結果，忽略 math 檔變動；仍依本次本地下注計算回收與模擬餘額。replay_samples.json 的初始化身分、SSO 已合成化，執行時不讀 webcap、capture_config.local.json 或金鑰。準備腳本 build_replay_samples.py 才讀本機原始擷取，不是執行 replay 的必要步驟。

## 資產與周邊服務

公開靜態資產在本款 static/。原始腳本存在檢查會觸及的 247 個 9926e 資產，依版本清單的 UUID、腳本內的實際檔名／副檔名與已驗證原始共用 payload 補齊；來源 SHA256 見 replay_asset_sources.json。另有三個 manifest 名稱在目前腳本未找到對應 literal 檢查，沒有猜副檔名或任意製造 200 回應。

只在離線頁面停用 TIP 側欄；原始活動頁若出現，保留其 OnClose 回呼流程自動關閉。沒有活動服務、真排行榜或真玩家；缺少的虛擬頭像使用本機已快取的 46 號圖。未登記資產仍回 404，server 不連真站補抓。

## 驗證

```sh
.venv/bin/python -B games/200/verify_replay.py --source math
.venv/bin/python -B games/200/verify_replay.py --source wire
```

涵蓋六局兩輪循環、合成初始化、加注／撤銷／清除／重送、鎖注與零下注結果、當前下注餘額、修改 math 後熱載入、錯誤 JSON 拒絕、真實 masked WebSocket 往返及 247 資產雜湊。後端報告為 replay_validation_math.json／replay_validation_wire.json；瀏覽器使用者確認與長時間本地循環另記 replay_browser_validation.json，不混為後端測試結論。

## Windows 貼圖檢查

Mac 會選 ASTC；不支援 ASTC 的裝置會依原始 Cocos ImageAsset metadata 選 WebP。不能只複製 Mac 當次載入的貼圖。已補齊本款可用 import packs 宣告的 WebP 與所有已抓 ASTC 的 WebP 對應檔；逐檔來源 URL、SHA256、尺寸及覆蓋範圍見 `texture_validation.json`。這是貼圖與 HTTP 檢查，Windows 實機畫面仍須由 QA 驗證。

啟動 replay server 會先做離線檢查，缺檔／偽裝格式／尺寸不符就停止；不會執行中連真站補檔。驗證程式也逐張透過本機 HTTP 檢查 200、image/webp、檔案 hash。

```sh
.venv/bin/python -B routex/texture_variants.py games/200/static --report games/200/texture_validation.json
# 準備資源時才執行，需要連原站；不需登入 token，不下載遊戲 API 資料
.venv/bin/python -B routex/texture_variants.py games/200/static --fetch --report games/200/texture_validation.json
```

工具可對其他款的 `games/<ID>/static` 重用；`unavailable_import_packs` 明列尚未擷取的 pack，`binary_import_packs` 明列本工具未解碼的二進位 pack，報告不代表所有未載入內容已完整備份。
