#!/usr/bin/env bash
# fetch_webp_mirror.sh — 補齊 mirror 的 WebP 貼圖(給非 Apple GPU 的瀏覽器,如 Windows)。
#
# 為什麼要這支:game_site_backup 是在 Mac 抓的,壓縮貼圖只存了 .astc(Apple GPU 用);
# 換到 Windows/一般 GPU 的 Chrome,Cocos 會改要同一張圖的 .webp → 本機 mirror 沒有 →
# /fg5/assets/.../<hash>.webp 一路 404 → loader 卡在 JILI splash。
# WebP 幾乎所有瀏覽器都支援,補進去後 Windows 就能載,而且之後全離線。
#
# 原理:每個 .astc 在真站都有對應的 .webp(同路徑、同 basename,只換副檔名)。
#       這支把 mirror 裡每個 .astc 的 .webp 從【真站】抓回來、存到 mirror 同位置。
#
# 前置(缺一不可):
#   1) VPN = 巴西(BR)   —— curl ipinfo 需顯示 BR
#   2) /etc/hosts 沒有把 uat-wbgame 指到 127.0.0.1(否則會抓到自己)
#      若剛跑過 webcapture/mock,手動移除那行(stop.sh 只殺 process、不清 hosts):
#        sudo sed -i '' -E '/127\.0\.0\.1[[:space:]].*uat-wbgame\.jlfafafa3\.com/d' /etc/hosts
#        sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
#
# 用法:  ./fetch_webp_mirror.sh          (預設補 uat-wbgame 的 fg5 整棵)
#        DRY=1 ./fetch_webp_mirror.sh    (只列要抓什麼,不真的抓)
# 跑完 → 重打包 zip 給同事(見結尾提示)。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PY="$ROOT/.venv/bin/python3"
HOST="${DOC_HOST:-uat-wbgame.jlfafafa3.com}"
BASE="game_site_backup/$HOST"
[ -d "$BASE/fg5" ] || { echo "✗ 找不到 $BASE/fg5"; exit 1; }

DRY="${DRY:-0}"
if [ "$DRY" != "1" ]; then
  echo "[preflight] 出口國家 / hosts 檢查…"
  c=$(curl -s --max-time 6 https://ipinfo.io/json | "$PY" -c "import sys,json;print(json.load(sys.stdin).get('country',''))" 2>/dev/null || true)
  echo "  country=$c  (需要 BR)"
  [ "$c" = "BR" ] || { echo "  ✗ 出口不是 BR,先把 Surfshark 切巴西再來"; exit 1; }
  if grep -qE "^[[:space:]]*127\.0\.0\.1[[:space:]].*$HOST" /etc/hosts; then
    echo "  ✗ /etc/hosts 把 $HOST 指到本機了 → 會抓到自己。手動移除該行再跑:"
    echo "      sudo sed -i '' -E '/127\\.0\\.0\\.1[[:space:]].*uat-wbgame\\.jlfafafa3\\.com/d' /etc/hosts"
    echo "      sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder"
    exit 1
  fi
  echo "  ✓ BR + hosts 乾淨"
fi
ok=0; skip=0; miss=0
# 列出所有壓縮貼圖(.astc),推對應 .webp;逐一從真站抓(缺才抓)。
while IFS= read -r a; do
  w="${a%.astc}.webp"
  rel="${w#"$BASE"/}"                       # 相對路徑(= URL path,去掉 host 目錄)
  if [ -f "$w" ]; then skip=$((skip+1)); continue; fi
  if [ "$DRY" = "1" ]; then echo "  would fetch  $rel"; continue; fi
  code=$(curl -sk -o "$w.tmp" -w "%{http_code}" --max-time 25 "https://$HOST/$rel" 2>/dev/null || echo 000)
  if [ "$code" = "200" ] && [ -s "$w.tmp" ]; then
    mv "$w.tmp" "$w"; ok=$((ok+1)); echo "  ✓ $rel"
  else
    rm -f "$w.tmp"; miss=$((miss+1)); echo "  ✗ HTTP $code  $rel"
  fi
done < <(find "$BASE/fg5" -type f -name '*.astc')

echo
if [ "$DRY" = "1" ]; then echo "[dry-run] 只列出,未下載。拿掉 DRY=1 才會抓。"; exit 0; fi
echo "✅ 完成:新增 webp ${ok:-0} 個 / 已存在略過 ${skip:-0} / 抓不到 ${miss:-0}。"
echo "   接著重打包給同事(整包):"
echo "     zip -qr jili_webcapture_win.zip <zip 內原有清單> …   # 或用你原本打包的方式"
echo "   若只想更新 zip 裡的 mirror,對每個新檔:"
echo "     (cd <stage>; zip \"\$ZIP\" jili/game_site_backup/$HOST/<那些新 .webp>)"
