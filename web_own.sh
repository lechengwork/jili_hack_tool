#!/usr/bin/env bash
# web_own.sh — 用「你自己的域名」跑 JILI 696(本地 mock)。
#   原理:路徑④——為你的 base 域名鑄一個「murmur3 撞中 domain-lock 白名單」的子網域,
#   遊戲部署在其下 → DomainLock 讀真 location.hostname 就撞中允許值、合法放行,bundle 零改。
#   (對照 web.sh:那支是假裝已白名單的 uat-wbgame.jlfafafa3.com;本支是用你自己的域名。)
#
# 免 sudo:mock 開在 8443、用 Chrome --host-resolver-rules 把域名映到 mock(不改 /etc/hosts)。
#
# 用法:  ./web_own.sh [你的base域名] [漂亮前綴]
#          ./web_own.sh dyson4092.com            → 隨機 label
#          ./web_own.sh dyson4092.com fortune    → fortune<短隨機尾>.dyson4092.com
#   收工:./stop.sh(或直接關 Chrome 視窗 + mock 視窗)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$ROOT/.venv/bin/python3"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
BASE="${1:-myjili.example.com}"
PREFIX="${2:-}"
PORT=8443
PROFILE="/tmp/jili-own-profile-$(date +%s)"

[ -x "$PY" ]     || { echo "✗ 找不到 venv python:$PY"; exit 1; }
[ -x "$CHROME" ] || { echo "✗ 找不到 Google Chrome(可設 CHROME=... )"; exit 1; }

# ① 為 base 鑄一個撞中白名單的子網域(有前綴走 pretty,否則隨機 label)
if [ -n "$PREFIX" ]; then
  echo "① 為 base 域名鑄撞中子網域:$BASE(前綴 '$PREFIX')…"
  HOST="$("$PY" "$ROOT/routex/dl_domlock_solve.py" pretty "$BASE" "$PREFIX" | awk '/✓/{print $2;exit}')"
else
  echo "① 為 base 域名鑄撞中子網域:$BASE …"
  HOST="$("$PY" "$ROOT/routex/dl_domlock_solve.py" preimage "$BASE" 1 | awk '/=> /{for(i=1;i<=NF;i++)if($i=="=>"){print $(i+1);exit}}')"
fi
[ -n "${HOST:-}" ] || { echo "✗ 鑄子網域失敗"; exit 1; }
# 驗證(離線 murmur):確認真的撞中
"$PY" "$ROOT/routex/dl_domlock_solve.py" verify "$HOST" | sed 's/^/   /'
echo "   → 遊戲域名 = $HOST"

URL="https://${HOST}/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0"

# ② mock（8443,免 sudo;INJECT_BUNDLE=1:crypto shim 進 polyfills,不動 bundle.24017）
term() { osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}
if curl -sk -o /dev/null --max-time 1 "https://127.0.0.1:${PORT}/" 2>/dev/null; then
  echo "② mock 已在 ${PORT} 服務中 → 重用 ✓"
  [ -n "${REPLAY:-}${REPLAY_SPINS:-}" ] && echo "   ⚠ 既有 mock 未必吃你這次的 REPLAY;要換重播資料請先 ./stop.sh 再跑。"
else
  echo "② 啟動 mock(新視窗,免密碼)…"
  # ★所有 REPLAY* 都要顯式轉發★:mock 開在另一個 Terminal 視窗,不會繼承你這裡的環境。
  PASS=""
  for _v in REPLAY REPLAY_SPINS REPLAY_ROUNDS; do
    eval "_val=\${$_v:-}"
    [ -n "$_val" ] && PASS="$PASS $_v=$_val"
  done
  [ -n "$PASS" ] && echo "   轉發給 mock 的環境變數:$PASS"
  term "cd $ROOT && PORT=$PORT TLS=1 VERBOSE=1 INJECT_BUNDLE=1$PASS .venv/bin/python3 routex/server.py"
  printf "   等 mock listen ${PORT}"
  for _ in $(seq 1 30); do
    curl -sk -o /dev/null --max-time 1 "https://127.0.0.1:${PORT}/" 2>/dev/null && { echo " ✓"; break; }
    printf "."; sleep 1
  done
fi

# ③ Chrome:所有域名(含撞中子網域)映到 mock;拋棄式 profile;不驗憑證;關 QUIC
rm -rf /tmp/jili-own-profile-* 2>/dev/null || true
echo "③ 開 Chrome(域名=$HOST,拋棄式 profile)…"
"$CHROME" --user-data-dir="$PROFILE" \
  --host-resolver-rules="MAP * 127.0.0.1:${PORT}" \
  --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 完成。你的域名 = $HOST"
echo "   盯 mock 視窗:看到 kind=init[...] 且【沒有】/webservice/event/jscrambler(DomainLock)= 過了、可以玩。"
echo "   ⚠ 別開 DevTools(觸發 Jscrambler)。收工:./stop.sh 或直接關視窗。"