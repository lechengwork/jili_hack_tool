#!/bin/bash
# 一鍵開遊戲:VPN關→產token→VPN開BR→開遊戲。全自動,你只要「點兩顆按鈕進遊戲 + 玩」。
# 用法:
#   bash go.sh              # 開 696,不錄 netlog(要抓 heap 回應用這個)
#   bash go.sh 696 --netlog # 開 696,錄 netlog(要抓明文請求用這個;玩完要關 Chrome 視窗)
#   bash go.sh 111          # 開別款
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
UUID="${VPN_UUID:-E2416E2B-51EA-4569-B4D9-49A7665E5BC2}"   # Surfshark WireGuard profile (override: VPN_UUID=...)
CHROME_APP="Google Chrome for Testing"
APP="${CHROME_APP_PATH:-}"
[ -d "$APP" ] || APP="$(ls -d "$HOME"/.cache/puppeteer/chrome/*/chrome-mac-arm64/"$CHROME_APP.app" 2>/dev/null | head -1)"
[ -d "$APP" ] || APP="$(ls -d "$HOME"/Library/Caches/ms-playwright/chromium-*/chrome-mac*/"$CHROME_APP.app" 2>/dev/null | head -1)"
[ -d "$APP" ] || { echo "✗ 找不到 CfT .app,設 CHROME_APP_PATH=... 指到 .app"; exit 1; }
PROF=/tmp/cft_jili_go
PY=./.venv/bin/python

GID=696; NL=0
for a in "$@"; do
  case "$a" in
    --netlog) NL=1;;
    [0-9]*) GID="$a";;
  esac
done

country(){ curl -s --max-time 6 https://ipinfo.io/json | $PY -c "import sys,json;print(json.load(sys.stdin).get('country',''))" 2>/dev/null; }
wait_country(){ local want="$1" c; for i in $(seq 1 25); do c=$(country); [ "$c" = "$want" ] && { echo "$c"; return 0; }; sleep 2; done; echo "$c"; return 1; }

echo "[0] 清乾淨舊 Chrome"
pkill -f 'chrome-mac-arm64' 2>/dev/null; pkill -f 'cft_jili_go' 2>/dev/null; sleep 1; rm -rf "$PROF"

echo "[1] VPN 關 → 等 TW (產 token 需要)..."
scutil --nc stop "$UUID" >/dev/null 2>&1
c=$(wait_country TW) || { echo "!!! 沒切成 TW (現在=$c),停"; exit 1; }
echo "    country=$c ✓"

echo "[2] 產 token (gameid=$GID)..."
$PY jili_login.py "$GID" --json > /tmp/go_login.json 2>/tmp/go_login_err.txt
URL=$($PY -c "import json;d=json.load(open('/tmp/go_login.json'));d=d[0] if isinstance(d,list) else d;print(d.get('game_url',''))" 2>/dev/null)
SSO=$($PY -c "import json,urllib.parse as u;d=json.load(open('/tmp/go_login.json'));d=d[0] if isinstance(d,list) else d;print(u.parse_qs(u.urlparse(d['game_url']).query).get('ssoKey',[''])[0])" 2>/dev/null)
[ -z "$URL" ] && { echo "!!! 產 token 失敗:"; cat /tmp/go_login_err.txt; exit 1; }
echo "    ssoKey=$SSO ✓"
echo "$URL" > /tmp/go_url.txt   # 存起來給其他工具用

echo "[3] VPN 開 → 等 BR..."
scutil --nc start "$UUID" >/dev/null 2>&1
c=$(wait_country BR) || { echo "!!! 沒切成 BR (現在=$c),停"; exit 1; }
echo "    country=$c ✓"

echo "[3.5] 移除 /etc/hosts 的 mock 對應(B 要連真 server,不能指到 127.0.0.1 的 mock)..."
if grep -qE '127\.0\.0\.1.*uat-wbgame\.jlfafafa3\.com' /etc/hosts; then
  sudo sed -i '' -E '/127\.0\.0\.1.*uat-wbgame\.jlfafafa3\.com/d' /etc/hosts
  { sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null || true  # flush DNS 快取
  echo "    ✓ 已移除 + flush DNS(之後跑 ./run.sh 用 mock 時會自動加回)"
else
  echo "    (本來就沒有 mock 對應) ✓"
fi

echo "[4] 開遊戲..."
NLFLAG=""
if [ "$NL" = "1" ]; then
  NLP="$(pwd)/games/$GID/netlog_req.json"; mkdir -p "games/$GID"; rm -f "$NLP"
  NLFLAG="--log-net-log=$NLP --net-log-capture-mode=Everything"
  echo "    (含 netlog → $NLP)"
fi
open -n "$APP" --args --no-sandbox --user-data-dir="$PROF" \
  --ignore-certificate-errors --disable-quic --no-first-run --no-default-browser-check \
  --disable-features=ChromeWhatsNewUI $NLFLAG "$URL" >/tmp/cft_go.log 2>&1

echo ""
echo "[✓] 遊戲開了。換你:點兩顆按鈕進遊戲、玩;完成後回來跟 Claude 說。"
[ "$NL" = "1" ] && echo "    ⚠ netlog 模式:玩完要『關 Chrome 視窗』,netlog 才會寫完整。"
