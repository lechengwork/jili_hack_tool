#!/bin/bash
# 帶 netlog(Everything,含 body)開 CfT,供擷取明文請求。用法: ./run_cft_netlog.sh "<game_url>"
URL="$1"; [ -z "$URL" ] && { echo "用法: ./run_cft_netlog.sh \"<game_url>\""; exit 1; }
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHROME_APP="Google Chrome for Testing"
CFT="${CHROME:-}"
[ -x "$CFT" ] || CFT="$(ls -d "$HOME"/.cache/puppeteer/chrome/*/chrome-mac-arm64/"$CHROME_APP.app"/Contents/MacOS/"$CHROME_APP" 2>/dev/null | head -1)"
[ -x "$CFT" ] || CFT="$(ls -d "$HOME"/Library/Caches/ms-playwright/chromium-*/chrome-mac*/*.app/Contents/MacOS/* 2>/dev/null | head -1)"
[ -x "$CFT" ] || { echo "✗ 找不到 CfT,設 CHROME=... 指到執行檔"; exit 1; }
PROF=/tmp/cft_jili_nl; NL="$ROOT/games/696/netlog_req.json"
pkill -f 'cft_jili_nl' 2>/dev/null; sleep 1; rm -rf "$PROF"; rm -f "$NL"
echo "[netlog] → $NL"
"$CFT" --no-sandbox --user-data-dir="$PROF" --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI \
  --log-net-log="$NL" --net-log-capture-mode=Everything \
  "$URL" >/tmp/cft_nl.log 2>&1 &
echo "[netlog] CfT pid $! —— 進遊戲、設定、spin;抓夠了『關掉 Chrome 視窗』(讓 netlog 收尾寫檔)"
wait $!
