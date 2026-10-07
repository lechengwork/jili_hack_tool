#!/usr/bin/env bash
# wscapture.sh — JILI 明文 WebSocket 遊戲【實時擷取】真伺服器封包(Mac/白名單機)。
# 以【遊戲號】分派:124=7up7down(/sudm), 94=Rummy(/rummy)。對應 Windows 的 wscapture.ps1。
#
# 原理(與 124 同):split-host — 只 doc host(uat-wbgame) 用 Chrome --host-resolver-rules 導本機
#   server(服務該遊戲的【靜態鏡像】+ 注入 ws_capture_shim 側錄 WebSocket);sso-login(uat-wbwebapi)
#   /遊戲 WS(uat-wbslot-fd 等)走【真站】(需 BR VPN)。location.hostname 仍是真 jili host → 過 domain-lock,免 bypass。
#   ★鏡像缺檔★:設 ORIGIN(見下 case)時,server 會自動從真 doc host 補抓並快取 → 2 局的鏡像也能自我補完。
#
# 前置:先【關 VPN(TW)】讓這支產 token;產完再叫你【開 BR VPN】。收工 kill server + wscapture_finish.sh。
# env: PORT(預設8443) CHROME OUT(側錄檔) URL(給定就跳過產token) ACCOUNT/PLAYER_ID(換帳號) MATH_OUT
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
GID="${1:-124}"
PORT="${PORT:-8443}"
PY="${PY:-$ROOT/.venv/bin/python3}"; [ -x "$PY" ] || PY="python3"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
DOC_HOST="uat-wbgame.jlfafafa3.com"
PROFILE="/tmp/jili-webcap-profile-$(date +%s)"   # ★每次開全新 profile★(固定 profile 跑多次會累積髒快取/SW → 遊戲 init 崩在開 WS 前,同 696 原版做法)
UUID="${VPN_UUID:-E2416E2B-51EA-4569-B4D9-49A7665E5BC2}"   # Surfshark WireGuard(override: VPN_UUID=...)
AUTO_VPN="${AUTO_VPN:-1}"   # 1=scutil 自動切 VPN(切不動自動退回手動按 Enter);0=一律手動

country(){ curl -s --max-time 6 https://ipinfo.io/json | "$PY" -c "import sys,json;print(json.load(sys.stdin).get('country',''))" 2>/dev/null; }
wait_country(){ local want="$1" c; for _ in $(seq 1 25); do c=$(country); [ "$c" = "$want" ] && { echo "$c"; return 0; }; sleep 2; done; echo "$c"; return 1; }
vpn_switch(){ # $1=want(TW/BR) $2=scutil動作(stop/start) $3=手動提示
  local want="$1" act="$2" hint="$3" c
  if [ "$AUTO_VPN" = 1 ]; then
    scutil --nc "$act" "$UUID" >/dev/null 2>&1 || true
    c=$(wait_country "$want") && { echo "    country=$c ✓"; return 0; }
    echo "    (自動切沒到 $want,現在=$c → 改手動)"
  fi
  read -r -p "    $hint 切好後按 Enter…" _
  c=$(wait_country "$want") || { echo "    !!! 還不是 $want(現在=$c)"; return 1; }
  echo "    country=$c ✓"
}

# ── 每遊戲設定(新增遊戲在這裡加一筆) ────────────────────────────────
case "$GID" in
  124) PATHSEG="sudm";  STATIC="$ROOT/dist124/static";  ORIGIN="";                    FINISH="ws_math_view" ;;
  94)  PATHSEG="rummy"; STATIC="$ROOT/games/94/static"; ORIGIN="https://$DOC_HOST";   FINISH="ws_rummy_view" ;;
  736) PATHSEG="fish23"; STATIC="$ROOT/games/736/static"; ORIGIN="https://$DOC_HOST"; FINISH="ws_fish736_view" ;;
  *)   echo "✗ 未登記的遊戲號 $GID(目前支援:124/94/736)。新增:在 wscapture.sh 的 case 加一筆 PATHSEG/STATIC/ORIGIN/FINISH。"; exit 1 ;;
esac
OUT="${OUT:-$ROOT/games/$GID/webcap_ws.jsonl}"
DOC_INDEX="/$PATHSEG/index.html"

[ -x "$CHROME" ] || { echo "✗ 找不到 Chrome:$CHROME (可設 CHROME=...)"; exit 1; }
[ -d "$STATIC" ] || { echo "✗ 找不到靜態鏡像:$STATIC(先用 ./wscapture_boot.sh $GID 或 jili_capture.py $GID 抓一次鏡像)"; exit 1; }

echo "── JILI $GID 實時擷取(Mac)  path=/$PATHSEG  static=$STATIC ──"
echo "[0] 清舊 server/Chrome(含 replay server + 佔 $PORT 的任何程式)"
pkill -f 'ws_capture_server.py' 2>/dev/null || true
pkill -f 'ws_replay_server.py' 2>/dev/null || true
pkill -f 'jili-webcap-profile' 2>/dev/null || true
P=$(lsof -nP -tiTCP:$PORT -sTCP:LISTEN 2>/dev/null || true); [ -n "$P" ] && { kill -9 $P 2>/dev/null || true; echo "    清掉佔 $PORT 的 PID:$P"; }
rm -rf /tmp/jili-webcap-profile-* 2>/dev/null || true   # 清掉舊 profile(髒快取/SW 會弄壞遊戲 init)
sleep 1

# 換帳號:ACCOUNT=<config login_accounts key> 或 PLAYER_ID=<直接指定>
LOGIN_ARGS=""
[ -n "${ACCOUNT:-}" ]   && LOGIN_ARGS="$LOGIN_ARGS --account $ACCOUNT"
[ -n "${PLAYER_ID:-}" ] && LOGIN_ARGS="$LOGIN_ARGS --player-id $PLAYER_ID"

URL="${URL:-}"
if [ -z "$URL" ]; then
  echo "[1] VPN 關 → 等 TW(產 token 需要)…"
  vpn_switch TW stop "請【關閉】VPN。" || exit 1
  URL="$("$PY" jili_login.py "$GID" $LOGIN_ARGS --json | "$PY" -c 'import sys,json; d=json.load(sys.stdin); d=d[0] if isinstance(d,list) else d; print(d.get("game_url",""))')"
  [ -n "$URL" ] || { echo "✗ 產 token 失敗(game_url=null;$GID 該帳號可能沒上架 → 試 ACCOUNT=evo/thb,或 URL=\"...\" 手動貼)"; exit 1; }
fi
echo "    game_url = ${URL:0:80}…"

echo "[2] 起擷取 server(port $PORT;STATIC=$STATIC;注入 shim${ORIGIN:+;缺檔自動從 $ORIGIN 補})"
# 保留上一輪側錄(被 idle-kick 重連也能累加) → 歸檔到 raw_sessions/,不再直接刪。
# 736 解碼器會讀 raw_sessions/*.jsonl 一併累加;124/94 仍讀當輪 $OUT,不受影響。
if [ -f "$OUT" ]; then
  ARCH="$(dirname "$OUT")/raw_sessions"; mkdir -p "$ARCH"
  mv "$OUT" "$ARCH/$(basename "${OUT%.jsonl}").$(date +%Y%m%d-%H%M%S).jsonl" 2>/dev/null || rm -f "$OUT"
fi
OUT="$OUT" PORT="$PORT" TLS=1 VERBOSE=1 STATIC="$STATIC" DOC_INDEX="$DOC_INDEX" ORIGIN="$ORIGIN" \
  "$PY" -u ws_capture_server.py > "/tmp/ws${GID}_cap.log" 2>&1 &
SRV=$!
printf "    等 server listen"
for _ in $(seq 1 30); do
  if curl -sk -o /dev/null --max-time 1 "https://127.0.0.1:$PORT$DOC_INDEX"; then echo " ✓"; break; fi
  kill -0 "$SRV" 2>/dev/null || { echo " ✗ server 掛了"; tail -20 "/tmp/ws${GID}_cap.log"; exit 1; }
  printf "."; sleep 1
done

echo "[3] VPN 開 → 等 BR(sso-login / 遊戲 WS / 缺檔補抓都要走真站)…"
vpn_switch BR start "請【開啟】VPN(巴西)。" || exit 1

echo "[4] 開 Chrome:只把 $DOC_HOST 導本機(WS/api 走真站 VPN)"
"$CHROME" \
  --user-data-dir="$PROFILE" \
  --host-resolver-rules="MAP $DOC_HOST 127.0.0.1:$PORT" \
  --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check \
  --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 開始擷取:進遊戲/牌桌,打你要的局數(越多越好)。★別開 DevTools★。盯 server:tail -f /tmp/ws${GID}_cap.log"
echo "   看到 [ws] SEND/RECV = 有抓到;只有 [shim] 沒 [ws] = WS 沒連上(檢查 VPN/token);[backfill] = 自動補鏡像缺檔。"
echo "   收工:kill $SRV   然後   ./wscapture_finish.sh $GID   (或 $PY $FINISH.py $GID)"
