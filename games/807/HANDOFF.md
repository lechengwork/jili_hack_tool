# 807 INR 擷取交接 — 2026-11-04

專案：lechengwork/jili_hack_tool。來源Mac工作目錄 `/Users/dyson/Downloads/jili_hack_tool`；接手者可clone到自己的目錄。已停止所有807擷取／監看，現在不會繼續下注。

## 接手前準備

Python與Chrome；安裝 `cryptography requests`。重新編譯proto另外需要grpcio-tools（本次1.80.0／protobuf6.33.6）。

`login_config.example.json` 只有設定範例。將login設定及login_accounts.inr合併至本機根目錄config.json，填自己的INR agent JWT、player ID；不要提交真Token。現有config.json屬歷史追蹤檔，尤其不要git add它。帳號權限／餘額由平台管理。

LoginGame須在可用出口先取得新入口，本次台灣出口成功、巴西曾回403；取入口後再連Brazil/São Paulo。VPN由接手者自行操作。

```
python jili_login.py 807 --account inr --json > games/807/login_session.local.json
chmod 600 games/807/login_session.local.json
python games/807/refresh_assets.py
python -B -u games/807/capture_server.py
```

另一終端：

```
python -B -u games/807/open_capture.py --seconds 43200
python games/807/watch_fields.py --max-new-rounds 0 --out games/807/monitor_v2
```

open_capture目前啟動器為macOS Chrome固定路徑。Windows擷取需適配該啟動器；離線mock已有跨平台Chrome查找。伺服器127.0.0.1:8807使用專用Chrome的主機解析，API仍走真站，不修改系統hosts。hook預檢通過才開視窗。所有轉局／切換模式由操作人員自行操作，監看只被動讀檔。

v2的基準已含2399局；**不要沿用v1監看state**，必須使用新的monitor_v2輸出。預設monitor亦可用於全新clone；--out範例避免原Mac舊state的基準hash衝突。

## 收尾

先停止專用遊戲視窗與capture server，待監看讀完最後記錄後Ctrl+C停止；不要停止其他Chrome或不相關服務。

```
python games/807/finish_capture.py
```

各次工作階段在current_session.txt及webcap/，不可混用金鑰。收尾重驗簽章並解密export；匯入新樣本前先清除請求憑證，只保留action/type/ret/應用層payload。修改schema後重新編譯並驗證所有舊新局，不可靜默丟棄未知欄位。

## 已收資料與下一個目標

2,399局：初版241、11/3上午1452、下午706。全部簽章驗證通過，資料在replay_samples.json與math/；原始網路請求／GRV／金鑰未上傳。handoff保存已去除憑證的逐局演出註記及原圖，附停止檢查點。

f17索引2仍未出現；f9雖有重複兩筆，但內容皆空。8×有升級成功案例，可作有限批次收集選擇，不能保證未見欄位一定會出現。跨模式、自然Ex Nudge、交換成功／失敗、升級、主軸重轉與SuperWild多次抽取已有案例。

最後一筆失敗回覆type0/ret304、簽章有效，訊息single wallet process error。這是後端錢包處理錯誤，不足以斷言跑太久、session過期或本地網路問題。重新取得登入入口；若再出現應記錄單號／時間交平台查錢包處理。

離線包重建：`python build_807_math_package.py`，會執行staged獨立測試與憑證掃描，產出jili_807_math_test_20261104.zip。
