#!/usr/bin/env bash
# dl_trace.sh — 【Phase 1+ 動態追值】定位 Domain Lock 的「比對方式」+ 證實/證偽 hash-gate 猜想(純網頁,免 Frida)。
# 用 myslot.test(違規)跑,EXTRA_SHIM=dl_trace2_shim.js 從 polyfills 最先掛:
#   • hook String/RegExp/Array 比對方法(看有沒有 domainish 明文流過)
#   • ★hook charCodeAt/codePointAt(hash 指紋:domain 被逐字讀 = JS hash 在算它)
#   • trace 可攔截的 location/document 讀取點 + crypto.subtle.digest + SendJscramblerLog 對齊
# 判讀看檔頭註解 dl_trace2_shim.js;把 mock 視窗的 ★★★ [shim-report] TRACE … 幾行貼回來。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
SHIM="${SHIM:-dl_trace2_shim.js}"                  # 可 SHIM=dl_trace_shim.js 跑舊版對照
APIDOM="${1:-myslot.test}"
REV=$(printf '%s' "$APIDOM" | rev)
PROFILE="/tmp/jili-dltrace-$(date +%s)"
JILI_HOSTS="uat-wbgame.jlfafafa3.com uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com"
URL="https://$APIDOM/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=$REV&domain_gs=1afafaflj&domain_platform=$REV&gameID=696&gs=$REV&iu=true&legalLang=true&skin=0"
MOCK_CMD="cd $ROOT && sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 EXTRA_SHIM=$SHIM .venv/bin/python3 routex/server.py"

term(){ osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}

echo "── Phase 1+ 動態追值:document=${APIDOM}(觸發違規)+ EXTRA_SHIM=${SHIM} ──"
[ -x "$PY" ] || { echo "✗ venv python 不在:$PY"; exit 1; }
[ -x "$CHROME" ] || { echo "✗ Chrome 不在:$CHROME"; exit 1; }
[ -f "$ROOT/routex/$SHIM" ] || { echo "✗ 找不到 routex/$SHIM"; exit 1; }

echo "[0] 清舊 Chrome/server"
pkill -f 'jili-dltrace-' 2>/dev/null || true
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

echo "[3] 開 Chrome(普通 Chrome 即可,不用 Frida,★別開 DevTools★)…"
"$CHROME" --user-data-dir="$PROFILE" --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 看【mock 視窗】的 ★★★ [shim-report] TRACE:"
echo "   • S.indexOf / RE.test a0=\"...jlfafafa...\"  → 明文(runtime 解出)= 不是 hash → hook 那個 method 收工"
echo "   • CHARCODE.charCodeAt FULL-PASS on \"myslot.test\" = 疑似 hash → ★hash 猜想成立★;stack = hash fn 位置"
echo "   • READ location.* / document.*             → 誰在讀網域(可攔截點 = dlpoc 偽裝就能贏)"
echo "   • CHARCODE summary:無 domain 逐字讀        → 不是 JS hash(可能 ===/includes/bracket-index)"
echo "   把出現 jlfafafa/myslot 的那幾行 TRACE 貼回來 → 我照它決定 Phase 2 怎麼下刀。"
echo "   收工:./stop.sh"
