# 807 Fortune Garuda 1000 / INR

2026-11-04 機率交接版v2：2,399局已併入proto／adapter／mock，完整byte與獨立protobuf驗證通過。操作入口：

- 真站擷取、監看與接續：`HANDOFF.md`
- 機率數字介面、ABI變更、欄位定義及限制：`math/INTERFACE.md`
- 離線回放：根目錄 `README_ForMath_807.md`、`replay_807.py`
- 遊戲規則來源：`RULES_807.md`
- 696欄位比較：`696_807_FIELD_MAP.md`
- 實際演出與畫面證據：`handoff/`

807 API game_id為111000807、入口/fg1000/，不能直接套用696 adapter。f17索引2與f9非空內文尚無案例，不宣稱完整覆蓋。

## WebP 全專案批次驗證（2026-11-09）

現行版本已辨識的 WebP 126/126 檔通過格式、尺寸及 loopback HTTP 驗證。含保留歷史版本的完整目標為 127/130。詳見本款 texture_validation.json 與根目錄 artifacts/texture_webp_batch_20261109.json。 歷史 config 引用的 3 個舊檔已無原站來源，保留為明確缺口；不影響本款現行 versions.json 的驗證結果。 未覆蓋的 import packs／binary packs 分別為 2/0，仍列在報告；尚未做 Windows 實機完整畫面驗收。
