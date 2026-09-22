# 696 行為覆蓋清單
遊戲無「免費遊戲」獨立畫面;特色=倍率轉輪 + EX NUDGE + 兩級額外下注,全在 base game。

已抓到並對應欄位:
- [x] base spin 中獎        (f3/f13=win, f6[]=線)
- [x] base spin 沒中        (win 欄位省略)
- [x] 1.5倍額外下注         (f23.f26={})
- [x] 8倍額外下注           (f23.f26={f1:1})
- [x] 倍率套用中獎          (f1.f12=倍率;20x 已驗證)
- [x] type:2 餘額更新
建議再補(非必要):
- [ ] EX 符號「明確 nudge 動畫那把」對 f8/f19 逐 byte(想精確還原 nudge 位置才需要)
- [x] 明文請求端 schema(netlog 擷取完成:bet=f2.f1, ante=f2.f26;見 REQUEST_SCHEMA.md)
