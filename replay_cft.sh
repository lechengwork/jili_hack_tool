#!/usr/bin/env bash
# replay_cft.sh — 舊 build 696 重播,繞過 date-lock + MSG 8 校時(免 sudo / 免改 hosts / 免密碼)。
#
# 原理(2026-09-29 破)：
#  1) 舊 build 一個月後觸發 Jscrambler date-lock + 遊戲內 MSG 8 校時。純 JS 撥 Date 會被 self-defending
#     判 GameDebugging;凍結/放慢又被判「時鐘沒走」。
#  2) 解法 = libfaketime 從 OS 層把「真實 native 時鐘」整體往回撥(偵測不到),用 Chrome for Testing
#     (非 hardened,吃 DYLD 注入)。用【偏移模式 -18d】→ server 與 client 用同一系統時鐘算,兩邊零時差。
#  3) MSG 8 比對的是【重播回應內層那個卡在擷取時刻的死時戳】。server 開 REPLAY_RETIME=1,建回應時
#     把內層 epoch 全部改成「當下(被 faketime 的)時間」→ 死時戳跟著 device 一起走 → 永遠對得上。
#
# 用法:  ./replay_cft.sh
#        REPLAY_ROUNDS=<局號,...> ./replay_cft.sh   # 只播指定局
# 收工:  Ctrl+C(停 server),Chrome 直接關視窗。★別開 DevTools★。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
PORT=8443
# 每次啟動自動算偏移,讓 device 固定落在【擷取日】(09-11),不管今天是哪天都有效(耐久)。
# server 和 client 共用這個算出的偏移值 → 兩進程用同一系統時鐘算 → 零時差(MSG8 校時要的)。
RETIME_REF="${RETIME_REF:-1789109665}"          # 擷取 handshake 基準:07:07:45 UTC 2026-09-11
FAKE_TARGET="${FAKE_TARGET:-$RETIME_REF}"        # 想把 device 撥到哪個 epoch(預設=擷取日)
OFFSET="${FAKE_OFFSET:--$(( $(date +%s) - FAKE_TARGET ))}"   # 純秒偏移 -N;或用 FAKE_OFFSET=-18d 覆蓋

LFT="$(ls /opt/homebrew/lib/faketime/libfaketime.1.dylib \
         /opt/homebrew/Cellar/libfaketime/*/lib/faketime/libfaketime.1.dylib 2>/dev/null | head -1)"
CFT="${CFT:-$HOME/.cache/puppeteer/chrome/mac_arm-152.0.7977.54/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing}"
REPLAY="${REPLAY:-$ROOT/games/696/webcap/exchanges_ordered.jsonl}"
REPLAY_SPINS="${REPLAY_SPINS:-$ROOT/games/696/webcap/spins_raw}"
ROUNDS="${1:-${REPLAY_ROUNDS:-}}"

[ -x "$PY" ]  || { echo "✗ 沒有 venv python:$PY"; exit 1; }
[ -n "$LFT" ] || { echo "✗ 沒有 libfaketime。先: brew install libfaketime"; exit 1; }
[ -x "$CFT" ] || { echo "✗ 沒有 Chrome for Testing:$CFT(可設 CFT=...)"; exit 1; }
[ -f "$REPLAY" ] || { echo "✗ 沒有 REPLAY:$REPLAY"; exit 1; }

export DYLD_INSERT_LIBRARIES="$LFT" DYLD_FORCE_FLAT_NAMESPACE=1 FAKETIME="$OFFSET"

echo "① 停舊 mock / CfT"
lsof -nP -iTCP:$PORT -sTCP:LISTEN -t 2>/dev/null | xargs kill 2>/dev/null || true
pkill -f 'cft-replay-profile' 2>/dev/null || true
sleep 1
echo "   faketime offset=$OFFSET → device≈$("$PY" -c 'import time,datetime;print(datetime.datetime.utcfromtimestamp(time.time()).isoformat())') UTC"

# ② CfT:等 server listen 後自動開(本視窗留給 server log)
URL="https://uat-wbgame.jlfafafa3.com/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0"
(
  for _ in $(seq 1 60); do
    curl -sk -o /dev/null --max-time 1 "https://127.0.0.1:$PORT/" 2>/dev/null && break
    sleep 0.5
  done
  echo "③ 開 Chrome for Testing(偏移同步)"
  "$CFT" --user-data-dir="/tmp/cft-replay-profile-$(date +%s)" \
    --no-sandbox --host-resolver-rules="MAP * 127.0.0.1:$PORT" \
    --ignore-certificate-errors --disable-quic --no-first-run --no-default-browser-check \
    "$URL" >/dev/null 2>&1 &
) &

# ③ server(前景=log;偏移 + retime)
# ★關鍵★:一定要「行內賦值」直接跑 python,【不能用 /usr/bin/env】——env 是 SIP 保護的系統
# 二進位,dyld 經過它會把 DYLD_INSERT_LIBRARIES 剝掉 → server 沒被 libfaketime 撥時鐘 →
# 回應時戳(信封 f1)是真實時間 → 遊戲比對 device(假) vs f1(真) → MSG 8。所以這裡用 export + exec。
if [ -n "$ROUNDS" ]; then echo "② server:只播 $ROUNDS"; else echo "② server:播全部(循環)"; fi
echo "   (看到 handshake / kind=init / spin[..] 就是通了;★別開 DevTools★;Ctrl+C 收工)"
echo "────────────────────────────────────────────"
export PORT="$PORT" TLS=1 VERBOSE=1 INJECT_BUNDLE=1 REPLAY_RETIME=1 RETIME_REF="$RETIME_REF"
export REPLAY="$REPLAY" REPLAY_SPINS="$REPLAY_SPINS"
[ -n "$ROUNDS" ] && export REPLAY_ROUNDS="$ROUNDS"
exec "$PY" routex/server.py            # DYLD_INSERT_LIBRARIES / FAKETIME 已在最上面 export
