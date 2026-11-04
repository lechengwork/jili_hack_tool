# 807 隨機效果／欄位證據監看

目標是補齊隨機效果的欄位定義，不以「有沒有進 Free Game」作為唯一判斷。監看的是新真站樣本；重播同一批資料不會當成新證據。

## 啟動

```sh
python3 games/807/watch_fields.py
```

以原始 `replay_samples.json` 的 2399 局為基準，自動跟隨 `current_session.txt` 指向的擷取 session。無須第三方套件。預設最多收錄 2000 個新單號後停止監看；這個上限是資料收集界線，並不表示 proto 已完整。它不會停止遊戲或 capture server。

```sh
# 不限新局數
python3 games/807/watch_fields.py --max-new-rounds 0
# 只檢查當下資料；不持續等待
python3 games/807/watch_fields.py --once
# 指定其他擷取目錄或獨立監看輸出
python3 games/807/watch_fields.py --session games/807/webcap/<session> --out /tmp/807-watch
```

同一輸出目錄有單一實例鎖，拒絕重複啟動。重啟會讀回進度與檔案 offset，不重複計算同一局；寫到一半的 JSON 行會等下一次補完才處理。基準檔變更時拒絕沿用舊 state，請另指定輸出目錄，以免混淆證據。

## 它會找什麼

- schema 沒有的新欄位／已知欄位 wire type 改變，包括巢狀欄位。
- f6/f7 的特殊符號與數值、組合及筆數的新情境。
- f8/f9 的新組合，尤其 f9 首次出現非空內容。
- f13/f17 首次出現的新非零效果槽及參數。
- 新 win_type、下注、完整 request action 或 f21 設定值。
- 已有普通轉輪倍率對照、線獎公式或派彩加總的反例。
- 現有 math adapter 拒絕或無法 byte 還原的新資料。
- 五分鐘沒有新轉局：提示檢查自動轉／側錄。心跳、餘額輪詢不當成轉局。

普通轉輪規則只在既有證據範圍內驗證；特殊效果不硬套普通公式。新值只增加證據與待查項，不自動賦予「饋贈／免費遊戲」等玩法名稱。

## 產物

全部位於忽略版控的 `games/807/monitor/`：

| 檔案 | 內容 |
|---|---|
| summary.json | 基準、新局數、特殊局數、目前狀態與待解問題 |
| events.jsonl | 事件時間、類型、單號、來源及證據路徑 |
| evidence/<單號>.json | 原始回應 payload、完整欄位樹、可解碼的 math JSON、相關事件及不含憑證的 spin action |
| state.json | 已見單號、offset、事件與範圍基準，用於重啟接續 |
| process.json | 本次監看 PID 和收集上限 |
| console.log | 背景啟動時的終端事件輸出 |

同一類事件的終端通知會限量，避免刷屏；後續證據仍持續寫檔。轉換器不認得的 payload 也完整保存，包含未知欄位 raw hex。監看產物不複製 JWT、SSO URL、請求 token、X25519 公鑰或 AES session key。

## 取得新證據的流程

1. 保持真站 capture server 與這支監看程式運行。
2. 由操作人員進遊戲、選擇模式與開啟自動轉。監看程式不會送出下注、切換模式或自動補按轉局。
3. 出現特殊事件後，依單號／時間對照實際演出；必要時記錄演出名稱或錄影。
4. 比較同一效果的多個樣本、跨模式樣本及反例，再更新欄位定義。
5. 更新 adapter／proto 後，以所有舊、新向量重新跑 byte round-trip 與獨立 protobuf 驗證，再重新打包給機率。

即使收了很多局，未出現的效果仍沒有定義證據。事件檔與終端回報不等同於聊天的背景推播，也不代表 AI 在聊天結束後仍持續自動分析。回來要求檢查監看結果時，可直接讀取上述檔案接續分析。

## 驗證

```sh
python3 games/807/test_watch_fields.py
```

測試涵蓋基準排除／去重、未知巢狀欄位原樣保存、非空 f9、非零 f17、派彩反例、未驗章回應排除、半行 JSON 與重啟接續。

## v2 接續

v2已將全部2399局納入基準。舊state基準hash不同，請指定 `--out games/807/monitor_v2` 開始新監看；不要刪除舊state冒充連續統計。
