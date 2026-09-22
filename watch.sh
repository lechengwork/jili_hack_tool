#!/usr/bin/env bash
# watch.sh — 盯擷取進度,只在「我會採取行動」的事情發生時吐一行。達標就退出。
#
#   ./watch.sh            # 預設目標:饋贈樣本 5 局
#   GIFT_TARGET=10 ./watch.sh
#   INTERVAL=60 ./watch.sh
#
# 這支是設計來給 Claude 的 Monitor 工具掛的(每行 stdout = 一則通知),
# 但你自己在終端跑也一樣看得懂。設計理由見 WATCH_PATTERN.md。
set -u
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=./.venv/bin/python
TARGET="${GIFT_TARGET:-5}"
INTERVAL="${INTERVAL:-30}"
STALL="${STALL:-180}"          # 側錄幾秒沒動就算斷線
HB="${HB:-250}"                # 每 +N 局報一次心跳

prev_gift=-1; prev_bad=0; prev_unk=0; stalled=0; hb_total=0
while true; do
  line=$($PY watch_state.py 2>/dev/null) || { sleep "$INTERVAL"; continue; }
  IFS='|' read -r total gift bad unk age vals <<< "$line"
  [ -z "${total:-}" ] && { sleep "$INTERVAL"; continue; }
  if [ "$prev_gift" -lt 0 ]; then prev_gift=$gift; hb_total=$total; fi

  # ① 要的東西:饋贈樣本增加
  if [ "$gift" -gt "$prev_gift" ]; then
    echo "★饋贈樣本 $prev_gift → $gift / $TARGET  (總局 $total)"
    echo "$vals" | tr ';' '\n' | tail -n $((gift - prev_gift)) | sed 's/^/   /'
    prev_gift=$gift
  fi

  # ② 壞消息:沉默不等於正常,一定要吵
  if [ "$bad" -gt "$prev_bad" ]; then
    echo "✗★倍率規則出現反例★ $bad 局 —— 規則要重解"; prev_bad=$bad
  fi
  if [ "$unk" -gt "$prev_unk" ]; then
    echo "✗★封包出現沒解到的欄位★ $unk 種 —— 跑全欄位掃描,而且 adapter 可能正在掉資料"; prev_unk=$unk
  fi

  # ③ 側錄斷線:這是最容易被誤判成「一切正常」的失敗
  if [ "$age" -gt "$STALL" ] && [ "$stalled" -eq 0 ]; then
    echo "⚠★側錄停了★ 最後一筆 $((age/60)) 分鐘前 —— 現在轉的都沒被錄到(總局停在 $total)"
    stalled=1
  elif [ "$age" -le 90 ] && [ "$stalled" -eq 1 ]; then
    echo "● 側錄恢復(總局 $total)"; stalled=0
  fi

  # ④ 心跳:免得看起來像死掉
  if [ $((total - hb_total)) -ge "$HB" ]; then
    echo "… 進度 總局 $total / 饋贈 $gift / 規則 $bad 反例 / 側錄 ${age}s 前"; hb_total=$total
  fi

  # ⑤ 達標就退出 —— 監看結束
  if [ "$gift" -ge "$TARGET" ]; then
    echo "★★達成★★ 饋贈樣本 $gift 局。總局 ${total}。"
    echo "$vals" | tr ';' '\n' | sed 's/^/   /'
    exit 0
  fi
  sleep "$INTERVAL"
done
