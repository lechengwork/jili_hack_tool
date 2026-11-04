# JILI 518 馬戲團小丑 4096 — 機率測試包

先看 `games/518/math/INTERFACE.md`，照 `games/518/math_518.proto` 產出 **SpinAck**，放在 JSON 的 `data`。
輸入是 `spinReq`，輸出是 `data`；加解密、餘額及單號由遊戲層處理。

## 包含內容

| 檔案 | 用途 |
|---|---|
| `games/518/math_518.proto` | 機率輸入／輸出；無 bytes 或加密欄位 |
| `games/518/math_518.desc` | 已編譯的 protobuf descriptor |
| `games/518/math/<單號>.json` | 151 筆實際轉局回應，完整數字欄位 |
| `games/518/math/all.jsonl` | 同一批資料，每行一筆 |
| `games/518/math/COVERAGE.json` | 樣本覆蓋、代表單號及實測值域 |
| `games/518/math_adapter.py` | 零第三方相依的雙向轉換與檢查 |
| `games/518/math/roundtrip_vectors.jsonl` | 原始明文回應測試向量，不含登入 token 或 session key |
| `replay_518.py` | 一鍵開本地 server + 專用 Chrome；可播原始樣本或修改後的 math JSON |

這是可編輯樣本的本地測試包，不是新機率結果產生器。主遊戲有 150 筆 0.3 下注樣本，另有 1 筆 0.1 下注、含觸發局與 10 回合免費遊戲的回應。不要把它當成完整玩法分佈或 RTP 模擬結果。

## 1. 先檢查格式（不用裝套件）

在解壓後的資料夾執行：

```text
python games/518/math_adapter.py --selftest
```

應顯示 151 筆原始 payload／完整遊戲信封 byte round-trip 通過，並驗證目前 math JSON 的結構及金額加總。
測試向量固定保存原始樣本；修改 math JSON 後，檢查仍會驗證原始轉換能力及修改檔的格式，不要求修改後內容等於原始樣本。

## 2. 看原始樣本演出

安裝 Python 3.9+ 和 Google Chrome。回放只需要這個第三方套件：

```text
python -m pip install -r requirements_518.txt
python replay_518.py
```

Windows 也可執行 `replay_518.cmd` 或 `replay_518.ps1`。Mac 在本專案可用 `.venv/bin/python replay_518.py`。
不用 VPN、sudo 或修改系統 hosts。這個專用 Chrome 的所有主機都映射到本機 mocker。
進入遊戲後自行轉局；不要開 DevTools。

只播指定的樣本（依列出的順序；下注要與樣本一致）：

```text
python replay_518.py --rounds 2484635253000060518,2484636245000120518
```

重播會依下注金額選用樣本。目前只支援這批樣本的 **0.3／0.1**，其他下注不會自動縮放結果。
本地餘額取自樣本，不是新錢包帳務；同樣本循環時單號會自動遞增。

## 3. 改 math JSON 看演出

1. 修改 `games/518/math/<單號>.json` 的 `data`；保持欄位、陣列位置和金額加總一致。
2. 先跑 `python games/518/math_adapter.py --selftest`。
3. 關閉上一個回放視窗，再執行：

```text
python replay_518.py --source math --rounds 2484635253000060518
```

**原始回放預設讀擷取資料；只有 `--source math` 才讀修改後的 JSON。**
修改後要重啟回放程序才會重新載入。不要同時開兩個預設 port 8519 的 server。
如果另一個測試已使用該 port，可加 `--port 8520`；程式不會強制關掉別人的程序。

不要只改 TotalWin：AwardDataVec[].Win → ComboStageWin → RoundWin → TotalWin 必須逐層加總相符。
不要把 `ComboMult` 再乘進已經填好的金額；轉換層不會代算倍率或派彩。
餘額 `postMoney` 仍保留樣本值，若想同時觀察錢包變化，請一併調整，正式服務則由遊戲層回填。

## 4. 代表樣本

| 情境 | 單號 |
|---|---|
| 未中獎 | `2484636245000120518` |
| 中獎、連消 | `2484635253000060518` |
| 一回合含 5 個階段 | `2484636837000010518` |
| 觸發局 + 10 個免費回合 | `2484645845000160518`（下注 0.1） |

## 5. 已驗證與限制

- 151 筆解密／簽章有效；原始前端 codec、獨立編譯的 protobuf codec 均能重編碼回原始 151 筆 payload。
- Python adapter 的 151 筆完整遊戲信封亦 byte 相同；金額三層加總在 219 個 stage／161 個 RoundInfo 都通過。
- 原始本地回放已在 macOS 的真實 Chrome 進場、連續轉局確認。Windows 已提供啟動器及 WebP 素材，但沒有在 Windows 主機實測。
- 已在獨立測試包將一筆贏分由 1.05 改成 2.10；`--source math` server 的實際 HTTP 回應、簽章、解密及餘額比對皆通過。金額加總不一致的修改會被擋下。
- `special.context23` 保留了原始數值，尚未定義業務名稱；這筆的 field3=4.65，與相鄰餘額推導實扣吻合，但只有一個樣本，不能推廣成所有特色玩法的成本公式。
- BuyType／AckType 在這批均為 0；其他 enum 值、旗標業務含義及更多觸發情境仍需補樣本或遊戲規則佐證。
- 可選推薦／活動服務有部分空 protobuf stub，這個包的測試範圍是 518 盤面與演出。

收工：關閉專用 Chrome；一鍵啟動器會停止自己開的 server。也可在啟動終端按 Ctrl+C。
若找不到 Chrome，設定 `CHROME` 為執行檔完整路徑。
