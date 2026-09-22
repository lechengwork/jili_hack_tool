#!/usr/bin/env bash
# webmock_domain.sh — 證明「wasm 反轉出來的 API host 是非 jili 網域也照樣過」。
#
# 設計:其餘全部照「已知會通的 jili mock」不動(document/遙測/assets 都走 jili host → localhost,
#      這組合 web.sh 已驗證能到 handshake),★只把 be/gs 換成一個非 jili 網域★——這正是遊戲會
#      「反轉→拿去打 sso / /fg5/req」的那兩個 host。若還能 handshake(mock log 出現 [sso] +
#      [fg5] kind=handshake→init[...])→ 證明前端不檢查「反轉出來是不是 jili 網域」,你能換自己的 API 網域。
#
# 用法:./webmock_domain.sh [myslot.test]   別開 DevTools;收工 ./stop.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
APIDOM="${1:-myslot.test}"                          # 一個明顯不是 jili 的 API 網域
PROFILE="/tmp/jili-domtest-profile-$(date +%s)"
REV=$(printf '%s' "$APIDOM" | rev)                 # be/gs = 這個網域的反轉

# 4 個 jili host(document/sso/gs/platform)照 web.sh 全指 localhost;再加自訂 API 網域。
JILI_HOSTS="uat-wbgame.jlfafafa3.com uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com"
# game_url:★連 document(網址列本身)也換成 ${APIDOM}★ + be/gs/domain_platform 都是它的反轉。
# domain_gs 先留 jili 值、jili host 也留在 hosts 當保險(隔離變因,先證 document 能換)。
URL="https://$APIDOM/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=$REV&domain_gs=1afafaflj&domain_platform=$REV&gameID=696&gs=$REV&iu=true&legalLang=true&skin=0"
MOCK_CMD="cd $ROOT && sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 .venv/bin/python3 routex/server.py"

term(){ osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}

echo "── 測: 連 document(網址列)都換成非 jili 網域 ${APIDOM} (be/gs/domain_platform 也是它的反轉 ${REV}) ──"
echo "   網址列會是 https://${APIDOM}/fg5/…;document + sso + fg5 + 遙測 全打到它 (-> 127.0.0.1 mock)"
[ -x "$PY" ] || { echo "✗ venv python 不在:$PY"; exit 1; }
[ -x "$CHROME" ] || { echo "✗ Chrome 不在:$CHROME"; exit 1; }

echo "[0] 清舊 Chrome/server"
pkill -f 'jili-domtest-profile' 2>/dev/null || true
sudo pkill -f 'routex/server.py' 2>/dev/null || true
sleep 1

echo "[1] hosts:4 個 jili host + ${APIDOM} 全 → 127.0.0.1…"
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

echo "[3] 開 Chrome…"
"$CHROME" --user-data-dir="$PROFILE" --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 看【瀏覽器網址列 = https://${APIDOM}/…】+【mock 視窗】:"
echo "   ★網址列是你的網域、且出現 [GET] / + [sso] + [fg5] kind=handshake→init[...] 且可玩 = document 也能換自己網域★"
echo "   → 連網址列(document)都能是自己域名 = 整站可部署到你自己網域,uat-wbgame 只是我們一直沿用的、非必需。"
echo "   (domain_gs 這版先留 jili 值 + jili host 當保險;若這樣能玩,剩 domain_gs 是否要一起換是最後的小細節。)"
echo "   收工:./stop.sh;回原 jili mock:./web.sh(會自動修 hosts)。"
