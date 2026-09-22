#!/usr/bin/env bash
# stop.sh — 停止 JILI mock harness (mock + patchwasm + CfT 遊戲視窗)。
# 'chrome-mac-arm64' 只中 Chrome for Testing,不會誤殺你正常的 Google Chrome。
echo "停止 mock + patchwasm + CfT…"
sudo pkill -f 'routex/server.py' 2>/dev/null && echo "  ✓ mock 已停"      || echo "  · mock 未在跑"
sudo pkill -9 -f 'patchwasm.py'  2>/dev/null && echo "  ✓ patchwasm 已停" || echo "  · patchwasm 未在跑"
pkill -f 'chrome-mac-arm64'      2>/dev/null && echo "  ✓ CfT 遊戲已關"   || echo "  · CfT 未在跑"
# 純網頁版(web.sh)開的 Chrome:用拋棄式 profile 路徑精準比對,不會誤殺你日常的 Google Chrome。
pkill -f 'jili-web-profile'      2>/dev/null && echo "  ✓ 純網頁 Chrome 已關" || echo "  · 純網頁 Chrome 未在跑"
pkill -f 'jili-own-profile'      2>/dev/null && echo "  ✓ 自有域名 Chrome 已關" || echo "  · 自有域名 Chrome 未在跑"

# ── 還原 /etc/hosts ──────────────────────────────────────────────────────────
# webcapture.sh 會把 doc host 指到 127.0.0.1(擷取時 split hosts 用)。
# 停掉 harness 後那條若留著,一般瀏覽器開該域名會連不上 → 收工一併還原。
# 只刪「127.0.0.1 + 我們自己的網域」那幾行,不動你其他的 hosts 設定。
if grep -qE '^[[:space:]]*127\.0\.0\.1[[:space:]].*jlfafafa' /etc/hosts 2>/dev/null; then
  echo "還原 /etc/hosts…"
  grep -E '^[[:space:]]*127\.0\.0\.1[[:space:]].*jlfafafa' /etc/hosts | sed 's/^/  - /'
  sudo sed -i '' -E '/^[[:space:]]*127\.0\.0\.1[[:space:]].*jlfafafa/d' /etc/hosts \
    && echo "  ✓ 已移除" || echo "  ✗ 移除失敗(權限?)"
  { sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder; } 2>/dev/null \
    && echo "  ✓ DNS 快取已刷新"
else
  echo "· /etc/hosts 乾淨,不用還原"
fi
