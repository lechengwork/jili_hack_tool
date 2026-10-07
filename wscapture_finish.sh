#!/usr/bin/env bash
# wscapture_finish.sh — 收工:把 wscapture.sh 側錄的 WS frame 解成每局 JSON。Mac。
# 以遊戲號分派解碼器:124=ws_math_view, 94=ws_rummy_view。對應 Windows wscapture_finish.ps1。
# 用法: ./wscapture_finish.sh [124|94]   (遊戲可先不關;中止整個 capture 用 kill <server pid>)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
GID="${1:-124}"
PY="${PY:-$ROOT/.venv/bin/python3}"; [ -x "$PY" ] || PY="python3"
SRC="${SRC:-games/$GID/webcap_ws.jsonl}"
MATH_OUT="${MATH_OUT:-games/$GID/math}"

[ -f "$SRC" ] || { echo "✗ 找不到側錄 $SRC — wscapture.sh $GID 有跑、且 server 有印 [ws] 嗎?"; exit 1; }
N=$(wc -l < "$SRC" | tr -d ' ')
echo "側錄 $N 筆 WS frame → 解碼(遊戲 $GID)→ $MATH_OUT/ …"
case "$GID" in
  124) "$PY" ws_math_view.py  --src "$SRC" --out "$MATH_OUT" ;;
  94)  "$PY" ws_rummy_view.py "$GID" --src "$SRC" --out "$MATH_OUT" ;;
  736) "$PY" ws_fish736_view.py "$GID" --src "$SRC" --out "$MATH_OUT" ;;
  *)   echo "✗ 未登記的遊戲號 $GID(支援:124/94/736)"; exit 1 ;;
esac
echo "✅ 完成。給機率的檔在 $MATH_OUT/(每局 <round_id>.json + all.jsonl)。"
