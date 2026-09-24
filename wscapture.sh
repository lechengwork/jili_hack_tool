#!/usr/bin/env bash
# wscapture.sh — JILI 124 (7up7down) 實時擷取【真伺服器】WebSocket 封包(Mac/白名單機)。
# 對應 Windows 的 wscapture.ps1。split-host:只 doc host(uat-wbgame)導本機 server(服務 static +
# 注入 WS-hook shim);sso-login(uat-wbwebapi)/遊戲 WS(uat-fish)走真站(需 BR VPN)。
# 用 jili host 就過 domain-lock,不用 bypass。頁面內 shim 側錄每個明文 WS frame → 本機 server。
#
# 前置:先【關 VPN(TW)】讓這支產 token;產完再叫你【開 BR VPN】。收工 Ctrl+C server + ./stop.sh(dist124)。
# env: PORT(預設8443) CHROME OUT(側錄檔) URL(給定就跳過產token)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PORT="${PORT:-8443}"
PY="${PY:-python3}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
DOC_HOST="uat-wbgame.jlfafafa3.com"
OUT="${OUT:-$ROOT/games/124/webcap_ws.jsonl}"
PROFILE="/tmp/jili-webcap-profile"

[ -x "$CHROME" ] || { echo "✗ 找不到 Chrome:$CHROME (可設 CHROME=...)"; exit 1; }

echo "── JILI 124 實時擷取(Mac)──"
echo "[0] 清舊 server/Chrome"
pkill -f 'ws_capture_server.py' 2>/dev/null || true
pkill -f 'jili-webcap-profile' 2>/dev/null || true
sleep 1

URL="${URL:-}"
if [ -z "$URL" ]; then
  echo "[1] 產 token(需【關 VPN / 台灣】)。若現在是 BR，先關 VPN 再按 Enter。"
  read -r -p "    關好 VPN 後按 Enter…" _
  URL="$("$PY" jili_login.py 124 --json | "$PY" -c 'import sys,json; d=json.load(sys.stdin); d=d[0] if isinstance(d,list) else d; print(d["game_url"])')"
  [ -n "$URL" ] || { echo "✗ 產 token 失敗"; exit 1; }
fi
echo "    game_url = ${URL:0:80}…"

echo "[2] 起擷取 server(port $PORT,注入 shim)"
rm -f "$OUT"
OUT="$OUT" PORT="$PORT" TLS=1 VERBOSE=1 "$PY" -u ws_capture_server.py > /tmp/ws124_cap.log 2>&1 &
SRV=$!
printf "    等 server listen"
for _ in $(seq 1 30); do
  if curl -sk -o /dev/null --max-time 1 "https://127.0.0.1:$PORT/sudm/index.html"; then echo " ✓"; break; fi
  kill -0 "$SRV" 2>/dev/null || { echo " ✗ server 掛了"; tail -20 /tmp/ws124_cap.log; exit 1; }
  printf "."; sleep 1
done

echo "[3] 現在【開 BR VPN(巴西)】—— sso-login/WS 要走真站。"
read -r -p "    VPN 連上巴西後按 Enter 開 Chrome…" _

echo "[4] 開 Chrome:只把 $DOC_HOST 導本機(WS/api 走真站 VPN)"
"$CHROME" \
  --user-data-dir="$PROFILE" \
  --host-resolver-rules="MAP $DOC_HOST 127.0.0.1:$PORT" \
  --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check \
  --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 開始擷取:進遊戲下注/開骰。盯 server:tail -f /tmp/ws124_cap.log"
echo "   看到 [ws] SEND/RECV = 有抓到;只有 [shim] 沒 [ws] = WS 沒連上(檢查 VPN/token)。"
echo "   收工:kill $SRV  然後  $PY ws_math_view.py --src \"$OUT\" --out games/124/math"