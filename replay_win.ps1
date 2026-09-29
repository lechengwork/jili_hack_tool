# replay_win.ps1 — Windows 版:繞過 696 舊 build 的「date-lock + MSG 8 校時」雙鎖後重播。
#
# 背景(2026-09-29):9/2 的 build 約一個月後開始鎖:
#   (1) Jscrambler date-lock:過期就在 handshake 前停(送 dateLock / j-002-00003)。
#   (2) 遊戲內 MSG 8「发现设备时间异常」:比對【裝置時間 vs 伺服器回應時戳】,差太多就跳。
# 兩者都是【時間觸發】。用純 JS 改時間會被 self-defending 抓(GameDebugging)。
# ★唯一穩解 = 讓「真實系統時鐘」整體撥回擷取日(2026-09-11)★:
#   系統時鐘一撥,本機的 python mock server 和 Chrome 就【同時】讀到 09-11、天生同步 →
#   date-lock 看到過去日期(過)、self-defending 因為是真 OS 時鐘(測不到)、MSG 8 因 server 時戳
#   也 = 09-11 跟裝置一致(過)。這支自動:設回時鐘 → 跑既有 replay → 收工自動還原時鐘。
#
#   .\replay_win.ps1                        # 播全部(spins_raw,循環)
#   .\replay_win.ps1 24126-883680-00240696  # 只播指定局(可逗號多局)
#   .\replay_win.ps1 -Source math           # 改讀 games\696\math\(編回 raw 再播)
#
# 收工:在這個視窗按 Ctrl+C → 會自動【還原系統時鐘】+ 提示跑 .\stop.ps1 還原 hosts。★別開 DevTools★。
# ⚠ 設回系統時鐘會影響【整台機器】的時間(其他 app / TLS / 排程),僅在重播期間;結束即還原。
#   建議用一台可犧牲時間的機器 / 重播專用環境。

param([string]$Rounds = "", [ValidateSet("spins","math")][string]$Source = "spins")
$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# ── 需要系統管理員(改系統時鐘 + 綁 443 + 改 hosts)→ 自我提權(UAC 一次) ──
$ident = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not (New-Object Security.Principal.WindowsPrincipal($ident)).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
  Write-Host "需要系統管理員(改系統時鐘/443/hosts)→ 跳 UAC…"
  $rl = "& '$PSCommandPath'"; if ($Rounds) { $rl += " -Rounds '$Rounds'" }; if ($Source) { $rl += " -Source '$Source'" }
  Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList @("-NoExit","-NoProfile","-ExecutionPolicy","Bypass","-Command",$rl)
  exit
}

$ROOT = $PSScriptRoot; Set-Location -LiteralPath $ROOT
$env:PYTHONUTF8 = "1"
$PORT = 443
$GHOST = "uat-wbgame.jlfafafa3.com"
$ALL_HOSTS = @("uat-wbgame.jlfafafa3.com","uat-wbwebapi.jlfafafa2.com","uat-wbslot-fd.jlfafafa1.com","uat-wbslot-platform.jlfafafa3.com")

# 撥到哪一天:擷取日 2026-09-11(在 date-lock 窗內)。要調就設環境變數 FAKE_DATE。
$TARGET = if ($env:FAKE_DATE) { [DateTime]::Parse($env:FAKE_DATE) } else { [DateTime]::Parse("2026-09-11 15:00:00") }

$CHROME = $env:CHROME
if (-not $CHROME) { foreach ($p in @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe","${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe","$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe")) { if (Test-Path $p) { $CHROME=$p; break } } }
$REPLAY = if ($env:REPLAY) { $env:REPLAY } else { Join-Path $ROOT "games\696\webcap\exchanges_ordered.jsonl" }
$REPLAY_SPINS = if ($env:REPLAY_SPINS) { $env:REPLAY_SPINS } else { Join-Path $ROOT "games\696\webcap\spins_raw" }
$ROUNDS = if ($Rounds) { $Rounds } elseif ($env:REPLAY_ROUNDS) { $env:REPLAY_ROUNDS } else { "" }

if (-not (Get-Command python -EA SilentlyContinue)) { Write-Host "✗ 找不到 python"; exit 1 }
if (-not $CHROME -or -not (Test-Path $CHROME)) { Write-Host "✗ 找不到 Chrome(可設 CHROME=…)"; exit 1 }
if (-not (Test-Path -LiteralPath $REPLAY)) { Write-Host "✗ 找不到 REPLAY:$REPLAY"; exit 1 }
if (-not (Test-Path -LiteralPath $REPLAY_SPINS)) { Write-Host "✗ 找不到 REPLAY_SPINS:$REPLAY_SPINS"; exit 1 }

# -Source math:games\696\math\ 編回 raw(同 replay.ps1)
if ($Source -eq "math") {
  $mathDir = Join-Path $ROOT "games\696\math"; $genDir = Join-Path $ROOT "games\696\webcap\spins_from_math"
  if (-not (Test-Path -LiteralPath $mathDir)) { Write-Host "✗ -Source math 但找不到 $mathDir"; exit 1 }
  Write-Host "由 math\ 編回 raw → $genDir …"
  $gen = @'
import json, glob, os, sys
import math_adapter as ma
srcdir, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
for f in glob.glob(os.path.join(outdir, '*.json')): os.remove(f)
n = bad = 0
for i, f in enumerate(sorted(glob.glob(os.path.join(srcdir, '*.json')))):
    base = os.path.basename(f)
    try: env = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        print('  x 讀檔失敗', base, repr(e)); bad += 1; continue
    data = env.get('data') or env.get('spinresult') or (env if isinstance(env, dict) and 'board' in env else None)
    if not data:
        print('  x 略過(找不到 data/spinresult/board):', base); bad += 1; continue
    rid = base[:-5]
    try: raw = list(ma.math_to_wire(data))
    except Exception as e:
        print('  x 轉換失敗', base, '->', repr(e)); bad += 1; continue
    json.dump({'round_id': rid, 'idx': i, 'type': 0, 'ret': 0, 'raw': raw}, open(os.path.join(outdir, rid + '.json'), 'w', encoding='utf-8'))
    n += 1
print('  由 math 產出', n, '局' + (f'(另有 {bad} 檔略過/失敗)' if bad else ''))
if n == 0: sys.exit(1)
'@
  $gen | & python - $mathDir $genDir
  if ($LASTEXITCODE -ne 0) { Write-Host "✗ math→raw 轉換失敗"; exit 1 }
  $REPLAY_SPINS = $genDir
}

# ── 記錄真實時間,設回系統時鐘;結束(含 Ctrl+C)自動還原 ──
$realStart = Get-Date
$w32started = $false
try {
  Write-Host ("① 撥回系統時鐘 → {0}(現在真實時間 {1})" -f $TARGET.ToString("yyyy-MM-dd HH:mm:ss"), $realStart.ToString("yyyy-MM-dd HH:mm:ss"))
  try { Stop-Service w32time -EA SilentlyContinue; $w32started = $true } catch {}   # 停自動同步,免被拉回
  Set-Date -Date $TARGET | Out-Null

  # ② 停舊 mock / 舊 Chrome
  try { Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'routex[\\/]+server\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } } catch {}
  try { Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -like "*jili-replay-profile*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } } catch {}
  Start-Sleep -Milliseconds 500

  # ③ hosts:4 host → 127.0.0.1(tag # jili-replay,stop.ps1 會清)
  $esc = ($ALL_HOSTS | ForEach-Object { [regex]::Escape($_) }) -join "|"
  $lines = @(Get-Content -LiteralPath "$env:WINDIR\System32\drivers\etc\hosts")
  $kept = @($lines | Where-Object { $_ -notmatch '#\s*jili-replay\s*$' -and $_ -notmatch "^\s*127\.0\.0\.1\s+.*($esc)" })
  foreach ($h in $ALL_HOSTS) { $kept += "127.0.0.1 $h  # jili-replay" }
  [System.IO.File]::WriteAllLines("$env:WINDIR\System32\drivers\etc\hosts", $kept); ipconfig /flushdns | Out-Null

  # ④ 背景等 mock listen 後自動開 Chrome(本視窗留給 mock log)
  $URL = "https://$GHOST/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0"
  $prof = Join-Path $env:TEMP ("jili-replay-profile-" + [DateTimeOffset]::Now.ToUnixTimeSeconds())
  Get-ChildItem -LiteralPath $env:TEMP -Directory -Filter "jili-replay-profile-*" -EA SilentlyContinue | Remove-Item -Recurse -Force -EA SilentlyContinue
  Start-Job -ArgumentList $CHROME,$URL,$prof {
    param($chrome,$url,$prof)
    for ($i=0;$i -lt 40;$i++){ & curl.exe -sk -o NUL --max-time 1 "https://127.0.0.1/" 2>$null; if ($LASTEXITCODE -eq 0) { break }; Start-Sleep -Milliseconds 500 }
    $a=@(('--user-data-dir="{0}"' -f $prof),"--ignore-certificate-errors","--disable-quic","--no-first-run","--no-default-browser-check","--disable-features=ChromeWhatsNewUI",('"{0}"' -f $url)) -join " "
    Start-Process -FilePath $chrome -ArgumentList $a
  } | Out-Null

  # ⑤ 前景起 mock(本視窗=log;Ctrl+C 收工 → 進 finally 還原時鐘)
  if ($ROUNDS) { Write-Host "② 起 mock:★只播指定局★ → $ROUNDS" } else { Write-Host "② 起 mock:播 spins_raw 全部(循環)" }
  Write-Host "   時鐘已撥回 $($TARGET.ToString('yyyy-MM-dd'));Chrome 會自動開;看到 handshake/kind=init/spin 就是通了。"
  Write-Host "   ★別開 DevTools★。收工按 Ctrl+C(會自動還原時鐘),再跑 .\stop.ps1 還原 hosts。"
  Write-Host "────────────────────────────────────────────"
  $env:PORT="$PORT"; $env:TLS="1"; $env:VERBOSE="1"; $env:INJECT_BUNDLE="1"
  $env:REPLAY="$REPLAY"; $env:REPLAY_SPINS="$REPLAY_SPINS"
  if ($ROUNDS) { $env:REPLAY_ROUNDS="$ROUNDS" }
  & python routex\server.py
}
finally {
  # 還原系統時鐘:真實now ≈ realStart + (期間經過的時間)。期間經過 = 現在(假)時鐘 - TARGET。
  try {
    $elapsed = (Get-Date) - $TARGET
    if ($elapsed.TotalSeconds -lt 0) { $elapsed = New-TimeSpan -Seconds 0 }
    $restore = $realStart + $elapsed
    Set-Date -Date $restore | Out-Null
    Write-Host ("`n③ 已還原系統時鐘 → {0}" -f $restore.ToString("yyyy-MM-dd HH:mm:ss"))
  } catch { Write-Host "⚠ 還原時鐘失敗,請手動校正時間或開自動同步" }
  try { if ($w32started) { Start-Service w32time -EA SilentlyContinue }; & w32tm /resync /force 2>$null | Out-Null } catch {}
  Write-Host "  (hosts 還沒還原 → 跑 .\stop.ps1)"
}
