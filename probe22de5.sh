#!/usr/bin/env bash
# probe22de5.sh — 實測「改 index.22de5.js 內容會不會觸發 Jscrambler 自毀」。
#
# 用 jili 網域跑(把 Domain Lock 這個變因排除),pubkey patch 照舊在 polyfills(遊戲能正常到 init),
# 額外往 index.22de5.js 內容前面塞一句「什麼都不做的 beacon」(CANARY_TARGET=index.22de5)。
# 判讀(看 mock 視窗):
#   • 出現 [canary] prepended … + [shim-report] CANARY index.22de5 ran + 照樣 [fg5] handshake→init 可玩
#       → ★22de5 內容「可改、不自毀」→ 你的「patch 檢查」想法有戲(下一步:找到檢查點再 patch)★
#   • 遊戲卡住 / 沒到 init → 22de5 一改就自毀 → 硬 patch 這條確認難。
# 注意:prepend(塞在最前面)未必動到「受保護函式」的 toString → 就算 survive,也還要再測「改函式內部」。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
PROFILE="/tmp/jili-probe22-profile-$(date +%s)"
JILI_HOSTS="uat-wbgame.jlfafafa3.com uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com"
URL='https://uat-wbgame.jlfafafa3.com/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0'
MOCK_CMD="cd $ROOT && sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 CANARY_TARGET=index.22de5 .venv/bin/python3 routex/server.py"

term(){ osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}

echo "── 探測:改 index.22de5.js 內容(canary)+ jili 網域跑,看會不會自毀 ──"
[ -x "$PY" ] || { echo "✗ venv python 不在:$PY"; exit 1; }
[ -x "$CHROME" ] || { echo "✗ Chrome 不在:$CHROME"; exit 1; }

echo "[0] 清舊 Chrome/server"
pkill -f 'jili-probe22-profile' 2>/dev/null || true
sudo pkill -f 'routex/server.py' 2>/dev/null || true
sleep 1

echo "[1] hosts:4 個 jili host → 127.0.0.1(用 jili 網域,排除 Domain Lock 變因)…"
for h in $JILI_HOSTS; do
  sudo sed -i '' -E "/^[[:space:]]*127\.0\.0\.1[[:space:]].*$h/d" /etc/hosts 2>/dev/null || true
done
echo "127.0.0.1 $JILI_HOSTS" | sudo tee -a /etc/hosts >/dev/null
{ sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null || true
echo "    ✓ 已設 + flush DNS"

echo "[2] 開 mock + CANARY(新視窗,輸密碼)…"
term "$MOCK_CMD"
printf "    等 mock listen 443"
ok=0
for _ in $(seq 1 30); do
  if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then ok=1; echo " ✓"; break; fi
  printf "."; sleep 1
done
[ "$ok" = 1 ] || { echo " ✗ mock 沒起來(看新視窗)"; exit 1; }

echo "[3] 開 Chrome(jili 網址)…"
"$CHROME" --user-data-dir="$PROFILE" --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 看【mock 視窗】:"
echo "   • [canary] prepended … + [shim-report] CANARY index.22de5 ran = 我們的碼塞進 22de5 且執行了"
echo "   • 若接著照樣 [fg5] … kind=handshake → init[...] 可玩 = ★22de5 內容可改、沒自毀 → patch 檢查有戲★"
echo "   • 若卡住 / 沒到 init = 22de5 一改就自毀 → 硬 patch 難"
echo "   收工:./stop.sh(本探測 Chrome:pkill -f jili-probe22-profile)。"
echo "   ★把 [canary]、CANARY … ran、有沒有到 [fg5] 貼給 Claude 判讀。"
