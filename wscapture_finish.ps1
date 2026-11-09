# wscapture_finish.ps1 — 收工:把側錄的 WS 封包解成每局 JSON。Windows 版。
# 以遊戲號分派:124=ws_math_view, 94=ws_rummy_view。對應 Mac 的 wscapture_finish.sh。
# 用法:.\webcapture_finish.ps1 <GID> (統一入口會分派到這;也可直接 .\wscapture_finish.ps1 <GID>)

param([string]$GID = "124")

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$ROOT = $PSScriptRoot; Set-Location -LiteralPath $ROOT
$env:PYTHONUTF8 = "1"

$SRC      = Join-Path $ROOT "games\$GID\webcap_ws.jsonl"
$MATH_DIR = if ($env:MATH_OUT) { $env:MATH_OUT } else { "games\$GID\math" }

if (-not (Test-Path -LiteralPath $SRC)) { Write-Host "✗ 找不到 $SRC — wscapture.ps1 $GID 有跑、server 視窗真的印過 [ws] 嗎?"; exit 1 }
$N=@(Get-Content -LiteralPath $SRC | Where-Object { $_.Trim() }).Count
Write-Host "① 側錄了 $N 個 WS frame → 解成每局(遊戲 $GID)…"

switch ($GID) {
  "124" {
    & python ws_math_view.py --src $SRC --out $MATH_DIR
    $rc = $LASTEXITCODE
    if ($rc -eq 2) { Write-Host "   ⚠ 有局賠付公式對不上 — 先別把樣本發出去,把上面訊息貼給 Claude"; exit 2 }
    if ($rc -ne 0) { Write-Host "✗ 轉換失敗($rc)"; exit 1 }
    Write-Host ""; Write-Host "✅ 完成(都在 $MATH_DIR):EXTRA_SUMMARY.json / <round_id>.json / all.jsonl / INTERFACE.md"
  }
  "94" {
    & python ws_rummy_view.py $GID --src $SRC --out $MATH_DIR
    if ($LASTEXITCODE -ne 0) { Write-Host "✗ 轉換失敗($LASTEXITCODE)"; exit 1 }
    Write-Host ""; Write-Host "✅ 完成(都在 $MATH_DIR):<round_id>.json(發牌/動作/亮牌/分數/金流) + all.jsonl"
  }
  "736" {
    & python ws_fish736_view.py $GID --src $SRC --out $MATH_DIR
    if ($LASTEXITCODE -ne 0) { Write-Host "✗ 轉換失敗($LASTEXITCODE)"; exit 1 }
    Write-Host ""; Write-Host "✅ 完成(都在 $MATH_DIR):shots.jsonl(每發) / summary.json(RTP+倍率/power直方圖) / INTERFACE.md"
  }
  default { Write-Host "✗ 未登記的遊戲號 $GID(支援:124/94/736)"; exit 1 }
}
