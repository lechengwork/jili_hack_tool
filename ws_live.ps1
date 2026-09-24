# ws_live.ps1 — JILI 124 即時逐局解碼視窗(邊玩邊看 + 每局存一筆)。
# 抓封包時另開一個 PowerShell 跑這支,右邊就會逐局跳出:骰子/和/下注/中獎/餘額。
# 每局也會存 games\124\ws_rounds\<局號>.json(含 decoded + 原始 raw)。
#   .\ws_live.ps1            # 跟隨(邊玩邊看)
#   .\ws_live.ps1 --once     # 只把現有側錄檔解一次

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONUTF8 = "1"
python ws_live.py @args
