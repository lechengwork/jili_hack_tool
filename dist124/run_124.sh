#!/usr/bin/env bash
# run_124.sh — 一鍵開 JILI 124 (7up7down) 本地離線回放。
#   ① 起 ws_replay_server.py(TLS 自簽)  ② 開 Chrome,用 --host-resolver-rules
#   把所有 jili host 指到本機 server(保留 jili hostname → 過 Jscrambler domain-lock)。
# 全本機、免 VPN、免 sudo、免改 /etc/hosts。收工:./stop.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PORT="${PORT:-8443}"
PY="${PY:-python3}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
PROFILE="/tmp/jili124-replay-profile"
# 入口 URL:ssoKey 用 replay(mock sso 不驗);其餘參數照擷取時,遊戲用它們組 host。
URL="https://uat-wbgame.jlfafafa3.com/sudm/index.html?ssoKey=replay&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=124&gs=1afafaflj&iu=true&legalLang=true&skin=0"

echo "── JILI 124 本地回放 ──"
[ -x "$CHROME" ] || { echo "✗ 找不到 Chrome:$CHROME (可設 CHROME=...)"; exit 1; }

echo "[0] 清舊 server / Chrome"
pkill -f 'ws_replay_server.py' 2>/dev/null || true
pkill -f 'jili124-replay-profile' 2>/dev/null || true
sleep 1

echo "[1] 起回放 server (port $PORT)"
PORT="$PORT" "$PY" ws_replay_server.py > /tmp/jili124_server.log 2>&1 &
SRV=$!
printf "    等 server listen"
for _ in $(seq 1 30); do
  if curl -sk -o /dev/null --max-time 1 "https://127.0.0.1:$PORT/sudm/index.html"; then echo " ✓"; break; fi
  kill -0 "$SRV" 2>/dev/null || { echo " ✗ server 掛了,看 /tmp/jili124_server.log"; tail -20 /tmp/jili124_server.log; exit 1; }
  printf "."; sleep 1
done

echo "[2] 開 Chrome(拋棄式 profile,host-resolver-rules 全指本機)"
"$CHROME" \
  --user-data-dir="$PROFILE" \
  --host-resolver-rules="MAP * 127.0.0.1:$PORT" \
  --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check \
  --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 已開。遊戲會載入本機 mirror、WS 走本機回放 server。"
echo "   · server log: tail -f /tmp/jili124_server.log  (加 VERBOSE=1 看每筆 WS)"
echo "   · 下注會顯示【錄到的那場結果】(依 cmd 配對回放,cmd22 循環)。★別開 DevTools★"
echo "   · 收工:./stop.sh"
