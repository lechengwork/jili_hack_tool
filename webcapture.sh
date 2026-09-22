#!/usr/bin/env bash
# webcapture.sh — 純網頁擷取【真伺服器】封包(免 Frida、免 netlog)。
#
# 原理:本地 server 只服務「靜態站 + capture-shim」;/fg5/req、sso 走【真主機】(VPN)。
#   split /etc/hosts:只有 document host(uat-wbgame)→ 127.0.0.1;api host(be/gs)→ 真站。
#   shim 在頁面裡 hook fetch 側錄每筆 /fg5/req,並從 crypto-wasm 記憶體讀 shared key → POST /__capture__。
#   收工 ./webcapture_finish.sh 批次離線解 → 每一局的 JSON。
#
# 你只要:打 ./webcapture.sh → 在跳出的 server 視窗輸一次 Mac 密碼(443 要 sudo)→
#         進遊戲、開【自動轉(autoplay)】轉到你要的局數 → 回來打 ./webcapture_finish.sh。
#
# 流程:① VPN 關→產真 token  ② split /etc/hosts(只 doc 指本機)  ③ 開 server(capture 模式)
#      ④ VPN 開→BR  ⑤ 開普通 Chrome 連【真 token 的 game_url】
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
UUID="${VPN_UUID:-E2416E2B-51EA-4569-B4D9-49A7665E5BC2}"   # Surfshark WireGuard profile(override: VPN_UUID=...)
GID="${1:-696}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
PROFILE="/tmp/jili-webcap-profile-$(date +%s)"
DOC_HOST="uat-wbgame.jlfafafa3.com"
ALL_HOSTS="$DOC_HOST uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com"
# 轉發可選的環境變數給 server:sudo 會清掉呼叫端環境,而且 server 是用 osascript 開在
# 另一個 Terminal 視窗,所以一定要在這裡顯式帶進去,不然 `MATH_OUT=... ./webcapture.sh` 會靜靜沒作用。
#   MATH_OUT=<dir>  機率介面每局檔要寫去哪(預設 games/<gid>/math)
#   LIVE_RAW=1      主控台改印工程用明文(payload_hex + payload_named)
#   ASSET_FALLBACK=1  鏡像缺的靜態資產(404)自動從真站抓回來並存進 mirror
#                     ——罕見效果第一次觸發時才會下載的 bundle 就靠這個補
PASS_ENV=""
for _v in MATH_OUT LIVE_RAW SPIN_OUT SPIN_RAW_OUT BR_SPIN_OUT ASSET_FALLBACK ASSET_ORIGIN; do
  eval "_val=\${$_v:-}"
  [ -n "$_val" ] && PASS_ENV="$PASS_ENV $_v=$_val"
done
[ -n "$PASS_ENV" ] && echo "  轉發給 server 的環境變數:$PASS_ENV"
MOCK_CMD="cd $ROOT && sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 CAPTURE=1 LIVE_DECODE=1$PASS_ENV .venv/bin/python3 routex/server.py"

term(){ osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}
country(){ curl -s --max-time 6 https://ipinfo.io/json | "$PY" -c "import sys,json;print(json.load(sys.stdin).get('country',''))" 2>/dev/null; }
wait_country(){ local want="$1" c; for _ in $(seq 1 25); do c=$(country); [ "$c" = "$want" ] && { echo "$c"; return 0; }; sleep 2; done; echo "$c"; return 1; }

echo "── JILI $GID 純網頁擷取(真伺服器,免 Frida)──"

# ── preflight ──
[ -x "$PY" ]                        || { echo "✗ 找不到 venv python:$PY"; exit 1; }
[ -f "$ROOT/routex/server.py" ]     || { echo "✗ 找不到 routex/server.py"; exit 1; }
[ -f "$ROOT/routex/capture_shim.js" ]|| { echo "✗ 找不到 routex/capture_shim.js"; exit 1; }
[ -x "$CHROME" ]                    || { echo "✗ 找不到普通 Google Chrome:$CHROME(可設 CHROME=... )"; exit 1; }

echo "[0] 清乾淨舊 Chrome / 舊 server"
pkill -f 'jili-webcap-profile' 2>/dev/null || true
sudo pkill -f 'routex/server.py' 2>/dev/null || true
sleep 1

echo "[1] VPN 關 → 等 TW(產 token 需要)…"
scutil --nc stop "$UUID" >/dev/null 2>&1 || true
c=$(wait_country TW) || { echo "!!! 沒切成 TW(現在=$c),停"; exit 1; }
echo "    country=$c ✓"

# 換帳號:ACCOUNT=<config.json login_accounts 的 key,如 thb> 或 PLAYER_ID=<直接指定 player_id>
#   例:ACCOUNT=thb ./webcapture.sh 696   /   PLAYER_ID=tryplayer003usd ./webcapture.sh 696
LOGIN_ARGS=""
[ -n "${ACCOUNT:-}" ]   && LOGIN_ARGS="$LOGIN_ARGS --account $ACCOUNT"
[ -n "${PLAYER_ID:-}" ] && LOGIN_ARGS="$LOGIN_ARGS --player-id $PLAYER_ID"
echo "[2] 產真 token(gameid=$GID${LOGIN_ARGS:+,$LOGIN_ARGS})…"
"$PY" jili_login.py "$GID" $LOGIN_ARGS --json > /tmp/webcap_login.json 2>/tmp/webcap_login_err.txt || true
URL=$("$PY" -c "import json;d=json.load(open('/tmp/webcap_login.json'));d=d[0] if isinstance(d,list) else d;print(d.get('game_url',''))" 2>/dev/null || true)
[ -z "$URL" ] && { echo "!!! 產 token 失敗:"; cat /tmp/webcap_login_err.txt; exit 1; }
SSO=$("$PY" -c "import json,urllib.parse as u;d=json.load(open('/tmp/webcap_login.json'));d=d[0] if isinstance(d,list) else d;print(u.parse_qs(u.urlparse(d['game_url']).query).get('ssoKey',[''])[0])" 2>/dev/null || true)
echo "    ssoKey=$SSO ✓"
echo "$URL" > /tmp/webcap_url.txt

echo "[3] split /etc/hosts:只有 document host → 127.0.0.1(api host 走真站)…"
# 先移除任何把「遊戲 4 host」指向 127.0.0.1 的舊行(mock 的 4-host 行),再只加 doc host。
NEED_FIX=0
for h in $ALL_HOSTS; do grep -qE "^[[:space:]]*127\.0\.0\.1[[:space:]].*$h" /etc/hosts && NEED_FIX=1; done
grep -qE "^[[:space:]]*127\.0\.0\.1[[:space:]]+$DOC_HOST[[:space:]]*\$" /etc/hosts || NEED_FIX=1
if [ "$NEED_FIX" = 1 ]; then
  for h in $ALL_HOSTS; do sudo sed -i '' -E "/^[[:space:]]*127\.0\.0\.1[[:space:]].*$h/d" /etc/hosts; done
  echo "127.0.0.1 $DOC_HOST" | sudo tee -a /etc/hosts >/dev/null
  { sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null || true
  echo "    ✓ hosts 已設(只 $DOC_HOST → 127.0.0.1)+ flush DNS"
else
  echo "    hosts 已是 split 狀態 ✓"
fi

echo "[4] 開 server(capture 模式,新視窗,請在該視窗輸入 Mac 密碼)…"
term "$MOCK_CMD"
printf "    等 server listen 443"
ok=0
for _ in $(seq 1 30); do
  if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then ok=1; echo " ✓"; break; fi
  printf "."; sleep 1
done
[ "$ok" = 1 ] || { echo " ✗ server 沒起來(看新視窗:443 被占用 / 密碼沒輸)"; exit 1; }

echo "[5] VPN 開 → 等 BR(真 /fg5/req 要巴西出口)…"
scutil --nc start "$UUID" >/dev/null 2>&1 || true
c=$(wait_country BR) || { echo "!!! 沒切成 BR(現在=$c),停"; exit 1; }
echo "    country=$c ✓"

echo "[6] 開普通 Chrome 連真 token 的 game_url(拋棄式 profile)…"
"$CHROME" \
  --user-data-dir="$PROFILE" \
  --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check \
  --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 開始擷取。做這些:"
echo "   1) 進遊戲(點兩顆按鈕進真實畫面)。★別開 DevTools★"
echo "   2) 用遊戲的【自動轉/autoplay】轉到你要的局數(幾千幾萬)。"
echo "   3) 盯【server 視窗】:每筆 spin 都會即時印出【這一局解出來的格式】——"
echo "      ┌── [decode] seq=… type=0 (spin) …  之後跟著 round_id/餘額/總中獎/底注/倍率/盤面/中獎線。"
echo "      (第一筆會帶 ★ +KEY;拿到 key 後每一局都即時解。spin 一次就看得到一局。)"
echo "   4) 想一次把全部匯成檔(pretty.jsonl)→ 打:  ./webcapture_finish.sh $GID  (可選,即時已經看得到了)"
echo
echo "   收工/中止:./stop.sh(停 server + 關這個擷取 Chrome)。回 mock:./run.sh 或 ./web.sh(會自動修回 hosts)。"
