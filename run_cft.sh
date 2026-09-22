#!/bin/bash
# 直接開 Chrome for Testing（非 CDP，navigator.webdriver=false）跑遊戲，供 Frida attach。
# 用法: ./run_cft.sh "<game_url>"
URL="$1"
[ -z "$URL" ] && { echo "用法: ./run_cft.sh \"<game_url>\""; exit 1; }
CFT="/Users/dyson/Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
PROF=/tmp/cft_jili
pkill -f 'cft_jili' 2>/dev/null; sleep 1; rm -rf "$PROF"
echo "[CfT] 啟動（--no-sandbox 讓 renderer 可被 Frida attach）..."
"$CFT" \
  --no-sandbox \
  --user-data-dir="$PROF" \
  --ignore-certificate-errors \
  --disable-quic \
  --no-first-run --no-default-browser-check \
  --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &
echo "[CfT] pid $! —— 進遊戲確認能不能玩；Frida 用 frida_scan.py 掛上去"
wait $!
