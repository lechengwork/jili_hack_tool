#!/usr/bin/env bash
# capture_finish.sh — B 的收尾:撈 AES key → 你關 CfT → 抽 netlog + 解密 → mock 吃新盤。
# 流程:
#   1) bash go.sh 696 --netlog     # 產token/VPN/開遊戲
#   2) 進遊戲、多轉幾把(30~50),★視窗先別關★
#   3) ./capture_finish.sh          # ← 這支:趁開著撈 key、關窗、抽取、解密
#   4) ./stop.sh && ./run.sh        # mock 輪播你這次抓到的全部 spin 盤
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
GID="${1:-696}"

echo "① 撈 AES key(★遊戲需仍開著★,會問 sudo 密碼)…"
sudo rm -f /tmp/jili_grab.json          # 清掉舊 key,確保拿到的是「這次」session 的
sudo .venv/bin/python grabshared.py || true      # 首選:直接讀 WASM @1108480(可靠)
if [ ! -f /tmp/jili_grab.json ]; then
  echo "  grabshared 沒中 → 改試 grabkey(heap 掃描)…"
  sudo .venv/bin/python grabkey.py || true
fi
if [ ! -f /tmp/jili_grab.json ]; then
  echo "✗ grabkey 沒撈到這次 session 的 key —— ★遊戲先別關★,可重試:"
  echo "    看上面每個 pid 的 f4_hits;有 hits 就加大半徑:sudo RADIUS=65536 ./.venv/bin/python grabkey.py"
  echo "    出現『[OK] 已存 /tmp/jili_grab.json』後,再重跑 ./capture_finish.sh"
  exit 1
fi
echo "  ✓ 撈到 key (f4=$(.venv/bin/python -c "import json;print(json.load(open('/tmp/jili_grab.json')).get('f4','?')[:16])" 2>/dev/null)…)"

# 備份現有可用資料(decrypt 失敗時 ①的守衛也會保住,這是雙保險)
cp -f "games/$GID/responses.jsonl"        /tmp/responses.bak.jsonl         2>/dev/null || true
cp -f "games/$GID/exchanges_ordered.jsonl" /tmp/exchanges_ordered.bak.jsonl 2>/dev/null || true

read -r -p "② 現在【關掉 CfT 視窗】讓 netlog 寫完整,關好後按 Enter…"
sleep 2

echo "③ 從 netlog 抽 /fg5/req exchanges…"
.venv/bin/python extract_fg5.py "$GID" --netlog "games/$GID/netlog_req.json"

echo "④ 解密整段 → responses.jsonl + exchanges_ordered.jsonl…"
( cd routex && ../.venv/bin/python decrypt_capture.py \
    --exchanges "../games/$GID/fg5_exchanges.json" --grab /tmp/jili_grab.json \
    --out "../games/$GID/responses.jsonl" )

echo
echo "✅ 完成。接著:  ./stop.sh && ./run.sh   → mock 會輪播這次抓到的全部 spin 盤。"
