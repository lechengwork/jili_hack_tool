# webcapture_finish.ps1 — 收工:批次離線解密 → 每局 JSON + 後端原封包 + 機率團隊介面。Windows 版。
# 對應 webcapture_finish.sh。用法:.\webcapture_finish.ps1 [696]
#   GRAB 要和 webcapture.ps1 同一個(預設 %TEMP%\jili_grab.json);MATH_OUT 決定機率介面輸出目錄。

param([string]$GID = "696")

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$ROOT = $PSScriptRoot; Set-Location -LiteralPath $ROOT
$env:PYTHONUTF8 = "1"

$JSONL  = "games/$GID/webcap_exchanges.jsonl"
$ARR    = "games/$GID/webcap/fg5_exchanges.json"
$OUTDIR = "games/$GID/webcap"
$GRV    = "games/$GID/webcap_grv.jsonl"
$GRAB   = if ($env:GRAB) { $env:GRAB } else { Join-Path $env:TEMP "jili_grab.json" }
$MATH_DIR = if ($env:MATH_OUT) { $env:MATH_OUT } else { "games/$GID/math" }

if (-not (Test-Path -LiteralPath $JSONL)) { Write-Host "✗ 找不到 $JSONL — webcapture.ps1 有跑、真的轉過幾局嗎?"; exit 1 }

# key 來源:① 記憶體 shared(GRAB) ② 退路 getRandomValues(GRV)
$keyArgs=$null; $hasKey=$false
if (Test-Path -LiteralPath $GRAB) { try { if (((Get-Content -Raw -LiteralPath $GRAB)|ConvertFrom-Json).key) { $hasKey=$true } } catch {} }
if ($hasKey) { Write-Host "key 來源:記憶體 shared($GRAB) ✓"; $keyArgs=@("--grab",$GRAB) }
elseif (Test-Path -LiteralPath $GRV) { $n=@(Get-Content $GRV|Where-Object{$_.Trim()}).Count; Write-Host "key 來源:getRandomValues($GRV,$n 筆)✓"; $keyArgs=@("--grv","../$GRV") }
else { Write-Host "✗ 沒有可用 key(server 無『+KEY』且 $GRV 不存在)。把 server 視窗的 ★★★ [shim-report] 貼給 Claude。"; exit 1 }

$N=@(Get-Content -LiteralPath $JSONL|Where-Object{$_.Trim()}).Count
Write-Host "① 側錄了 $N 筆 exchanges → 轉成 JSON 陣列…"
New-Item -ItemType Directory -Force -Path $OUTDIR | Out-Null
$pyCode = @'
import json,sys
src,dst=sys.argv[1],sys.argv[2]
rows=[json.loads(l) for l in open(src,encoding="utf-8") if l.strip()]
rows.sort(key=lambda r: r.get("seq") or 0)
json.dump(rows, open(dst,"w",encoding="utf-8"))
print("   ->",dst,len(rows),"筆")
'@
$pyCode | & python - $JSONL $ARR
if ($LASTEXITCODE -ne 0) { Write-Host "✗ 轉 JSON 陣列失敗"; exit 1 }

Write-Host "② 批次解密…"
Push-Location routex
try { & python decrypt_capture.py --exchanges "../$ARR" @keyArgs --out "../$OUTDIR/responses.jsonl"; $rc=$LASTEXITCODE } finally { Pop-Location }
if ($rc -ne 0) { Write-Host "✗ 解密失敗($rc)"; exit 1 }

Write-Host ""; Write-Host "③ 套語意標籤 → 可讀 JSON…"
& python webcap_pretty.py $GID
if ($LASTEXITCODE -ne 0) { Write-Host "✗ 語意化失敗"; exit 1 }

Write-Host ""; Write-Host "④ 匯出後端【原封不動】封包(給機率:未改名/未丟欄位/未自算)…"
& python webcap_backend_raw.py $GID --grab $GRAB
if ($LASTEXITCODE -ne 0) { Write-Host "✗ 後端原封包匯出失敗"; exit 1 }

Write-Host ""; Write-Host "⑤ 轉成【機率團隊介面】(math_696.proto 形狀)…"
Write-Host "   輸出目錄:$MATH_DIR"
& python webcap_math_view.py $GID --exch-raw "$OUTDIR/exchanges_ordered.jsonl" --out $MATH_DIR
if ($LASTEXITCODE -ne 0) { Write-Host "✗ 機率介面轉換失敗"; exit 1 }
& python math_adapter.py --selftest
if ($LASTEXITCODE -ne 0) { Write-Host "   ⚠ round-trip 自我驗證沒過 — 別把樣本發出去,先找 Claude" }

Write-Host ""
Write-Host "✅ 完成。主要輸出:"
Write-Host "   • $MATH_DIR\*.json                     ← ★給機率:輸入 spinReq / 輸出 data"
Write-Host "   • games\$GID\math\INTERFACE.md         ← ★給機率:欄位表(算 RTP 必看)"
Write-Host "   • $OUTDIR\backend_raw\spins\*.json     ← (工程)後端原封包(payload_hex=重播單位)"
Write-Host "   • $OUTDIR\pretty.jsonl                 ← 可讀格式(每局一行)"
Write-Host "   • $OUTDIR\exchanges_ordered.jsonl      ← 原始 decoded"
Write-Host "   • $OUTDIR\responses.jsonl              ← 每 type 一筆樣本"
