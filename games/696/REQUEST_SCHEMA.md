# JILI 696 /fg5/req 請求端 schema(明文 protobuf,netlog 擷取,已驗證)

所有請求共通:f1=序號(seq), f3=token(20B,整場固定), f4=client pubkey(32B,整場固定)。

## Spin 請求(核心)
f2 (msg):
- **f1 (f64) = 下注額**(如 0.3 / 100.0,驗證=玩家設定值)
- f25 (msg) = spin 選項 { f1,f2,f4 全 0 }(疑似 自動/turbo/快速 旗標)
- **f26 (msg) = 額外下注**;**有此欄位=開額外下注,f26.f1=級別**(0/省略=1.5倍, 1=8倍)。
  與回應 f23.f26 完全鏡射。無此欄位=一般 spin。

範例:
- 一般 spin(0.3):     f2{ f1=0.3, f25={0,0,0} }              → 76B → 回應 230B
- 8倍額外下注(100):  f2{ f1=100.0, f25={0,0,0}, f26={f1:1} } → 81B → 回應 238B

## 其他請求型態
- init/handshake(120B): f2={ f1:"OS X", f2:"zh-CN", f3:{chrome,151.0.0.0,zh-CN,1920,1080}, f5:"Macintosh" } → 回應 327B(遊戲設定)
- 62B: f1=seq, f2={f1:0}      (狀態/ack?)
- 67B: f1=seq, f2={f1:"zh-CN"}
- 69B: f1=seq, f2={f1:"zh-CN", f2:2}  (最常見,週期性?)
- 58B: f1=seq only            (keep-alive/ack)

## mock server 要點
- 下注額與額外下注**每把 spin 都在請求 f2 裡**(f2.f1=bet, f2.f26=ante)→ mock 直接讀,不用維護 session bet 狀態。
- token(f3)/key(f4)整場固定,握手時建立。
