#!/usr/bin/env bash
# dl_session.sh — 用 CfT 開「違規 session」(document=myslot.test 讓 Domain Lock 觸發),供 dl_dump.py 撈檢查點。
# 為什麼 CfT:普通 Chrome 的 hardened runtime 連 root 都掛不上 Frida;CfT + --no-sandbox 才行。
# 流程:hosts(jili + myslot.test → localhost)→ 開 mock(INJECT_BUNDLE,盡量載到 lock)→ 開 CfT(myslot.test)。
#       等它卡在 loading(lock 觸發、"DomainLock" 已解進記憶體)→ 另跑:sudo ./.venv/bin/python dl_dump.py
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
APIDOM="${1:-myslot.test}"
REV=$(printf '%s' "$APIDOM" | rev)
PROFILE="/tmp/jili-dlsess-$(date +%s)"
JILI_HOSTS="uat-wbgame.jlfafafa3.com uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com"
URL="https://$APIDOM/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=$REV&domain_gs=1afafaflj&domain_platform=$REV&gameID=696&gs=$REV&iu=true&legalLang=true&skin=0"
MOCK_CMD="cd $ROOT && sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 .venv/bin/python3 routex/server.py"

# 找 CfT(跟 run.sh / go.sh 同法)
CHROME_APP="Google Chrome for Testing"
APP="${CHROME_APP_PATH:-}"
[ -d "$APP" ] || APP="$(ls -d "$HOME"/.cache/puppeteer/chrome/*/chrome-mac-arm64/"$CHROME_APP.app" 2>/dev/null | head -1 || true)"
[ -d "$APP" ] || APP="$(ls -d "$HOME"/Library/Caches/ms-playwright/chromium-*/chrome-mac*/"$CHROME_APP.app" 2>/dev/null | head -1 || true)"
[ -d "$APP" ] || { echo "✗ 找不到 CfT .app,設 CHROME_APP_PATH=... 指到 .app(npx @puppeteer/browsers install chrome)"; exit 1; }

term(){ osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}

echo "── DL 定位用違規 session:CfT + document=${APIDOM}(觸發 Domain Lock)──"
[ -x "$PY" ] || { echo "✗ venv python 不在:$PY"; exit 1; }

echo "[0] 清舊 CfT/server"
pkill -f 'chrome-mac-arm64' 2>/dev/null || true
sudo pkill -f 'routex/server.py' 2>/dev/null || true
sleep 1

echo "[1] hosts:jili 4 host + ${APIDOM} → 127.0.0.1…"
for h in $JILI_HOSTS "$APIDOM"; do
  sudo sed -i '' -E "/^[[:space:]]*127\.0\.0\.1[[:space:]].*$h/d" /etc/hosts 2>/dev/null || true
done
echo "127.0.0.1 $JILI_HOSTS $APIDOM" | sudo tee -a /etc/hosts >/dev/null
{ sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null || true
echo "    ✓ 已設 + flush DNS"

echo "[2] 開 mock(新視窗,輸密碼)…"
term "$MOCK_CMD"
printf "    等 mock listen 443"
ok=0
for _ in $(seq 1 30); do
  if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then ok=1; echo " ✓"; break; fi
  printf "."; sleep 1
done
[ "$ok" = 1 ] || { echo " ✗ mock 沒起來(看新視窗)"; exit 1; }

echo "[3] 開 CfT(--no-sandbox,Frida 才掛得上),網址 https://${APIDOM}/…"
open -n "$APP" --args --no-sandbox --user-data-dir="$PROFILE" \
  --ignore-certificate-errors --disable-quic --no-first-run --no-default-browser-check \
  --disable-features=ChromeWhatsNewUI "$URL" >/dev/null 2>&1

echo
echo "✅ 等遊戲卡在 loading(mock 視窗看到 [post?] /webservice/event/jscrambler = lock 已觸發、DomainLock 已解進記憶體),"
echo "   然後【另開終端】跑:  sudo ./.venv/bin/python dl_dump.py"
echo "   它會 scan CfT renderer 記憶體、把 DomainLock/檢查函式 source 撈出來(存 /tmp/dl_hits.txt)。"
echo "   收工:./stop.sh"
