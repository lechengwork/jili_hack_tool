#!/usr/bin/env bash
# replay.sh — 一鍵本地回放 JILI 696(免 sudo / 免改 hosts / 免鑄子網域)。
#
#   ./replay.sh                          # 播預設全部(spins_raw,循環)
#   ./replay.sh 24126-883680-00240696    # 只播這一局(可逗號多局,依序)
#
# 資料夾預設寫死:REPLAY=…/exchanges_ordered.jsonl、REPLAY_SPINS=…/spins_raw。
# 要換來源就在前面帶 env,例:REPLAY_SPINS=別的目錄 ./replay.sh
#
# 這個視窗會變成 mock 的 log(每 spin 印一次);收工按 Ctrl+C 就停,Chrome 直接關視窗。
# ★別開 DevTools★(觸發 Jscrambler)。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
PORT=8443
HOST="uat-wbgame.jlfafafa3.com"        # 本來就在 domain-lock 白名單 → 免鑄子網域

# 預設回放資料(可用 env 蓋過)
REPLAY="${REPLAY:-$ROOT/games/696/webcap/exchanges_ordered.jsonl}"
REPLAY_SPINS="${REPLAY_SPINS:-$ROOT/games/696/webcap/spins_raw}"
# 指定局號:第一個參數優先,其次 env REPLAY_ROUNDS,都沒有就播全部
ROUNDS="${1:-${REPLAY_ROUNDS:-}}"

# ── preflight ──
[ -x "$PY" ]           || { echo "✗ 找不到 venv python:$PY (先 python3 -m venv .venv && .venv/bin/pip install cryptography requests)"; exit 1; }
[ -x "$CHROME" ]       || { echo "✗ 找不到 Chrome(可設 CHROME=... )"; exit 1; }
[ -f "$REPLAY" ]       || { echo "✗ 找不到 REPLAY 檔:$REPLAY"; exit 1; }
[ -d "$REPLAY_SPINS" ] || { echo "✗ 找不到 REPLAY_SPINS 目錄:$REPLAY_SPINS"; exit 1; }

# ① 殺掉 8443 上的舊 mock —— 這是「換局不生效」的元凶(舊 mock 被重用、不吃新變數)
OLD="$(lsof -nP -iTCP:$PORT -sTCP:LISTEN -t 2>/dev/null || true)"
if [ -n "$OLD" ]; then
  echo "① 停掉 8443 上的舊 mock(PID $OLD)…"
  kill $OLD 2>/dev/null || true
  sleep 1
fi

# ② Chrome:背景等 mock listen 後自動開(這樣本視窗留給 mock log)
(
  for _ in $(seq 1 40); do
    if curl -sk -o /dev/null --max-time 1 "https://127.0.0.1:$PORT/" 2>/dev/null; then break; fi
    sleep 0.5
  done
  rm -rf /tmp/jili-replay-profile-* 2>/dev/null || true
  URL="https://${HOST}/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0"
  echo "③ 開 Chrome → $HOST(拋棄式 profile)"
  "$CHROME" --user-data-dir="/tmp/jili-replay-profile-$(date +%s)" \
    --host-resolver-rules="MAP * 127.0.0.1:$PORT" \
    --ignore-certificate-errors --disable-quic \
    --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI \
    "$URL" >/dev/null 2>&1 &
) &

# ③ 起 mock(前景;帶回放變數)—— 這個視窗就是 log,Ctrl+C 收工
if [ -n "$ROUNDS" ]; then
  echo "② 起 mock:★只播指定局★ → $ROUNDS"
else
  echo "② 起 mock:未指定局號 → 播 spins_raw 全部(循環)"
fi
echo "   (給了局號要看到「1 spin board(s)」;收工 Ctrl+C)"
echo "────────────────────────────────────────────"
exec env PORT="$PORT" TLS=1 VERBOSE=1 INJECT_BUNDLE=1 \
  REPLAY="$REPLAY" REPLAY_SPINS="$REPLAY_SPINS" \
  ${ROUNDS:+REPLAY_ROUNDS="$ROUNDS"} \
  "$PY" routex/server.py
