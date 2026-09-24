# JILI 124 (7up7down / Extra Pay) — 機率團隊介面

每局一個 `<round_id>.json`;`all.jsonl` 每局一行;`EXTRA_SUMMARY.json` 是 extra 彙總。
本檔只列介面,完整實測定案(公式 29/29 驗過、position 對照的坑)看 `games/124/EXTRA_MULT.md`。

## 一句話
`extra` = 每局隨機灑在 13 個注區的【額外倍率】,乘在該格顯示賠率上,**跟骰子/下注都無關**,開獎才回。
沒蓋的格子 `extra=1`。實測值域 `{1,2,5,10}`(截圖佐證至少還有 3,樣本沒抽到而已)。

## 每局欄位(全畫面順序、含本金賠率)
```
round_id            局號(單調遞增)
dice=[die1,die2]    兩顆骰(1..6)          sum=die1+die2
total_win           本局總贏(封包值)      bet_total  本局總下注
balance             開獎後餘額
extra_row_screen[13] 這局 13 格的 extra 快照(畫面順序,給你快速掃)
won_idx_screen      本局中獎格(畫面順序 idx)
positions[13]       每格明細:
   idx name         畫面順序 0..12 / 注區名
   base_odds        含本金基礎賠率(押1拿回 base_odds)
   extra            這局這格的額外倍率(1=無)
   final_odds       含本金最終賠率 = (base_odds-1)×extra + 1
   bet won win      這局你在這格下的注 / 是否中 / 賠付(=bet×final_odds)
```
`_check` 是本工具自檢欄位(calc_win/win_match…),不是規格,可忽略。

## 畫面順序 ↔ 封包順序(★只有前兩格互換,其餘 11 格相同★)
```
畫面 idx : 0=小(2-6) 1=和(7) 2=大(8-12) 3=點數2 4=點數3 … 12=點數12
封包 pos : 1         0       2          3       4          … 12
```
畫面序含本金賠率 = [2,5,2,27,13,9,7,6,6,7,9,13,27]。
漏掉互換 → 只有「押7」和「押2-6」會錯(互拿對方賠率),平常測不出來,要專門測這兩格。

## 你要設計的其實是「每格的 E[extra]」
每格 RTP = 命中率 ×(base顯示 × E[extra] + 1)。各格命中率不同、base 不同,
**extra 機率不能各格一視同仁**(否則「和」那格會 >100%)。細節與各格目標 E[extra] 表見 EXTRA_MULT.md。
`EXTRA_SUMMARY.json` 已用實際擷取局數算好每格的 extra 出現次數與 E[extra],直接拿來對。
