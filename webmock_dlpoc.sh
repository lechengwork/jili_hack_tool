#!/usr/bin/env bash
# webmock_dlpoc.sh — 【Domain Lock 破解 PoC】document 用非 jili 網域,靠 dl_probe_shim 偽裝 location 探能不能破。
#
# 跟 webmock_domain.sh 一樣把整站(含 document)換成 ${APIDOM},但 server 多開 DLPROBE=1:
#   → 在 mock patch shim 前再 prepend dl_probe_shim.js,從 polyfills 偽裝 location 網域成 jili。
# 判讀:
#   • mock 視窗 [shim-report] DLPROBE OK/FAIL = 哪些 location 讀取點攔得到。
#   • 若出現 [sso] + [fg5] kind=handshake→init 且可玩 = ★Domain Lock 被騙過 = 可破★。
#   • 若仍卡 loading = Lock 讀不可偽造的 location.hostname/href → 需更深 RE(老實回報)。
# jili host 也留在 hosts 當保險(dl_probe 把 baseURI 等偽裝成 jili host 時,資產仍能 →localhost)。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
APIDOM="${1:-myslot.test}"
PROFILE="/tmp/jili-dlpoc-profile-$(date +%s)"
REV=$(printf '%s' "$APIDOM" | rev)
JILI_HOSTS="uat-wbgame.jlfafafa3.com uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com"
URL="https://$APIDOM/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=$REV&domain_gs=1afafaflj&domain_platform=$REV&gameID=696&gs=$REV&iu=true&legalLang=true&skin=0"
MOCK_CMD="cd $ROOT && sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 DLPROBE=1 .venv/bin/python3 routex/server.py"

term(){ osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}

echo "── Domain Lock 破解 PoC:document=${APIDOM}(非 jili)+ dl_probe 偽裝 location ──"
[ -x "$PY" ] || { echo "✗ venv python 不在:$PY"; exit 1; }
[ -x "$CHROME" ] || { echo "✗ Chrome 不在:$CHROME"; exit 1; }
[ -f "$ROOT/routex/dl_probe_shim.js" ] || { echo "✗ 找不到 routex/dl_probe_shim.js"; exit 1; }

echo "[0] 清舊 Chrome/server"
pkill -f 'jili-dlpoc-profile' 2>/dev/null || true
sudo pkill -f 'routex/server.py' 2>/dev/null || true
sleep 1

echo "[1] hosts:jili 4 host + ${APIDOM} 全 → 127.0.0.1(jili 當保險)…"
for h in $JILI_HOSTS "$APIDOM"; do
  sudo sed -i '' -E "/^[[:space:]]*127\.0\.0\.1[[:space:]].*$h/d" /etc/hosts 2>/dev/null || true
done
echo "127.0.0.1 $JILI_HOSTS $APIDOM" | sudo tee -a /etc/hosts >/dev/null
{ sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null || true
echo "    ✓ 已設 + flush DNS"

echo "[2] 開 mock+DLPROBE(新視窗,輸密碼)…"
term "$MOCK_CMD"
printf "    等 mock listen 443"
ok=0
for _ in $(seq 1 30); do
  if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then ok=1; echo " ✓"; break; fi
  printf "."; sleep 1
done
[ "$ok" = 1 ] || { echo " ✗ mock 沒起來(看新視窗)"; exit 1; }

echo "[3] 開 Chrome(網址列會是 https://${APIDOM}/…)…"
"$CHROME" --user-data-dir="$PROFILE" --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 看【mock 視窗】的 ★★★ [shim-report]:"
echo "   • DLPROBE OK/FAIL … = 哪些 location 讀取點攔得到(記下來)"
echo "   • 若接著出現 [sso] + [fg5] kind=handshake → init[...] 且可玩 = ★Domain Lock 可破(讀的是可攔截屬性)★"
echo "   • 若仍卡 loading = Lock 讀不可偽造的 location.hostname/href → 需更深 RE"
echo "   收工:./stop.sh(本 PoC Chrome:pkill -f jili-dlpoc-profile)。"
echo
echo "   ★把 mock 視窗的 DLPROBE 那幾行 + 有沒有到 [fg5] 貼給 Claude,我判讀。"
