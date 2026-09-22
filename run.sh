#!/usr/bin/env bash
# run.sh — 全自動啟動 JILI 696 route X mock harness。
# 你只要:打 ./run.sh → 在跳出的兩個視窗各輸一次 Mac 密碼 → 其餘全自動。
#   ① 開 mock(新視窗,sudo) → 等它 listen 443
#   ② 開 CfT 遊戲 → 輪詢 renderer 直到載好(RSS≥SETTLE_MB)
#   ③ 自動開 patchwasm(新視窗,sudo) → 等它就緒(/tmp/jili-patchwasm-ready)
#   ④ 自動 reload 遊戲 → 觸發被 FIX_SHARED 蓋對的新 handshake
# 盯 mock 視窗出現 kind=init[1] = 通。解法原理見 memory: jili-patch-mechanism-solved。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # self-locating: works wherever the repo lives
PY="$ROOT/.venv/bin/python3"
CHROME_APP="Google Chrome for Testing"
# CfT: env override wins; else pinned path; else auto-detect any installed puppeteer CfT version.
CHROME="${CHROME:-/Users/dyson/.cache/puppeteer/chrome/mac_arm-152.0.7977.54/chrome-mac-arm64/$CHROME_APP.app/Contents/MacOS/$CHROME_APP}"
if [ ! -x "$CHROME" ]; then
  CHROME="$(ls -d "$HOME"/.cache/puppeteer/chrome/*/chrome-mac-arm64/"$CHROME_APP.app"/Contents/MacOS/"$CHROME_APP" 2>/dev/null | head -1 || true)"
fi
PROFILE="/tmp/jili-cft-profile"
READY="/tmp/jili-patchwasm-ready"
SETTLE_MB="${SETTLE_MB:-300}"    # renderer RSS(MB)到這值視為載好;可覆寫 SETTLE_MB=350 ./run.sh
URL='https://uat-wbgame.jlfafafa3.com/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0'

MOCK_CMD="cd $ROOT && sudo env PORT=443 TLS=1 VERBOSE=1 SSO_DELAY=4 HS_DELAY=8 .venv/bin/python3 routex/server.py"
PATCH_CMD="cd $ROOT && sudo SECS=300 FIX_SHARED=1 .venv/bin/python patchwasm.py"

term() {  # open a new Terminal window running "$1"
  osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}

renderer_mb() {  # biggest CfT renderer RSS in MB, 0 if none
  ps aux 2>/dev/null | awk '
    /--type=renderer/ && (/Chrome for Testing/ || /chrome-mac-arm64/) { if ($6+0 > max) max=$6 }
    END { printf "%d", (max+0)/1024 }'
}

echo "── JILI 696 route X 全自動啟動 ──"

# ── preflight ──
[ -x "$PY" ]                    || { echo "✗ 找不到 venv python: $PY"; exit 1; }
[ -f "$ROOT/routex/server.py" ] || { echo "✗ 找不到 routex/server.py"; exit 1; }
[ -f "$ROOT/patchwasm.py" ]     || { echo "✗ 找不到 patchwasm.py"; exit 1; }
HOSTS_LINE="127.0.0.1 uat-wbgame.jlfafafa3.com uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com"
# 只認「未註解的 127.0.0.1 對應」= mock 生效中;go.sh(B 擷取)會移除它,所以這裡沒有就自動加回。
if ! grep -qE '^[[:space:]]*127\.0\.0\.1[[:space:]].*uat-wbgame\.jlfafafa3\.com' /etc/hosts; then
  echo "  /etc/hosts 缺 mock 對應 → 自動加入(需 sudo,可能問密碼)…"
  echo "$HOSTS_LINE" | sudo tee -a /etc/hosts >/dev/null
  { sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null || true  # macOS 要 flush DNS
  echo "  ✓ 已加入 /etc/hosts + flush DNS"
fi
[ -x "$CHROME" ] || { echo "✗ 找不到 Chrome for Testing。裝一個:npx @puppeteer/browsers install chrome  或設 CHROME=... 指到執行檔"; exit 1; }
# 標記檔由 root(sudo patchwasm)建立,sticky /tmp 下一般權限刪不掉 → 不刪它,改成只信任
# 「run.sh 啟動之後才被更新」的標記(比對 mtime),自然忽略上一輪的舊檔。
START="$(date +%s)"

# 清掉上一輪殘留的 CfT(否則視窗越開越多,且會干擾 patchwasm 掛到正確 renderer)。
# 'chrome-mac-arm64' 只中 CfT,不動你正常的 Google Chrome。
if pgrep -f 'chrome-mac-arm64' >/dev/null 2>&1; then
  echo "  清掉殘留的 CfT 視窗…"
  pkill -f 'chrome-mac-arm64' 2>/dev/null || true
  sleep 1
fi

# ① mock
echo "① 啟動 mock(新視窗,請在該視窗輸入 Mac 密碼)…"
term "$MOCK_CMD"
printf "   等 mock listen 443"
for _ in $(seq 1 30); do
  if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then echo " ✓"; break; fi
  printf "."; sleep 1
done

# ② game
echo "② 開 CfT 遊戲(--no-sandbox,專用 profile)…"
"$CHROME" --no-sandbox --user-data-dir="$PROFILE" --ignore-certificate-errors "$URL" >/dev/null 2>&1 &
printf "   等遊戲載入(RSS≥%sMB)" "$SETTLE_MB"
mb=0
for _ in $(seq 1 120); do
  mb=$(renderer_mb)
  if [ "$mb" -ge "$SETTLE_MB" ]; then echo " ✓ (${mb}MB)"; break; fi
  printf "."; sleep 1
done
[ "$mb" -ge "$SETTLE_MB" ] || echo " (逾時,RSS 只到 ${mb}MB,仍繼續)"

# ③ patcher
echo "③ 自動啟動 patchwasm(新視窗,請在該視窗再輸一次密碼)…"
term "$PATCH_CMD"
printf "   等 patcher 就緒(attach+FIX_SHARED)"
ready=0
for _ in $(seq 1 60); do
  if [ -f "$READY" ]; then
    mt="$(stat -f %m "$READY" 2>/dev/null || echo 0)"   # 只認這一輪(mtime≥START)才更新的標記
    if [ "${mt:-0}" -ge "$START" ]; then ready=1; echo " ✓"; break; fi
  fi
  printf "."; sleep 1
done
[ "$ready" = 1 ] || echo " (逾時未就緒;若視窗A沒 changed=8,見下方排錯)"

# ④ auto reload → fresh decryptable handshake
echo "④ 自動 reload 遊戲觸發新 handshake…"
if osascript -e "tell application \"$CHROME_APP\" to reload active tab of window 1" 2>/dev/null; then
  echo "   ✓ 已 reload"
elif osascript -e 'tell application "System Events" to keystroke "r" using command down' 2>/dev/null; then
  echo "   ✓ 已送 Cmd-R"
else
  echo "   ⚠ 自動 reload 失敗(缺自動化權限?)→ 請手動對遊戲視窗按 Cmd-R"
fi

echo
echo "✅ 完成。盯【mock 視窗】:handshake 不再迴圈、出現 kind=init[1] = 通了。"
echo "   若 ~15 秒沒動,手動對遊戲 Cmd-R 一次即可。收工:./stop.sh"
