# web_own.ps1 — 用「你自己的域名」跑 JILI 696 本地 mock(重播)。Windows 版。
# 對應 web_own.sh,但改 443 + hosts(Windows 上 --host-resolver-rules 多開 Chrome 時會失效)。開頭跳一次 UAC。
# 用法:.\web_own.ps1 [base域名] [漂亮前綴]
#   重播資料用環境變數指定(會轉發給 mock):REPLAY / REPLAY_SPINS / REPLAY_ROUNDS
#   沒設 REPLAY 時,自動用 games\696\webcap\exchanges_ordered.jsonl。
#   收工:.\stop.ps1

param([string]$Base = "myjili.example.com", [string]$Prefix = "")

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$ident = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not (New-Object Security.Principal.WindowsPrincipal($ident)).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
  Write-Host "需要系統管理員(綁 443 + 改 hosts)→ 跳 UAC…"
  $rl = "& '$PSCommandPath'"; if ($Base) { $rl += " -Base '$Base'" }; if ($Prefix) { $rl += " -Prefix '$Prefix'" }
  Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList @("-NoExit","-NoProfile","-ExecutionPolicy","Bypass","-Command",$rl)
  exit
}

$ROOT = $PSScriptRoot; Set-Location -LiteralPath $ROOT
$env:PYTHONUTF8 = "1"
$GID="696"; $PORT=443
$HOSTS_FILE="$env:WINDIR\System32\drivers\etc\hosts"
$ALL_HOSTS=@("uat-wbgame.jlfafafa3.com","uat-wbwebapi.jlfafafa2.com","uat-wbslot-fd.jlfafafa1.com","uat-wbslot-platform.jlfafafa3.com")

$CHROME=$env:CHROME
if (-not $CHROME) { foreach ($p in @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe","${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe","$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe")) { if (Test-Path $p) { $CHROME=$p; break } } }

if (-not (Get-Command python -EA SilentlyContinue)) { Write-Host "✗ 找不到 python"; exit 1 }
if (-not (Test-Path "$ROOT\routex\dl_domlock_solve.py")) { Write-Host "✗ 找不到 dl_domlock_solve.py"; exit 1 }
if (-not $CHROME -or -not (Test-Path $CHROME)) { Write-Host "✗ 找不到 Chrome(可設 CHROME=…)"; exit 1 }

# 重播資料(env 優先;REPLAY 沒設則自動用 webcap 的整場檔)
$REPLAY = if ($env:REPLAY) { $env:REPLAY } else { $c = Join-Path $ROOT "games\$GID\webcap\exchanges_ordered.jsonl"; if (Test-Path $c) { $c } else { "" } }
$REPLAY_SPINS = $env:REPLAY_SPINS
$REPLAY_ROUNDS = $env:REPLAY_ROUNDS

Write-Host "[0] 清舊 mock + 舊 own-profile Chrome"
try { Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'routex[\\/]+server\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } } catch {}
try { Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -like "*jili-own-profile*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } } catch {}
Start-Sleep -Milliseconds 600

# ① 鑄撞中白名單子網域($HOST 是保留變數,用 $GameHost)
$GameHost=$null
if ($Prefix) { Write-Host "① 鑄撞中子網域:$Base(前綴 '$Prefix')…"; $out=& python "$ROOT\routex\dl_domlock_solve.py" pretty $Base $Prefix; $l=$out|Where-Object{$_ -match "✓"}|Select-Object -First 1; if ($l -and $l -match "✓\s+(\S+)"){$GameHost=$matches[1]} }
else { Write-Host "① 鑄撞中子網域:$Base …"; $out=& python "$ROOT\routex\dl_domlock_solve.py" preimage $Base 1; $l=$out|Where-Object{$_ -match "=>"}|Select-Object -First 1; if ($l -and $l -match "=>\s+(\S+)"){$GameHost=$matches[1]} }
if (-not $GameHost) { Write-Host "✗ 鑄子網域失敗:"; $out|ForEach-Object{"   $_"}; exit 1 }
(& python "$ROOT\routex\dl_domlock_solve.py" verify $GameHost) | ForEach-Object { "   $_" }
Write-Host "   → 遊戲域名 = $GameHost"

# ② hosts:子網域 + 4 API host 全導 127.0.0.1(等同 MAP *;只導子網域會 MSG 103)
Write-Host "② 改 hosts:$GameHost + API host → 127.0.0.1 + flush DNS…"
$esc=($ALL_HOSTS|ForEach-Object{[regex]::Escape($_)}) -join "|"
$lines=@(Get-Content -LiteralPath $HOSTS_FILE)
$kept=@($lines | Where-Object { $_ -notmatch '#\s*jili-own\s*$' -and $_ -notmatch "^\s*127\.0\.0\.1\s+.*($esc)" })
$kept += "127.0.0.1 $GameHost  # jili-own"
foreach ($h in $ALL_HOSTS) { $kept += "127.0.0.1 $h  # jili-own" }
[System.IO.File]::WriteAllLines($HOSTS_FILE,$kept); ipconfig /flushdns | Out-Null

$URL="https://$GameHost/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=$GID&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0"

Write-Host "[3] 啟動 mock(443,新視窗)…"
Write-Host "── 重播設定 ──"
if ($REPLAY)        { Write-Host "   REPLAY        = $REPLAY" } else { Write-Host "   ⚠ 沒有 REPLAY(會是通用 mock)" }
if ($REPLAY_SPINS)  { Write-Host "   REPLAY_SPINS  = $REPLAY_SPINS" }
if ($REPLAY_ROUNDS) { Write-Host "   REPLAY_ROUNDS = $REPLAY_ROUNDS" }
$envs=@("`$env:PYTHONUTF8='1'","`$env:PORT='$PORT'","`$env:TLS='1'","`$env:VERBOSE='1'","`$env:INJECT_BUNDLE='1'")
if ($REPLAY)        { $envs += "`$env:REPLAY='$REPLAY'" }
if ($REPLAY_SPINS)  { $envs += "`$env:REPLAY_SPINS='$REPLAY_SPINS'" }
if ($REPLAY_ROUNDS) { $envs += "`$env:REPLAY_ROUNDS='$REPLAY_ROUNDS'" }
$serverCmd="Set-Location -LiteralPath '$ROOT'; " + ($envs -join "; ") + "; python routex\server.py"
Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit","-NoProfile","-ExecutionPolicy","Bypass","-Command",$serverCmd)
Write-Host -NoNewline "   等 mock listen $PORT"
$ok=$false; for ($i=0;$i -lt 30;$i++){ & curl.exe -sk -o NUL --max-time 1 "https://127.0.0.1/" 2>$null; if ($LASTEXITCODE -eq 0){$ok=$true;Write-Host " ✓";break}; Write-Host -NoNewline "."; Start-Sleep -Seconds 1 }
if (-not $ok) { Write-Host " ✗ mock 沒起來"; exit 1 }

# ④ Chrome(靠 hosts 解析,不用 host-resolver-rules)
Get-ChildItem -LiteralPath $env:TEMP -Directory -Filter "jili-own-profile-*" -EA SilentlyContinue | Remove-Item -Recurse -Force -EA SilentlyContinue
$PROFILE_DIR=Join-Path $env:TEMP ("jili-own-profile-"+[DateTimeOffset]::Now.ToUnixTimeSeconds())
Write-Host "[4] 開 Chrome(域名=$GameHost)…"
$args=@(('--user-data-dir="{0}"' -f $PROFILE_DIR),"--ignore-certificate-errors","--disable-quic","--no-first-run","--no-default-browser-check","--disable-features=ChromeWhatsNewUI",('"{0}"' -f $URL)) -join " "
Start-Process -FilePath $CHROME -ArgumentList $args

Write-Host ""; Write-Host "✅ 完成。你的域名 = $GameHost"
Write-Host "   盯 mock 視窗:看到 kind=init[...] 且沒有 jscrambler = 過了、可以玩。★別開 DevTools★"
Write-Host "   收工:.\stop.ps1(會還原 hosts)"
