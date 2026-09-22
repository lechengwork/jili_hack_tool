#!/usr/bin/env bash
# dl_fpt_run.sh — 跑 FPT-spoof forge 測試:合法域完整載入 + 掛 dl_fpt_spoof_shim.js。
# 先 ./routex/dl_fpt_forge.py patch 產生 bundle 改動 + shim,再跑本腳本。
# 判讀:載到轉盤 + 【無】GameTampering = ★FPT-spoof 成功、integrity 被繞★。
# 看 mock 視窗 ★★★ [shim-report] FPTSPOOF installed ... 確認 shim 有掛上。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
export SHIM="dl_fpt_spoof_shim.js"
exec ./dl_murmur_trace.sh   # 該腳本:合法域 uat-wbgame.jlfafafa3.com 完整載入 + EXTRA_SHIM=$SHIM
