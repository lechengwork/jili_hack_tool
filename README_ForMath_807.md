# JILI 807 Fortune Garuda 1000 — 機率測試包 v2

2026-11-04：已併入2,399局、普通／1.5×／8×模式、f14/f15/f16/f22、BetInfo f26，以及f9重複空訊息。請先讀 `games/807/math/INTERFACE.md`，尤其 v1→v2 的 f9 與模式輸入 ABI 變更。

## 啟動

```
python -m pip install -r requirements_807.txt
python games/807/math_adapter.py --selftest
python replay_807.py
# 修改 math JSON 後播放指定局：
python replay_807.py --source math --rounds 2486007347000260807
```

Windows可用 `replay_807.cmd` 或 `.ps1`。需Chrome，可用CHROME環境變數指定路徑。專用Chrome所有主機導向本機127.0.0.1:8808，不需VPN或真站Token；用 `--port 8810` 改port。前端須選擇樣本對應的基本下注與模式，不支援的完整action回400。

## 內容與驗證

- 2,399局數字JSON、完整wire向量、編譯proto／descriptor與零相依adapter；全部byte round-trip與獨立Google protobuf核對通過。
- 基本下注1.0／3.0，共五個捕獲action。普通1,475局、1.5× 423局、8× 501局，316局中獎、2,083局零贏分。
- wire與math回放依完整action／模式分池；HTTPS加密、簽章、餘額查詢、循環和客戶端隔離由自動測試驗證。
- 修改JSON倍率5→2、派彩10.5→4.2的加密HTTP回放與非法資料拒絕測試。
- `games/807/handoff/` 有使用者逐局演出註記、截圖、欄位定義證據與停止檢查點。規則、696比較見同層文件。

```
python replay_807.py --selftest
python games/807/verify_mock.py --source math
python games/807/verify_math.py
```

mock為樣本回放，餘額沿用樣本結算值，不是持續下注帳本或正式結果產生器。VIP等周邊服務為空stub。舊版Mac wire前端曾由使用者確認進場連轉正常；v2全模式已做協定測試，尚待前端逐種演出驗收，Windows尚未實機驗證。

## 未覆蓋範圍

f17索引2未出現非零案例；f9已見0／1／2筆空訊息，未見非空內文，不臆造其內容。其餘效果參數的證據程度見INTERFACE與handoff。數量與樣本頻率不能作為正式RTP或完整概率分布。

接手真站擷取看 `games/807/HANDOFF.md`。ZIP僅供離線回放；真站擷取工具與監看在Git專案。不含真站JWT、SSO登入入口、擷取session key；本地mock金鑰僅用於本機測試。
