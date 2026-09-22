#!/usr/bin/env bash
# web_own_hub.sh — 跟 web_own.sh 一樣的玩法，但 mock 換成【jade-game-hub 的 Go jilimock】。
#   專用腳本，跟 routex 的 web_own.sh 分開，避免搞混「到底是哪個 server 在回」。
#   會用 /__whoami__ 明確確認 8443 上的是 jilimock（不是 routex）。
#
# 用法:  ./web_own_hub.sh [你的base域名] [漂亮前綴]
#   收工:關 Chrome 視窗 + jilimock 視窗。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$ROOT/.venv/bin/python3"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
HUB="${HUB:-/Users/dyson/Downloads/work/jade-game-hub}"   # jade-game-hub 專案路徑
BASE="${1:-myjili.example.com}"
PREFIX="${2:-}"
PORT=8443
PROFILE="/tmp/jili-hub-profile-$(date +%s)"

[ -x "$PY" ]     || { echo "✗ 找不到 venv python:$PY"; exit 1; }
[ -x "$CHROME" ] || { echo "✗ 找不到 Google Chrome(可設 CHROME=... )"; exit 1; }
[ -d "$HUB" ]    || { echo "✗ 找不到 jade-game-hub:$HUB(可設 HUB=... )"; exit 1; }

whoami_8443() { curl -sk --max-time 1 "https://127.0.0.1:${PORT}/__whoami__" 2>/dev/null || true; }

# ① 為 base 鑄一個撞中 domain-lock 白名單的子網域
if [ -n "$PREFIX" ]; then
  echo "① 鑄撞中子網域:$BASE(前綴 '$PREFIX')…"
  HOST="$("$PY" "$ROOT/routex/dl_domlock_solve.py" pretty "$BASE" "$PREFIX" | awk '/✓/{print $2;exit}')"
else
  echo "① 鑄撞中子網域:$BASE …"
  HOST="$("$PY" "$ROOT/routex/dl_domlock_solve.py" preimage "$BASE" 1 | awk '/=> /{for(i=1;i<=NF;i++)if($i=="=>"){print $(i+1);exit}}')"
fi
[ -n "${HOST:-}" ] || { echo "✗ 鑄子網域失敗"; exit 1; }
"$PY" "$ROOT/routex/dl_domlock_solve.py" verify "$HOST" | sed 's/^/   /'
echo "   → 遊戲域名 = $HOST"

URL="https://${HOST}/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0"

# ② 確保 8443 上是 jilimock（Go hub），不是 routex
term() { osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}
who="$(whoami_8443)"
if [ "$who" = "jilimock jade-game-hub" ]; then
  echo "② 8443 已是 jilimock(Go hub)→ 重用 ✓"
elif [ -n "$who" ] || curl -sk -o /dev/null --max-time 1 "https://127.0.0.1:${PORT}/" 2>/dev/null; then
  echo "✗ 8443 被【別的 mock】佔用(可能是 routex 的 server.py)。"
  echo "  這支腳本只跑 jilimock。請先關掉那個(routex 用 ./stop.sh)再重跑本腳本。"
  exit 1
else
  echo "② 啟動 jilimock(Go hub，新視窗)…"
  term "cd $HUB && PORT=$PORT CERT=cmd/jilimock/server.crt KEY=cmd/jilimock/server.key ./bin/jilimock"
  printf "   等 jilimock listen ${PORT}"
  for _ in $(seq 1 30); do
    [ "$(whoami_8443)" = "jilimock jade-game-hub" ] && { echo " ✓"; break; }
    printf "."; sleep 1
  done
  [ "$(whoami_8443)" = "jilimock jade-game-hub" ] || { echo; echo "✗ jilimock 沒起來(先 cd $HUB && make jilimock?)"; exit 1; }
fi

# ③ Chrome:所有域名映到 jilimock;拋棄式 profile;不驗憑證;關 QUIC
rm -rf /tmp/jili-hub-profile-* 2>/dev/null || true
echo "③ 開 Chrome(域名=$HOST → jade-game-hub)…"
"$CHROME" --user-data-dir="$PROFILE" \
  --host-resolver-rules="MAP * 127.0.0.1:${PORT}" \
  --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 完成。遊戲域名 = $HOST，mock = jade-game-hub(Go jilimock)"
echo "   盯 jilimock 視窗:[fg5] type=1→58→0 = 你的 Go server 在回、可以玩。⚠ 勿開 DevTools。"
