#!/usr/bin/env bash
# webcapture_finish.sh — 收工:把 webcapture.sh 側錄的原始封包批次離線解密 → 每一局的 JSON。
# 用現有的 decrypt_capture.py(免 Frida、免重跑遊戲)。輸出隔離在 games/<GID>/webcap/,不動 mock 的檔。
#
# 前置:./webcapture.sh 已跑過、你轉了 N 局(server 視窗有 ★ [capture] …)、key 已寫 /tmp/jili_grab.json。
# 用法:./webcapture_finish.sh [696]   (遊戲可以先不關;要中止整個 capture 用 ./stop.sh)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
GID="${1:-696}"
JSONL="games/$GID/webcap_exchanges.jsonl"
ARR="games/$GID/webcap/fg5_exchanges.json"
OUTDIR="games/$GID/webcap"
GRAB="${GRAB:-/tmp/jili_grab.json}"
GRV="games/$GID/webcap_grv.jsonl"

[ -f "$JSONL" ] || { echo "✗ 找不到 $JSONL — webcapture.sh 有跑、且真的轉過幾局嗎?(server 視窗要有 ★ [capture])"; exit 1; }

# 選 key 來源:① server 從 wasm 記憶體撈到的 shared(/tmp/jili_grab.json,首選)
#            ② 退路:getRandomValues 側錄的私鑰候選(webcap_grv.jsonl)→ 用 f4 反查
KEYARGS=""
if [ -f "$GRAB" ] && "$PY" -c "import json,sys;sys.exit(0 if json.load(open('$GRAB')).get('key') else 1)" 2>/dev/null; then
  echo "key 來源:記憶體 shared($GRAB) ✓"
  KEYARGS="--grab $GRAB"
elif [ -f "$GRV" ]; then
  echo "key 來源:getRandomValues 私鑰候選($GRV,$(wc -l < "$GRV" | tr -d ' ') 筆)→ 用 f4 反查 ✓"
  KEYARGS="--grv ../$GRV"
else
  echo "✗ 沒有可用 key:記憶體沒撈到(server 無『+KEY』)且 getRandomValues 也沒側錄到($GRV 不存在)。"
  echo "  把 server 視窗的 ★★★ [shim-report] 幾行(mem#… anchor=… / grv#… / KEYMISS)貼給 Claude 判斷。"
  exit 1
fi

N=$(wc -l < "$JSONL" | tr -d ' ')
echo "① 側錄了 $N 筆 /fg5/req exchanges → 轉成 decrypt_capture 吃的 JSON 陣列…"
mkdir -p "$OUTDIR"
"$PY" -c "
import json,sys
rows=[json.loads(l) for l in open('$JSONL') if l.strip()]
rows.sort(key=lambda r: r.get('seq') or 0)   # 依 shim 的 seq 還原順序
json.dump(rows, open('$ARR','w'))
print('   ->', '$ARR', len(rows),'筆')
"

echo "② 批次解密(每筆一行 decoded JSON)…"
( cd routex && ../.venv/bin/python decrypt_capture.py \
    --exchanges "../$ARR" $KEYARGS \
    --out "../$OUTDIR/responses.jsonl" )

echo
echo "③ 套語意標籤 → 可讀 JSON(餘額/下注/中獎/單號/盤面/中獎線…)…"
"$PY" webcap_pretty.py "$GID"

echo
echo "④ 匯出後端【原封不動】封包(給機率/數學:未改名、未丟欄位、未自算)…"
"$PY" webcap_backend_raw.py "$GID" --grab "$GRAB"

echo
echo "⑤ 轉成【機率團隊介面】(math_696.proto 形狀:全 int、沒有 bytes、沒有密文欄位)…"
# 與 webcapture.sh 一致:MATH_OUT 決定寫去哪,沒設就用預設。兩邊一定要同一個目錄,
# 不然擷取當下即時落的檔和收工重產的檔會散在兩處。
MATH_DIR="${MATH_OUT:-games/$GID/math}"
echo "   輸出目錄:$MATH_DIR"
"$PY" webcap_math_view.py "$GID" --exch-raw "$OUTDIR/exchanges_ordered.jsonl" --out "$MATH_DIR"
"$PY" math_adapter.py --selftest || echo "   ⚠ round-trip 自我驗證沒過 — 別把樣本發出去,先找 Claude"

echo
echo "✅ 完成。給同事看的檔:"
echo "   • $MATH_DIR/*.json          ← ★★★給機率:輸入 spinReq / 輸出 data,照 games/$GID/math_696.proto 填"
echo "   • games/$GID/math/INTERFACE.md     ← ★★★給機率:欄位表+實測依據+實扣倍率(算 RTP 必看)"
echo "   • $OUTDIR/backend_raw/spins/*.json ← (工程用)後端原封不動封包(payload_hex=SpinResult=重播單位)"
echo "   • $OUTDIR/backend_raw/backend_raw.jsonl ← 全回應各一筆(含 wire/plaintext/payload 三層 hex)"
echo "   • $OUTDIR/pretty.jsonl             ← 可讀格式(每筆一行,欄位有語意:round_id/balance/total_win/base_bet/ante/multiplier/board/reels/paylines)"
echo "   • $OUTDIR/exchanges_ordered.jsonl  ← 原始 decoded(通用 protobuf 傾印 f1/f8/f12…,對照/除錯用)"
echo "   • $OUTDIR/responses.jsonl          ← 每個 type 各一筆樣本(去重)"
echo "   機率看 games/$GID/math/INTERFACE.md;線路層欄位定義見 games/$GID/fg5_696.proto 與 GAME_FORMAT_SPEC.md。"
