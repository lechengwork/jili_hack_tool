# Go Rush — 平台4104／JILI224

已核對新 LoginGame 111000224 → /aviator/index.html?gameID=224，原始HTML內GameID=224；官方產品頁 https://jiligames.com/PlusIntro/224?showGame=false 。平台4104來自使用者指定。

帳號沿用專用保留 tryplayer003idr，IDR來源；不動共用config。已關VPN取新URL，再連Brazil São Paulo；獨立Chrome、8224本地collector與新webcap/session，不混用金鑰，不改hosts，不關閉憑證驗證，不開DevTools。

已由本款原始Game224/index.95fb8.js提取aviatorProto，建立math_224.proto、aviator_224.proto與雙向math_adapter.py/.cjs。math入口為math/INTERFACE.md。完整應用層frame與原始codec逐筆回編後，即時原子發布成功下注到結算的math；未知schema、零額下注、旁觀不充作成功樣本。這是明文protobuf/TLS協定，未觀察獨立應用層簽章欄位，不聲稱簽章驗證。

當前擷取程序用被動watch_live_math.py補即時輸出；下次capture_server.py直接內建相同Collector，不依賴finish。verify_math.py驗證原始完整frame、clean proto大整數、修改後反向adapter及衝突保護。finish_capture.py重驗／補轉／快照，原始封包與開發診斷保留webcap/session。初始wrapper parser游標問題已修正並全量重處理；零額settlement已改為獨立分類，排除成功math。

下注、cashout及任何瀏覽器安全警告由操作人員處理。每10分鐘由本聊天heartbeat go-rush-4104 背景檢查；僅完成或異常通知，完成後停用。

使用者已於本次遊玩結束要求收尾；在已結算且無pending下注時關閉本次專用Chrome，再停止其collector及watcher，10分鐘背景檢查已刪除。最終局數與覆蓋見final_capture_summary.json。

最終：1954筆原始frame；12局正額成功下注／12份math（雙下注區7局、單區5局；有兌現11局、未兌現損失1局）；另9局零額結算排除。117筆相關應用層frame經本款原始codec完整回編，最終錯誤0、衝突0、無殘缺尾行、無待結算下注。開發期診斷已保留且全量重處理，詳見final_capture_summary.json。

下次流程：關VPN → .venv/bin/python -B games/224/login_capture.py → capture_server.py → Brazil São Paulo確認 → open_capture.py。收尾finish_capture.py；驗證verify_math.py。

## 本地重播

在專案根目錄執行 `.venv/bin/python -B replay_224.py`。預設使用current_session.txt指定session的完整倍率軌跡（本次20261109-100032為12局，其中2局正額、10局零額），以原廠aviatorProto處理本地下注與兌現；餘額及本次派付為模擬計算，不能當作新增真站math樣本。重播不寫入math，不改原始capture。

服務只聽127.0.0.1:8225，專用Chrome所有host導向loopback；本地HTTP頁面將API與WebSocket導向同一個本地origin，保留瀏覽器憑證驗證，使用本地假SSO、不讀取真站一次性URL。右上角標示「本地重播 · 模擬餘額」。素材使用本款static與既有Game224原始zip；字型缺漏以相同5468e MD5版本的原始payload補齊。

原始前端的假玩家、初始24筆模擬歷史仍依原碼顯示；排行榜使用該session已驗證的原始RankBoard回應。每個WebSocket連線各自從第一份快照開始，每次查詢依序前進，最後一份持續保留；原始日期、帳號名稱、金額與倍率不改寫。本地模擬下注／兌現不插入已錄排行榜。倍率軌跡是已錄製資料，下注金額、手動／自動兌現與餘額則由本地server計算，因此不是逐byte固定播放原始現金流。記錄及PID位於忽略版控的replay/與replay.log。

已驗證原廠前端完成本地SSO／WebSocket初始化，連續重播並收到雙下注區的手動兌現。僅在本地模擬範圍驗證，不代表真站或新機率模型的驗收。

2026-11-09 排行榜／各頁補抓：新登入、新session、新Chrome profile。capture_server.py另載入capture_http_shim.js，被動保存JILI API的HTTP請求與回應到本次session/http_exchanges.jsonl，保持原始請求目標；JSON responseType若無原始text，明確標為json-reserialized，不宣稱其byte roundtrip。WebSocket主排行榜RECV14使用本款RankBoard codec完整frame回編，成功寫rank_verified.jsonl，失敗保留原始frames並寫rank_errors.jsonl。原始帳號／登入資訊只留忽略版控的session。當前聊天heartbeat go-rush每10分鐘檢查，使用者完成後收尾刪除。

2026-11-09 補抓已關閉：1201筆WS frame，2局成功math、10局零額排除，來源wallet確定IDR/Rp。逐局原始codec、完整frame回編、clean proto、修改後雙向adapter與原子衝突保護重驗通過；錯誤0、衝突0、無殘缺尾行。5筆原生RankBoard回應皆完整byte round-trip，當日日榜押200000／回收328000／rate1.64與本帳號新結算相符；月榜11筆均可對上2026-11-06的11筆有回收紀錄。全部榜單條目都是本帳號，未取得外部帳號樣本；月榜在這次快照中未納入新贏局，刷新／保留政策未確認。通用活動排行榜HTTP回覆ranking not exist or begin，不和遊戲內WS榜單混為一談。

公平性：用使用者截圖揭露的48字元server seed做UTF-8 SHA-256，精確對上單號645352646659592416下注前的Info.serverHash。截圖19b6efa7轉十進位431419303正確；候選公式0.97*(2^32-1)/(N+1)與該局9.656772975902811x相差約1.8e-15。此公式僅為單樣本推導，尚未確認原廠完整雜湊算法、輸入順序、截取規則、上下限與一般RTP，不能宣稱公平性全鏈已通過。截圖中的押注2 100000／1.6x／160000與本局第2區兌現一致。

擷取缺口：主頁HTTP hook沒有保存完整歷史／公平性子頁回應，尚缺全部參與的client seeds、完整combined hash和算法。應先補子頁／新視窗的網路側錄，查兩筆既有紀錄（含低倍率），毋須為查看舊紀錄而再下注。多人共用墜落結果、榜單範圍仍需第二個已授權帳號同時比對。詳見analysis/rank_fairness_validation.json；重驗本次固定證據用 `.venv/bin/python -B games/224/analysis/verify_rank_fairness.py`。截圖及種子轉錄只留忽略版控的session/evidence。背景檢查go-rush已刪除。

兩場彙整為capture_sessions_summary.json：合計14份成功math，原始session保持獨立。

本次排行榜replay更新已用5份原始回應驗證：查詢命令SEND12回覆RECV14；每份皆由原廠codec完整frame回編後逐byte發送，7次連續查詢確認末份保持、不同連線各自從首份開始。首份日榜空，末份日榜押200000／回收328000／1.64x，月榜兩類各11筆。驗證結果見analysis/replay_rank_validation.json。

### 2026-11-09 歷史子頁已接入

`webcap/20261109-105609/history_netlog/` 保存 71 個原始 HTTP entity 及 SHA256；含歷史列表 3 局、3 份單局明細、3 份公平性步驟。所有原始 URL、token、NetLog 僅留 ignored session，replay `/v2/token` 只回本地 mock JWT。

`history_replay.py` 服務原始 Nuxt 頁面、動態 chunks、字型及已擷取 API。遊戲內歷史入口、列表、單局明細、「驗證」公平性頁均可本地瀏覽；歷史為擷取快照，replay 模擬下注不會新增真站歷史。只擷取到第一頁，其後頁回空；未擷取明細／seed 組合會明確回 404，不能冒充已有資料。

重新驗證：`.venv/bin/python -B games/224/analysis/verify_history.py`。結果見 `analysis/history_validation.json`：三局金額、雙區兌現、SHA256 事前承諾、`SHA512(UTF8(ServerSeed + ClientSeed1 + ClientSeed2 + ClientSeed3))`、前 8 hex 整數及 `(2^32-1)/(N+1)*(1-0.03)` 均吻合，顯示值為向下截取兩位。此新報告補足較早 `rank_fairness_validation.json` 中「缺完整公平性回應」的缺口；舊報告保留原當時證據範圍。仍未證明邊界截斷／完整分布與RTP，亦未證明 client seed 2/3 來自真人或跨帳號共局。

本次另外 2 筆成功下注已即時輸出並重驗完整原始 codec byte round-trip（錯誤 0、衝突 0）；總成功 math 現有 16 筆。新 replay 保留前次已驗證 5 份原生排行榜快照。

2026-11-09 歷史清單入口修正：mock SSO 的 `profile.subAgentCode` 必須沿用此 Go Rush 擷取的 `2`。原先借用通用 SSO 的 `1` 導致遊戲內請求未擷取的 `/v2/game-entrance/1778/7/1/0`，而獨立測試 URL 使用 `sac=2` 因此漏掉差異。已改為 `2`，並加入歷史 API 狀態記錄。

## WebP 全專案批次驗證（2026-11-09）

現行版本已辨識的 WebP 86/86 檔通過格式、尺寸及 loopback HTTP 驗證。含保留歷史版本的完整目標為 86/86。詳見本款 texture_validation.json 與根目錄 artifacts/texture_webp_batch_20261109.json。 未覆蓋的 import packs／binary packs 分別為 0/0，仍列在報告；尚未做 Windows 實機完整畫面驗收。

## Git checkout / local-only files

Login config, authenticated captures, current_session pointers, profiles, logs and ZIPs are local-only. Original archive members and archive_manifest.json are tracked; replay reconstructs its ZIP load bundles locally. Install root npm dependencies and `npm ci --prefix games/545/runtime` before original-codec checks. See the root README for setup.

The default replay now reads sanitized replay_data (application messages and history response fixtures), not current_session.txt or replay_source.local.json. Raw NetLogs, authenticated login requests, token responses and original URL/headers remain excluded. Run `analysis/verify_history.py --offline` to recheck the included three completed-round fairness examples.
