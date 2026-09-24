# webcapture.ps1 — 純網頁擷取【真伺服器】封包(免 Frida、免 netlog)。Windows 版。
# 對應 webcapture.sh。① VPN關→產token ② split hosts(只 doc 指本機) ③ 開 server(capture)
#                    ④ VPN開→BR ⑤ 開 Chrome 連真 token 的 game_url。
# VPN 自動切用官方 WireGuard(wireguard.exe /installtunnelservice);抓不到就退回手動。
# 開頭跳一次 UAC(綁 443 + 改 hosts)。用法:.\webcapture.ps1 <遊戲號>  例:696(route-X) / 124(明文WS)
#   可用環境變數(會轉發給 server):MATH_OUT / LIVE_RAW / SPIN_OUT / SPIN_RAW_OUT / BR_SPIN_OUT

param([string]$GID = "696")

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# ── 分派:124 等【明文 WebSocket】遊戲走 wscapture.ps1(與 696 route-X 是兩套不同協定) ──
#   統一入口:機率團隊永遠 .\webcapture.ps1 <遊戲號>,號碼決定走哪套,不用記兩個腳本名。
if (@("124") -contains $GID) { & "$PSScriptRoot\wscapture.ps1" $GID; exit $LASTEXITCODE }

# ── 自動提權 ──
$ident = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not (New-Object Security.Principal.WindowsPrincipal($ident)).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
  Write-Host "需要系統管理員(綁 443 + 改 hosts)→ 跳 UAC…"
  Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList @(
    "-NoExit","-NoProfile","-ExecutionPolicy","Bypass","-File","`"$PSCommandPath`"",$GID)
  exit
}

$ROOT = $PSScriptRoot; Set-Location -LiteralPath $ROOT
$env:PYTHONUTF8 = "1"
$DOC_HOST  = "uat-wbgame.jlfafafa3.com"
$ALL_HOSTS = @("uat-wbgame.jlfafafa3.com","uat-wbwebapi.jlfafafa2.com","uat-wbslot-fd.jlfafafa1.com","uat-wbslot-platform.jlfafafa3.com")
$GRAB        = if ($env:GRAB) { $env:GRAB } else { Join-Path $env:TEMP "jili_grab.json" }
$LOGIN_OUT   = Join-Path $env:TEMP "webcap_login.json"
$LOGIN_ERR   = Join-Path $env:TEMP "webcap_login_err.txt"
$PROFILE_DIR = Join-Path $env:TEMP ("jili-webcap-profile-" + [DateTimeOffset]::Now.ToUnixTimeSeconds())
$HOSTS_FILE  = "$env:WINDIR\System32\drivers\etc\hosts"

$CHROME = $env:CHROME
if (-not $CHROME) { foreach ($p in @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe","${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe","$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe")) { if (Test-Path -LiteralPath $p) { $CHROME = $p; break } } }

# ── VPN(WireGuard)──
$WG_EXE = @("$env:ProgramFiles\WireGuard\wireguard.exe","${env:ProgramFiles(x86)}\WireGuard\wireguard.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
function Get-WgConf {
  if ($env:WG_CONF -and (Test-Path -LiteralPath $env:WG_CONF)) { return (Resolve-Path -LiteralPath $env:WG_CONF).Path }
  foreach ($dir in @($ROOT,(Join-Path $env:USERPROFILE "Downloads"))) {
    $c = @(Get-ChildItem -LiteralPath $dir -Filter *.conf -ErrorAction SilentlyContinue)
    if ($c.Count -eq 1) { return $c[0].FullName }
    if ($c.Count -gt 1) { $br = @($c | Where-Object { $_.Name -match "br|brazil|sao" }); if ($br.Count -ge 1) { return $br[0].FullName } }
  }
  return $null
}
function Vpn-Down { foreach ($s in @(Get-Service -EA SilentlyContinue | Where-Object { $_.Name -like 'WireGuardTunnel$*' })) { try { & $WG_EXE /uninstalltunnelservice ($s.Name -replace '^WireGuardTunnel\$','') *> $null } catch {} } }
function Vpn-Up { param([string]$Conf); $n=[IO.Path]::GetFileNameWithoutExtension($Conf); try { & $WG_EXE /uninstalltunnelservice $n *> $null } catch {}; Start-Sleep -Milliseconds 500; $o=(& $WG_EXE /installtunnelservice "$Conf" 2>&1 | Out-String); if ($LASTEXITCODE -ne 0) { throw "installtunnelservice 失敗: $($o.Trim())" } }
function Get-Country { try { $j = & curl.exe -s --max-time 6 https://ipinfo.io/json 2>$null; if ($j) { return [string](($j -join "`n" | ConvertFrom-Json).country) } } catch {}; return "" }
function Switch-Country {
  param([string]$Want,[scriptblock]$AutoAction,[string]$ManualHint)
  if ($script:autoVpn -and $AutoAction) { Write-Host "    自動切 VPN(WireGuard)…"; try { & $AutoAction } catch { Write-Host "    (自動切失敗:$($_.Exception.Message) → 改手動)"; $script:autoVpn=$false } }
  if (-not $script:autoVpn) { Write-Host "    $ManualHint"; Read-Host "    切好後按 Enter" | Out-Null }
  while ($true) {
    Write-Host -NoNewline "    偵測出口國(要 $Want)"; $c=""
    for ($i=0;$i -lt 25;$i++){ $c=Get-Country; if ($c -eq $Want){ Write-Host " → $c ✓"; return }; Write-Host -NoNewline "."; Start-Sleep -Seconds 2 }
    Write-Host " → 現在=$c ✗"; Read-Host "    還不是 $Want。確認 VPN 後按 Enter 重試(或 Ctrl+C 中止)" | Out-Null
  }
}

Write-Host "── JILI $GID 純網頁擷取(真伺服器,免 Frida)── Windows"
if (-not (Get-Command python -EA SilentlyContinue)) { Write-Host "✗ 找不到 python"; exit 1 }
if (-not (Test-Path -LiteralPath "$ROOT\routex\server.py")) { Write-Host "✗ 找不到 routex\server.py"; exit 1 }
if (-not (Test-Path -LiteralPath "$ROOT\routex\capture_shim.js")) { Write-Host "✗ 找不到 routex\capture_shim.js"; exit 1 }
if (-not $CHROME -or -not (Test-Path -LiteralPath $CHROME)) { Write-Host "✗ 找不到 Google Chrome(可設 CHROME=…)"; exit 1 }

$WG_CONF = Get-WgConf; $autoVpn = [bool]($WG_EXE -and $WG_CONF)
Write-Host $(if ($autoVpn) { "VPN 模式:自動(WireGuard)  conf = $WG_CONF" } elseif (-not $WG_EXE) { "VPN 模式:手動(沒裝 WireGuard)" } else { "VPN 模式:手動(找不到 .conf;可設 `$env:WG_CONF)" })

Write-Host "[0] 清乾淨舊擷取 Chrome + 舊 server"
try { Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -like '*jili-webcap-profile*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } } catch {}
try { Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'routex[\\/]+server\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } } catch {}

Write-Host "[1] VPN 關 → 等 TW(產 token 需要)…"
Switch-Country -Want "TW" -AutoAction { Vpn-Down } -ManualHint "請【關閉】VPN(Surfshark 斷線)。"

Write-Host "[2] 產真 token(gameid=$GID)…"
& python jili_login.py $GID --json 1>$LOGIN_OUT 2>$LOGIN_ERR
$URL=""; try { $d=(Get-Content -Raw -LiteralPath $LOGIN_OUT)|ConvertFrom-Json; if ($d -is [array]){$d=$d[0]}; $URL=[string]$d.game_url } catch {}
if (-not $URL) { Write-Host "!!! 產 token 失敗:"; if (Test-Path $LOGIN_ERR){ Get-Content $LOGIN_ERR }; exit 1 }
$SSO=""; if ($URL -match '[?&]ssoKey=([^&]+)') { $SSO=[Uri]::UnescapeDataString($matches[1]) }
Write-Host "    ssoKey=$SSO ✓"

Write-Host "[3] split hosts:只有 $DOC_HOST → 127.0.0.1(api host 走真站)+ flush DNS…"
$esc=($ALL_HOSTS|ForEach-Object{[regex]::Escape($_)}) -join "|"
$lines=@(Get-Content -LiteralPath $HOSTS_FILE)
$kept=@($lines | Where-Object { $_ -notmatch "^\s*127\.0\.0\.1\s+.*($esc)" })
$kept += "127.0.0.1 $DOC_HOST"
[System.IO.File]::WriteAllLines($HOSTS_FILE,$kept); ipconfig /flushdns | Out-Null
Write-Host "    ✓ hosts 已設(只 $DOC_HOST → 127.0.0.1)"

Write-Host "[4] 開 server(capture 模式,新視窗)…"
$envs=@("`$env:PYTHONUTF8='1'","`$env:GRAB='$GRAB'","`$env:PORT='443'","`$env:TLS='1'","`$env:VERBOSE='1'","`$env:INJECT_BUNDLE='1'","`$env:CAPTURE='1'","`$env:LIVE_DECODE='1'","`$env:ASSET_FALLBACK='1'")
foreach ($v in @("MATH_OUT","LIVE_RAW","SPIN_OUT","SPIN_RAW_OUT","BR_SPIN_OUT")) { $val=[Environment]::GetEnvironmentVariable($v); if ($val) { $envs += "`$env:$v='$val'" } }
$serverCmd = "Set-Location -LiteralPath '$ROOT'; " + ($envs -join "; ") + "; python routex\server.py"
Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit","-NoProfile","-ExecutionPolicy","Bypass","-Command",$serverCmd)
Write-Host "    key 檔(GRAB)= $GRAB  ← webcapture_finish 要用同一個"
Write-Host -NoNewline "    等 server listen 443"
$ok=$false; for ($i=0;$i -lt 30;$i++){ & curl.exe -sk -o NUL --max-time 2 https://127.0.0.1/ 2>$null; if ($LASTEXITCODE -eq 0){ $ok=$true; Write-Host " ✓"; break }; Write-Host -NoNewline "."; Start-Sleep -Seconds 1 }
if (-not $ok) { Write-Host " ✗ server 沒起來(443 被占用 / python 套件沒裝)"; exit 1 }

Write-Host "[5] VPN 開 → 等 BR(真 /fg5/req 要巴西出口)…"
Switch-Country -Want "BR" -AutoAction { Vpn-Up $WG_CONF } -ManualHint "請【開啟】VPN(Surfshark 連巴西節點)。"

Write-Host "[6] 開普通 Chrome 連真 token 的 game_url(拋棄式 profile)…"
$args=@(('--user-data-dir="{0}"' -f $PROFILE_DIR),"--ignore-certificate-errors","--disable-quic","--no-first-run","--no-default-browser-check","--disable-features=ChromeWhatsNewUI",('"{0}"' -f $URL)) -join " "
Start-Process -FilePath $CHROME -ArgumentList $args

Write-Host ""
Write-Host "✅ 開始擷取:進遊戲→開 autoplay 轉到你要的局數。★別開 DevTools★"
Write-Host "   盯 server 視窗即時解碼;收工匯出:.\webcapture_finish.ps1 $GID"
Write-Host "   中止:.\stop.ps1(停 server + 關 Chrome + 還原 hosts)"
