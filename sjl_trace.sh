#!/usr/bin/env bash
# sjl_trace.sh — 定位 Domain Lock 檢查點(純網頁,不用 Frida)。
# 用 myslot.test(違規)跑,EXTRA_SHIM=sjl_trace_shim 攔 window.SendJscramblerLog,
# 等 22de5 呼叫它時抓 stack → mock log 印出「index.22de5.js:行:列」= 檢查碼位置。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
APIDOM="${1:-myslot.test}"
REV=$(printf '%s' "$APIDOM" | rev)
PROFILE="/tmp/jili-sjl-$(date +%s)"
JILI_HOSTS="uat-wbgame.jlfafafa3.com uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com"
URL="https://$APIDOM/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=$REV&domain_gs=1afafaflj&domain_platform=$REV&gameID=696&gs=$REV&iu=true&legalLang=true&skin=0"
MOCK_CMD="cd $ROOT && sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 EXTRA_SHIM=sjl_trace_shim.js .venv/bin/python3 routex/server.py"

term(){ osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}

echo "── 定位 Domain Lock 檢查點:攔 SendJscramblerLog 抓 stack(document=${APIDOM} 觸發違規)──"
[ -x "$PY" ] || { echo "✗ venv python 不在:$PY"; exit 1; }
[ -x "$CHROME" ] || { echo "✗ Chrome 不在:$CHROME"; exit 1; }
[ -f "$ROOT/routex/sjl_trace_shim.js" ] || { echo "✗ 找不到 routex/sjl_trace_shim.js"; exit 1; }

echo "[0] 清舊 Chrome/server"
pkill -f 'jili-sjl-' 2>/dev/null || true
sudo pkill -f 'routex/server.py' 2>/dev/null || true
sleep 1

echo "[1] hosts:jili 4 host + ${APIDOM} → 127.0.0.1…"
for h in $JILI_HOSTS "$APIDOM"; do
  sudo sed -i '' -E "/^[[:space:]]*127\.0\.0\.1[[:space:]].*$h/d" /etc/hosts 2>/dev/null || true
done
echo "127.0.0.1 $JILI_HOSTS $APIDOM" | sudo tee -a /etc/hosts >/dev/null
{ sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null || true
echo "    ✓ 已設 + flush DNS"

echo "[2] 開 mock + EXTRA_SHIM(新視窗,輸密碼)…"
term "$MOCK_CMD"
printf "    等 mock listen 443"
ok=0
for _ in $(seq 1 30); do
  if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then ok=1; echo " ✓"; break; fi
  printf "."; sleep 1
done
[ "$ok" = 1 ] || { echo " ✗ mock 沒起來(看新視窗)"; exit 1; }

echo "[3] 開 Chrome(普通 Chrome 即可,不用 Frida)…"
"$CHROME" --user-data-dir="$PROFILE" --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 看【mock 視窗】的 ★★★ [shim-report] SJL:"
echo "   • SJL setter armed / index.html assigned SJL -> wrapped = 攔截就緒"
echo "   • SJL CALL type=DomainLock = 22de5 的檢查呼叫了它"
echo "   • ★SJL stack[1] / stack[2] … at … index.22de5.js:行:列 = 檢查碼的確切位置★"
echo "   把那幾行 SJL stack[...] 貼給 Claude → 我去 22de5 那個位置看檢查邏輯、想 patch。"
echo "   收工:./stop.sh"
