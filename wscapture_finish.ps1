# wscapture_finish.ps1 — 收工:把側錄的 124 WebSocket 封包攤成【機率團隊介面】。Windows 版。
# 124 是明文 protobuf,不用解密。用法:.\webcapture_finish.ps1 124 (統一入口會分派到這;也可直接 .\wscapture_finish.ps1)

param([string]$GID = "124")   # 只為相容統一入口的分派;124 目前是唯一 WS 遊戲

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$ROOT = $PSScriptRoot; Set-Location -LiteralPath $ROOT
$env:PYTHONUTF8 = "1"

$SRC     = Join-Path $ROOT "games\124\webcap_ws.jsonl"
$MATH_DIR = if ($env:MATH_OUT) { $env:MATH_OUT } else { "games\124\math" }

if (-not (Test-Path -LiteralPath $SRC)) { Write-Host "✗ 找不到 $SRC — wscapture.ps1 有跑、server 視窗真的印過 [ws] 嗎?"; exit 1 }
$N=@(Get-Content -LiteralPath $SRC | Where-Object { $_.Trim() }).Count
Write-Host "① 側錄了 $N 個 WS frame → 解成每局機率介面…"

& python ws_math_view.py --src $SRC --out $MATH_DIR
$rc = $LASTEXITCODE
if ($rc -eq 2) { Write-Host "   ⚠ 有局賠付公式對不上 — 先別把樣本發出去,把上面訊息貼給 Claude"; exit 2 }
if ($rc -ne 0) { Write-Host "✗ 轉換失敗($rc)"; exit 1 }

Write-Host ""
Write-Host "✅ 完成。主要輸出(都在 $MATH_DIR):"
Write-Host "   • EXTRA_SUMMARY.json   ← ★機率主看:extra 值域 + 每格各值次數 + 每格 E[extra]"
Write-Host "   • <round_id>.json      ← 每局明細(畫面順序、含本金賠率、每格 extra/下注/賠付)"
Write-Host "   • all.jsonl            ← 每局一行(彙整)"
Write-Host "   • INTERFACE.md         ← 欄位表(算 RTP 必看;完整規格見 games\124\EXTRA_MULT.md)"
