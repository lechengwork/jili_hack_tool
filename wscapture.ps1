# wscapture.ps1 — JILI 124 (7up7down) 實時擷取【真伺服器】WebSocket 封包。Windows 版。
#
# 124 是【明文 protobuf over WebSocket】(不像 696 要破 crypto):
#   ① VPN關→產token ② split hosts(只 doc host uat-wbgame 指本機;api/WS 走真站)
#   ③ 開 ws_capture_server(服務 static + 注入 WS-hook shim) ④ VPN開→BR ⑤ 開 Chrome 連真 token。
# 遊戲的 WebSocket 直連真站(uat-fish),頁面內的 shim 側錄每個明文 frame → 本機 server。
# 用 jili host 就過 Jscrambler domain-lock,不用任何 bypass(同 696)。
# VPN 自動切用官方 WireGuard;開頭跳一次 UAC(綁 443 + 改 hosts)。用法:.\wscapture.ps1

param([string]$GID = "124")

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

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
# 這些只用來清除 hosts 裡的舊殘留行(不會全部導本機;只有 DOC_HOST 導本機,api/WS 走真站)
$ALL_HOSTS = @("uat-wbgame.jlfafafa3.com","uat-wbwebapi.jlfafafa2.com","uat-fish.jlfafafa1.com","uat-wbslot-platform.jlfafafa3.com")
$OUT         = Join-Path $ROOT "games\124\webcap_ws.jsonl"
$LOGIN_OUT   = Join-Path $env:TEMP "wscap_login.json"
$LOGIN_ERR   = Join-Path $env:TEMP "wscap_login_err.txt"
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

Write-Host "── JILI $GID 實時擷取(明文 WebSocket,免 crypto)── Windows"
if (-not (Get-Command python -EA SilentlyContinue)) { Write-Host "✗ 找不到 python"; exit 1 }
if (-not (Test-Path -LiteralPath "$ROOT\ws_capture_server.py")) { Write-Host "✗ 找不到 ws_capture_server.py"; exit 1 }
if (-not (Test-Path -LiteralPath "$ROOT\ws_capture_shim.js")) { Write-Host "✗ 找不到 ws_capture_shim.js"; exit 1 }
if (-not (Test-Path -LiteralPath "$ROOT\dist124\static\sudm\index.html")) { Write-Host "✗ 找不到 dist124\static(靜態 mirror)"; exit 1 }
if (-not $CHROME -or -not (Test-Path -LiteralPath $CHROME)) { Write-Host "✗ 找不到 Google Chrome(可設 CHROME=…)"; exit 1 }

$WG_CONF = Get-WgConf; $autoVpn = [bool]($WG_EXE -and $WG_CONF)
Write-Host $(if ($autoVpn) { "VPN 模式:自動(WireGuard)  conf = $WG_CONF" } elseif (-not $WG_EXE) { "VPN 模式:手動(沒裝 WireGuard)" } else { "VPN 模式:手動(找不到 .conf;可設 `$env:WG_CONF)" })

Write-Host "[0] 清乾淨舊擷取 Chrome + 舊 server"
try { Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -like '*jili-webcap-profile*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } } catch {}
try { Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'ws_capture_server\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } } catch {}

Write-Host "[1] VPN 關 → 等 TW(產 token 需要)…"
Switch-Country -Want "TW" -AutoAction { Vpn-Down } -ManualHint "請【關閉】VPN(Surfshark 斷線)。"

Write-Host "[2] 產真 token(gameid=$GID,帳號 tryplayer002usd)…"
& python jili_login.py $GID --json 1>$LOGIN_OUT 2>$LOGIN_ERR
$URL=""; try { $d=(Get-Content -Raw -LiteralPath $LOGIN_OUT)|ConvertFrom-Json; if ($d -is [array]){$d=$d[0]}; $URL=[string]$d.game_url } catch {}
if (-not $URL) { Write-Host "!!! 產 token 失敗:"; if (Test-Path $LOGIN_ERR){ Get-Content $LOGIN_ERR }; exit 1 }
$SSO=""; if ($URL -match '[?&]ssoKey=([^&]+)') { $SSO=[Uri]::UnescapeDataString($matches[1]) }
Write-Host "    ssoKey=$SSO ✓"

Write-Host "[3] split hosts:只有 $DOC_HOST → 127.0.0.1(sso-login/WS 走真站)+ flush DNS…"
$esc=($ALL_HOSTS|ForEach-Object{[regex]::Escape($_)}) -join "|"
$lines=@(Get-Content -LiteralPath $HOSTS_FILE)
$kept=@($lines | Where-Object { $_ -notmatch "^\s*127\.0\.0\.1\s+.*($esc)" })
$kept += "127.0.0.1 $DOC_HOST"
[System.IO.File]::WriteAllLines($HOSTS_FILE,$kept); ipconfig /flushdns | Out-Null
Write-Host "    ✓ hosts 已設(只 $DOC_HOST → 127.0.0.1)"

Write-Host "[4] 開 ws_capture_server(443,TLS,注入 shim,新視窗)…"
if (Test-Path -LiteralPath $OUT) { Remove-Item -LiteralPath $OUT -Force }   # 每次擷取用乾淨的側錄檔
$envs=@("`$env:PYTHONUTF8='1'","`$env:PORT='443'","`$env:TLS='1'","`$env:VERBOSE='1'","`$env:OUT='$OUT'")
$serverCmd = "Set-Location -LiteralPath '$ROOT'; " + ($envs -join "; ") + "; python ws_capture_server.py"
Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit","-NoProfile","-ExecutionPolicy","Bypass","-Command",$serverCmd)
Write-Host "    側錄檔 = $OUT  ← wscapture_finish 會讀它"
Write-Host -NoNewline "    等 server listen 443"
$ok=$false; for ($i=0;$i -lt 30;$i++){ & curl.exe -sk -o NUL --max-time 2 https://127.0.0.1/sudm/index.html 2>$null; if ($LASTEXITCODE -eq 0){ $ok=$true; Write-Host " ✓"; break }; Write-Host -NoNewline "."; Start-Sleep -Seconds 1 }
if (-not $ok) { Write-Host " ✗ server 沒起來(443 被占用 / 憑證問題)"; exit 1 }

Write-Host "[5] VPN 開 → 等 BR(真 sso-login/WS 要巴西出口)…"
Switch-Country -Want "BR" -AutoAction { Vpn-Up $WG_CONF } -ManualHint "請【開啟】VPN(Surfshark 連巴西節點)。"

Write-Host "[6] 開普通 Chrome 連真 token 的 game_url(拋棄式 profile)…"
$args=@(('--user-data-dir="{0}"' -f $PROFILE_DIR),"--ignore-certificate-errors","--disable-quic","--no-first-run","--no-default-browser-check","--disable-features=ChromeWhatsNewUI",('"{0}"' -f $URL)) -join " "
Start-Process -FilePath $CHROME -ArgumentList $args

Write-Host ""
Write-Host "✅ 開始擷取:進遊戲→下注/開骰(或開 autoplay)轉到你要的局數。★別開 DevTools★"
Write-Host "   盯 server 視窗:每局會印 [ws] SEND/RECV;沒看到 [ws] 進來就是 WS 沒連上(見疑難排解)。"
Write-Host "   收工匯出:.\wscapture_finish.ps1"
Write-Host "   中止:.\stop.ps1(停 server + 關 Chrome + 還原 hosts + 斷 VPN)"
