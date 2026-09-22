#!/usr/bin/env bash
# dl_domtest.sh — ④ 經驗測試:從【非允許網域】載入遊戲,看 domain-lock 擋不擋、怎麼擋。
#   把一個假網域(jili-domtest.local,預設)+ jlfafafa API 4 host 都指到 127.0.0.1(本機 mock)。
#   遊戲【文件】從假網域載入 → location.hostname = 假網域(非允許);API 仍走 jlfafafa 本機 mock。
#   配 no-op shim(JS log):
#     - 到轉盤       = domain-lock 沒真的擋(或不讀 location)→ ④ 可能更簡單。
#     - 卡住/JSERR/GameTampering = 有擋 → 看它在哪一步、用什麼訊息擋(據此定位比對點 + 碰撞目標)。
#   ★別開 DevTools。用 TEST_HOST=xxx 覆寫假網域。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
SHIM="${SHIM:-dl_noop_probe_shim.js}"
TEST_HOST="${TEST_HOST:-jili-domtest.local}"
PROFILE="${JILI_PROFILE:-$HOME/.jili-test-profile}"
JILI_HOSTS="uat-wbgame.jlfafafa3.com uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com"
# 文件從【假網域】載入(location.hostname 變非允許);API 參數維持 jlfafafa 本機 mock。
URL="https://${TEST_HOST}/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0"
MOCK_CMD="cd $ROOT && sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 DOC_HOST=${TEST_HOST} EXTRA_SHIM=$SHIM .venv/bin/python3 routex/server.py"

term(){ osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}

echo "── ④ domain-lock 經驗測試:文件從【${TEST_HOST}】(非允許)載入 + EXTRA_SHIM=${SHIM} ──"
[ -x "$PY" ]     || { echo "✗ venv python 不在:$PY"; exit 1; }
[ -x "$CHROME" ] || { echo "✗ Chrome 不在:$CHROME"; exit 1; }
[ -f "$ROOT/routex/$SHIM" ] || { echo "✗ 找不到 routex/$SHIM"; exit 1; }

echo "[0] 清舊 mock server(不動持久 profile Chrome)"
sudo pkill -f 'routex/server.py' 2>/dev/null || true
sleep 1

echo "[1] hosts:假網域 + jlfafafa 4 host → 127.0.0.1…"
for h in $TEST_HOST $JILI_HOSTS; do
  sudo sed -i '' -E "/^[[:space:]]*127\.0\.0\.1[[:space:]].*$h/d" /etc/hosts 2>/dev/null || true
done
echo "127.0.0.1 $TEST_HOST $JILI_HOSTS" | sudo tee -a /etc/hosts >/dev/null
{ sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null || true
echo "    ✓ 已設 + flush DNS"

echo "[2] 開 mock(DOC_HOST=${TEST_HOST})…"
if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then
  echo "    ⚠ 443 已在服務——請先 ./stop.sh 再跑(需 DOC_HOST=${TEST_HOST} 版)"
else
  term "$MOCK_CMD"
  printf "    等 mock listen 443"
  ok=0
  for _ in $(seq 1 30); do
    if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then ok=1; echo " ✓"; break; fi
    printf "."; sleep 1
  done
  [ "$ok" = 1 ] || { echo " ✗ mock 沒起來(看新視窗)"; exit 1; }
fi

echo "[3] 開 Chrome 載入非允許網域(持久 profile,★別開 DevTools★)…"
"$CHROME" --user-data-dir="$PROFILE" --ignore-certificate-errors --disable-quic \
  --disk-cache-size=1 --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 觀察:到轉盤 = 沒真的擋;卡住/JSERR/GameTampering = 有擋(看在哪步、什麼訊息)。"
echo "   把 mock 視窗的 NOOP/tele/POST 行 + Chrome 畫面狀態貼回來。收工:./stop.sh"
