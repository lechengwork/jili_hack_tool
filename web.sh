#!/usr/bin/env bash
# web.sh — 一鍵開啟 JILI 696【純網頁版】mock(免 Frida、免 CfT、免 patchwasm)。
#
# 原理:server 用 INJECT_BUNDLE=1 把 wasm-patch shim prepend 進 polyfills.bundle 的內容
#       (HTML 一字不改、不加新 <script>)。瀏覽器載 wasm 時,在「編譯前」就把 8 個內建
#       server 公鑰換成 mock 的 → 遊戲自己導的 X25519 shared 天生就對、Ed25519 驗簽也過。
#       所以不需要 Frida 搶時序,普通 Chrome 就能跑。原理詳見 memory: jili-patch-mechanism-solved。
#
# 你只要:打 ./web.sh → 在跳出的 mock 視窗輸一次 Mac 密碼(443 要 sudo)→ 其餘全自動。
#   ① 確保 /etc/hosts 對應(缺就自動加 + flush DNS)
#   ② 開 mock(新視窗,sudo,INJECT_BUNDLE=1)→ 等它 listen 443
#   ③ 開「普通 Google Chrome」(拋棄式 profile,不用 Frida/CfT/--no-sandbox)
#
# 盯 mock 視窗:出現 `compile d=8`(crypto 被 patch)+ `kind=init[...]` = 通、可以玩。
# 收工:./stop.sh(停 mock);本腳本開的 Chrome 直接關視窗即可(不會動到你日常的 Chrome)。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # self-locating:repo 搬到哪都能跑
PY="$ROOT/.venv/bin/python3"

# 普通 Google Chrome(非 CfT)。env override 優先:CHROME=/path/to/chrome ./web.sh
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"

# 拋棄式 profile:避開真網域的 HSTS / 舊 service worker,也把 --ignore-certificate-errors
# 這個全域(整個瀏覽器 session 不驗憑證)的危險 flag 關在一次性 profile 裡,不碰你日常 profile。
PROFILE="/tmp/jili-web-profile-$(date +%s)"
URL='https://uat-wbgame.jlfafafa3.com/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0'

MOCK_CMD="cd $ROOT && sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 .venv/bin/python3 routex/server.py"

term() {  # 開一個新 Terminal 視窗跑 "$1"
  osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}

echo "── JILI 696 純網頁版一鍵啟動(免 Frida)──"

# ── preflight ──
[ -x "$PY" ]                    || { echo "✗ 找不到 venv python:$PY"; exit 1; }
[ -f "$ROOT/routex/server.py" ] || { echo "✗ 找不到 routex/server.py"; exit 1; }
[ -x "$CHROME" ]               || { echo "✗ 找不到普通 Google Chrome:$CHROME(可設 CHROME=... 指到執行檔)"; exit 1; }

# ① /etc/hosts — 只認「未註解的 127.0.0.1 對應」= mock 生效中;go.sh(B 擷取)會移除它,所以缺了就自動加回。
HOSTS_LINE="127.0.0.1 uat-wbgame.jlfafafa3.com uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com"
if ! grep -qE '^[[:space:]]*127\.0\.0\.1[[:space:]].*uat-wbgame\.jlfafafa3\.com' /etc/hosts; then
  echo "① /etc/hosts 缺 mock 對應 → 自動加入(需 sudo,可能問密碼)…"
  echo "$HOSTS_LINE" | sudo tee -a /etc/hosts >/dev/null
  { sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null || true   # macOS 要 flush DNS
  echo "   ✓ 已加入 /etc/hosts + flush DNS"
else
  echo "① /etc/hosts 對應已在 ✓"
fi

# ② mock — 若 443 已在服務就重用,否則開新視窗跑(INJECT_BUNDLE=1)
if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then
  echo "② mock 已在 443 服務中 → 重用 ✓"
  echo "   (若那是用 run.sh 起的 Frida 版 mock、非 INJECT_BUNDLE → 請先 ./stop.sh 再跑本腳本)"
else
  echo "② 啟動 mock(新視窗,請在該視窗輸入 Mac 密碼)…"
  term "$MOCK_CMD"
  printf "   等 mock listen 443"
  ok=0
  for _ in $(seq 1 30); do
    if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then ok=1; echo " ✓"; break; fi
    printf "."; sleep 1
  done
  [ "$ok" = 1 ] || { echo " ✗ mock 沒起來(看新視窗:常見 443 被占用 / 密碼沒輸 / venv 缺套件)"; exit 1; }
fi

# ③ browser — 普通 Chrome、拋棄式 profile、自簽憑證放行、關 QUIC(mock 只聽 TCP);不用 --no-sandbox
rm -rf /tmp/jili-web-profile-* 2>/dev/null || true   # 清掉舊的拋棄式 profile,免得 /tmp 越積越多
echo "③ 開普通 Google Chrome(拋棄式 profile,免 Frida/CfT)…"
"$CHROME" \
  --user-data-dir="$PROFILE" \
  --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check \
  --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 完成。盯【mock 視窗】:看到 compile d=8(crypto 被 patch)+ kind=init[...] = 通了、可以玩。"
echo "   ⚠ 別開 DevTools(觸發 Jscrambler 反除錯會弄壞遊戲,且與其他死法難分)。"
echo "   收工:./stop.sh(停 mock);本腳本開的 Chrome 直接關視窗即可。"
