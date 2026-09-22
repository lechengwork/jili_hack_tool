#!/usr/bin/env bash
# setup.sh — 換機器一鍵備妥環境。跑完就能 ./run.sh。
# 目標平台:macOS Apple Silicon。需先有 python3 與 node/npx。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# 釘住已驗證可用的版本(frida 版本會影響 patchwasm 的記憶體 API,務必一致)。
FRIDA_VER="17.17.0"
CRYPTO_VER="50.0.1"
CFT_VER="152.0.7977.54"      # 已驗證能跑遊戲 + Frida attach 的 Chrome for Testing build

echo "── JILI 696 route X 環境設定 ──"

# ① Python venv + 套件
command -v python3 >/dev/null || { echo "✗ 需要 python3"; exit 1; }
if [ ! -x ".venv/bin/python3" ]; then
  echo "① 建立 .venv…"
  python3 -m venv .venv
fi
echo "② 安裝 Python 套件 (frida==$FRIDA_VER, cryptography==$CRYPTO_VER, requests, ijson)…"
.venv/bin/pip install -q --upgrade pip
# frida/cryptography = 跑 mock+patch;requests = jili_login 產 token;ijson = extract_fg5 抽 netlog
.venv/bin/pip install -q "frida==$FRIDA_VER" "cryptography==$CRYPTO_VER" requests ijson

# ③ Chrome for Testing
CHROME_APP="Google Chrome for Testing"
if ls -d "$HOME"/.cache/puppeteer/chrome/*/chrome-mac-arm64/"$CHROME_APP.app" >/dev/null 2>&1; then
  echo "③ Chrome for Testing 已安裝 ✓"
elif command -v npx >/dev/null; then
  echo "③ 安裝 Chrome for Testing $CFT_VER (npx @puppeteer/browsers)…"
  npx -y @puppeteer/browsers install "chrome@$CFT_VER"
else
  echo "③ ⚠ 沒有 npx(裝 Node.js)→ 之後請自裝 CfT 或 CHROME=... 指到執行檔"
fi

# ④ /etc/hosts
HOSTS_LINE="127.0.0.1 uat-wbgame.jlfafafa3.com uat-wbwebapi.jlfafafa2.com uat-wbslot-fd.jlfafafa1.com uat-wbslot-platform.jlfafafa3.com"
if grep -q "uat-wbgame.jlfafafa3.com" /etc/hosts; then
  echo "④ /etc/hosts 已對應 ✓"
else
  echo "④ 加入 /etc/hosts (需 sudo,可能問密碼)…"
  echo "$HOSTS_LINE" | sudo tee -a /etc/hosts >/dev/null
  { sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null || true
  echo "  ✓ 已加入 + flush DNS"
fi

echo
echo "✅ 環境就緒。接下來:  ./run.sh   (收工 ./stop.sh)"
