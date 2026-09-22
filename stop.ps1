# stop.ps1 — 停止 JILI mock/capture:關 server + 關拋棄式 Chrome + 還原 hosts。Windows 版。
# 對應 stop.sh。server 是提權開的,故自動跳一次 UAC。用法:.\stop.ps1

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$ident = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not (New-Object Security.Principal.WindowsPrincipal($ident)).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
  Write-Host "需要系統管理員(停 server + 還原 hosts)→ 跳 UAC…"
  Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-NoExit","-File","`"$PSCommandPath`"")
  exit
}

Write-Host "停止 JILI mock/capture…"

# 1) 停 server.py
$srv=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "routex[\\/]+server\.py" })
if ($srv.Count -gt 0) { $srv | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }; Write-Host "  ✓ server 已停($($srv.Count) 個)" } else { Write-Host "  · server 未在跑" }

# 2) 關拋棄式 profile 的 Chrome(擷取/純網頁/自有域名/回放;不誤殺日常 Chrome)
$ch=@(Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object {
  $_.CommandLine -like "*jili-webcap-profile*" -or $_.CommandLine -like "*jili-web-profile*" -or
  $_.CommandLine -like "*jili-own-profile*"    -or $_.CommandLine -like "*jili-replay-profile*" })
if ($ch.Count -gt 0) { $ch | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }; Write-Host "  ✓ 擷取/回放 Chrome 已關($($ch.Count) 個)" } else { Write-Host "  · 擷取/回放 Chrome 未在跑" }

# 3) 還原 hosts:移除我們加的「127.0.0.1 …jlfafafa…」行(不動你其他設定)+ flush DNS
$hosts="$env:WINDIR\System32\drivers\etc\hosts"
$lines=@(Get-Content -LiteralPath $hosts)
$kept=@($lines | Where-Object { $_ -notmatch '^\s*127\.0\.0\.1\s+.*jlfafafa' })
if ($kept.Count -ne $lines.Count) {
  [System.IO.File]::WriteAllLines($hosts,$kept); ipconfig /flushdns | Out-Null
  Write-Host "  ✓ hosts 已還原(移除 $($lines.Count - $kept.Count) 行)+ flush DNS"
} else { Write-Host "  · hosts 乾淨,不用還原" }

# 4) 斷 WireGuard(擷取用自動 VPN 開的)
$wgExe=@("$env:ProgramFiles\WireGuard\wireguard.exe","${env:ProgramFiles(x86)}\WireGuard\wireguard.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
$wg=@(Get-Service -EA SilentlyContinue | Where-Object { $_.Name -like "WireGuardTunnel$*" })
if ($wgExe -and $wg.Count -gt 0) { $wg | ForEach-Object { try { & $wgExe /uninstalltunnelservice ($_.Name -replace '^WireGuardTunnel\$','') *> $null } catch {} }; Write-Host "  ✓ WireGuard 已斷($($wg.Count) 條)" } else { Write-Host "  · WireGuard 未在跑" }

Write-Host "完成。"
