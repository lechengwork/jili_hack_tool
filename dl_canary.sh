#!/usr/bin/env bash
# dl_canary.sh — 【Phase 0 最後未測的閘】測「改 bundle.24017.js 內容會不會觸發 Jscrambler 自毀」。
#
# 為什麼在 jlfafafa(合法域)跑:baseline 本來就會通(domain lock 不 fire),所以這裡唯一的變因就是
# 「往 bundle.24017 前面 prepend 一句無害 beacon」。若遊戲照常通 = bundle.24017 可改 → serve-modify
# patch(把 case 13 的 B$Τ() 反制 no-op / 強制檢查回傳 allowed)這條路開;若遊戲壞掉/卡 = 有自我校驗。
#
# 判讀(mock 視窗):
#   • [shim-report] CANARY bundle.24017 ran  且  compile d=8 + kind=init[...](= baseline 通)
#       → ★bundle.24017 可安全 serve-modify★ → 回報我,我出 patch。
#   • CANARY ran 有印,但遊戲卡/沒 init/自毀 → bundle.24017 有完整性校驗 → serve-modify 死。
#   • 連 CANARY ran 都沒印 → path 沒對到(不該發生,CANARY_TARGET=bundle.24017 會 match 該檔)。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
PROFILE="/tmp/jili-canary-$(date +%s)"
# ★合法域★:document = jlfafafa（domain lock 會 pass），隔離出「改 bundle.24017」單一變因。
URL='https://uat-wbgame.jlfafafa3.com/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0'
# 跟 web.sh 一樣的 baseline，只多 CANARY_TARGET=bundle.24017（獨立於主 wasm shim 的探針）。
MOCK_CMD="cd $ROOT && sudo env PORT=443 TLS=1 VERBOSE=1 INJECT_BUNDLE=1 CANARY_TARGET=bundle.24017 .venv/bin/python3 routex/server.py"

term(){ osascript >/dev/null <<OSA
tell application "Terminal"
  activate
  do script "$1"
end tell
OSA
}

echo "── Phase 0:測 bundle.24017 可不可改（jlfafafa 合法域，隔離變因）──"
[ -x "$PY" ] || { echo "✗ venv python 不在:$PY"; exit 1; }
[ -x "$CHROME" ] || { echo "✗ Chrome 不在:$CHROME"; exit 1; }

echo "[0] 清舊 Chrome/server"
pkill -f 'jili-canary-' 2>/dev/null || true
sudo pkill -f 'routex/server.py' 2>/dev/null || true
sleep 1

echo "[1] /etc/hosts → jlfafafa 4 host 指 127.0.0.1（缺才加）…"
if ! grep -qE '^[[:space:]]*127\.0\.0\.1[[:space:]].*uat-wbgame\.jlfafafa3\.com' /etc/hosts; then
  echo "127.0.0.1 uat-wbgame.jlfafafa3.com uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com" | sudo tee -a /etc/hosts >/dev/null
  { sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null || true
  echo "    ✓ 已加 + flush DNS"
else echo "    ✓ 已在"; fi

echo "[2] 開 mock + CANARY（新視窗，輸密碼）…"
term "$MOCK_CMD"
printf "    等 mock listen 443"
ok=0
for _ in $(seq 1 30); do
  if curl -sk -o /dev/null --max-time 1 https://127.0.0.1/ 2>/dev/null; then ok=1; echo " ✓"; break; fi
  printf "."; sleep 1
done
[ "$ok" = 1 ] || { echo " ✗ mock 沒起來（看新視窗）"; exit 1; }

echo "[3] 開 Chrome（jlfafafa 合法域，★別開 DevTools★）…"
rm -rf /tmp/jili-canary-* 2>/dev/null || true
"$CHROME" --user-data-dir="$PROFILE" --ignore-certificate-errors --disable-quic \
  --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI \
  "$URL" >/dev/null 2>&1 &

echo
echo "✅ 盯【mock 視窗】:"
echo "   • [shim-report] CANARY bundle.24017 ran  +  compile d=8 + kind=init[...]  = ★可改★ → serve-modify 開路"
echo "   • CANARY ran 有印但遊戲卡/沒 init                                          = bundle.24017 有自我校驗 → serve-modify 死"
echo "   把這兩點的結果貼回來 → 決定要不要出 patch。收工:./stop.sh"
