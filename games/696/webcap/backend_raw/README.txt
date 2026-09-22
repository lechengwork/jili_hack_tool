這批是後端原封不動的封包(只做了不可避免的 AES 解密),沒有任何改名/推導。
每筆三層:
  response_wire_hex = 線上實際 bytes(加密:sig64‖nonce12‖ct+tag)
  plaintext_hex     = 解密後完整 Envelope(f3=type f5=data f6=err f7=ret,+f1=server時間戳)
  payload_hex       = Envelope.f5 = 遊戲負載(spin=SpinResult),對應 fg5_696.proto
                      ★這一層就是重播單位:server.py make_response(data=payload) 會自己補外層+重新加密
  payload_decoded   = payload 的忠實 protobuf 傾印(field 編號+wire,零改名零推導)
  payload_named     = 套 fg5_696.proto 名字的可讀解讀(★我們逆向的解讀,非封包原生;
                      未知欄位保留 f<N>;proto 部分欄位標「待確認」;ground truth 仍是 payload_hex)

對照:spins/*.json、pretty.jsonl 是 webcap_pretty.py 的「可讀視圖」——會改名/丟欄位/自算欄位,
     機率/RTP 請以本目錄的 payload_hex + payload_decoded + fg5_696.proto 為準。
