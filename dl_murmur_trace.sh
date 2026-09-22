#!/usr/bin/env bash
# dl_murmur_trace.sh — Phase 3(a):抓 code-integrity 的 MurmurHash3 實際輸入(О_O.toString())+ 切窗方案。
#
# 跑【合法域 uat-wbgame.jlfafafa3.com】讓遊戲完整載入 → 所有整完性檢查(可能多個、延遲觸發)都會跑到,
# 且沒有 domain-lock halt 噪音。EXTRA_SHIM=dl_murmur_trace_shim.js 從 polyfills 最先掛,純側錄:
#   • hook substring/slice/substr → 抓被切的長字串 f0Ο(=被檢查函式的源碼)+ 每個(off,size)視窗
#   • hook charCodeAt → 確認逐位元組讀
# ★不改任何 byte、不碰 eval/FPT。★別開 DevTools(會觸發 Jscrambler)。
#
# 收工:把 mock 視窗所有  ★★★ [shim-report] ... MURMUR ...  行貼回來。我用 routex/dl_murmur_verify.py 對上本地原始檔。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
SHIM="${SHIM:-dl_murmur_trace_shim.js}"
# ★ 持久 profile:固定路徑 → 登入狀態(遊戲站/ChatGPT 等)跨次保留,不再每跑全清。
#   要強制乾淨 profile 時:JILI_PROFILE=/tmp/jili-clean-$(date +%s) ./dl_murmur_trace.sh
#   bundle 不吃快取靠:server no-store 標頭 + 下方 Chrome --disk-cache-size=1。
PROFILE="${JILI_PROFILE:-$HOME/.jili-test-profile}"
JILI_HOSTS="uat-wbgame.jlfafafa3.com uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com"
# 合法域正規啟動 URL(同 web.sh)——domain lock 會 pass,遊戲完整載入,整完性走 happy path。
URL='https://uat-wbgame.jlfafafa3.com/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0'
MOCK_CMD="cd $ROOT && sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 EXTRA_SHIM=$SHIM .venv/bin/python3 routex/server.py"

term(){ osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}

echo "── Phase 3(a):MurmurHash3 整完性輸入追蹤(合法域,完整載入)+ EXTRA_SHIM=${SHIM} ──"
[ -x "$PY" ]     || { echo "✗ venv python 不在:$PY"; exit 1; }
[ -x "$CHROME" ] || { echo "✗ Chrome 不在:$CHROME(可 CHROME=... 覆寫)"; exit 1; }
[ -f "$ROOT/routex/$SHIM" ] || { echo "✗ 找不到 routex/$SHIM"; exit 1; }

echo "[0] 清舊 mock server(★不動你的持久 profile Chrome:保住登入/分頁★)"
# 只殺【舊的臨時 profile】Chrome(名字含 jili-murmur-),持久 profile($HOME/.jili-test-profile)不匹配→不會被殺。
pkill -f 'jili-murmur-' 2>/dev/null || true
sudo pkill -f 'routex/server.py' 2>/dev/null || true
sleep 1

echo "[1] hosts:jili 4 host → 127.0.0.1…"
for h in $JILI_HOSTS; do
  sudo sed -i '' -E "/^[[:space:]]*127\.0\.0\.1[[:space:]].*$h/d" /etc/hosts 2>/dev/null || true
done
echo "127.0.0.1 $JILI_HOSTS" | sudo tee -a /etc/hosts >/dev/null
{ sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null || true
echo "    ✓ 已設 + flush DNS"

echo "[2] 開 mock + EXTRA_SHIM(新視窗,輸密碼)…"
if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then
  echo "    ⚠ 443 已在服務——若非本腳本的 INJECT_BUNDLE+EXTRA_SHIM 版,請先 ./stop.sh 再跑"
else
  term "$MOCK_CMD"
  printf "    等 mock listen 443"
  ok=0
  for _ in $(seq 1 30); do
    if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then ok=1; echo " ✓"; break; fi
    printf "."; sleep 1
  done
  [ "$ok" = 1 ] || { echo " ✗ mock 沒起來(看新視窗)"; exit 1; }
fi

echo "[3] 開 Chrome(持久 profile:$PROFILE,★別開 DevTools★)…"
# --disk-cache-size=1 幾乎停用磁碟快取 → 持久 profile 也不會載到舊 patch 的 bundle(配合 server no-store)。
# 若該 profile 的 Chrome 已開著,這行會在既有視窗開新分頁(不會清掉你的登入/其他分頁)。
"$CHROME" --user-data-dir="$PROFILE" --ignore-certificate-errors --disable-quic \
  --disk-cache-size=1 --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 等遊戲載入(進到轉盤畫面代表整完性都跑過了),看【mock 視窗】的 ★★★ [shim-report] MURMUR 行,重點:"
echo "   • MURMUR BIGSTR via=... len=... fnv=...        → 每個被雜湊的長字串(=被檢查函式源碼)的識別"
echo "   • MURMUR BIGSTR-head / -tail \"...\"             → 頭尾 48 字(拿去 grep 定位是 bundle 哪個函式)"
echo "   • MURMUR WIN substring cs=... off=... size=...  → 切窗方案(off 步幅/視窗數;確認是否 25000)"
echo "   • MURMUR CCA-scan cs=... min=.. max=.. count=..  → 逐位元組掃描確認"
echo "   把這些行整段貼回來 → 我用 dl_murmur_verify.py:"
echo "     ./routex/dl_murmur_verify.py grep '<head 可見片段>'   # 定位是哪個函式"
echo "     ./routex/dl_murmur_verify.py fnv <off> <len>          # 對上 runtime fnv,證實我有精確 bytes"
echo "   收工:./stop.sh"
