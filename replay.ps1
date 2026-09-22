# replay.ps1 — 一鍵本地回放 JILI 696(免鑄子網域;用已白名單的 uat-wbgame)。Windows 版。
# 對應 replay.sh,但改 443 + hosts(Windows 上 --host-resolver-rules 不穩)。開頭跳一次 UAC。
#
#   .\replay.ps1                          # 播預設全部(spins_raw,循環)
#   .\replay.ps1 24126-883680-00240696    # 只播這一局(可逗號多局,依序)
#   .\replay.ps1 -Source math             # ★改讀 games\696\math\(編回 raw 再播)→ 你改 math 的數字就會演出來
#   .\replay.ps1 24126-883680-00240696 -Source math   # 兩者可併用
#
# 這個視窗會變成 mock 的 log(每 spin 印一次);收工按 Ctrl+C,再跑 .\stop.ps1 還原 hosts。
# ★別開 DevTools★

param([string]$Rounds = "", [ValidateSet("spins","math")][string]$Source = "spins")

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$ident = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not (New-Object Security.Principal.WindowsPrincipal($ident)).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
  Write-Host "需要系統管理員(綁 443 + 改 hosts)→ 跳 UAC…"
  $rl = "& '$PSCommandPath'"; if ($Rounds) { $rl += " -Rounds '$Rounds'" }; if ($Source) { $rl += " -Source '$Source'" }
  Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList @("-NoExit","-NoProfile","-ExecutionPolicy","Bypass","-Command",$rl)
  exit
}

$ROOT = $PSScriptRoot; Set-Location -LiteralPath $ROOT
$env:PYTHONUTF8 = "1"
$PORT = 443
$GHOST = "uat-wbgame.jlfafafa3.com"   # 本來就在白名單 → 免鑄子網域
$ALL_HOSTS = @("uat-wbgame.jlfafafa3.com","uat-wbwebapi.jlfafafa2.com","uat-wbslot-fd.jlfafafa1.com","uat-wbslot-platform.jlfafafa3.com")

$CHROME = $env:CHROME
if (-not $CHROME) { foreach ($p in @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe","${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe","$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe")) { if (Test-Path $p) { $CHROME=$p; break } } }

$REPLAY = if ($env:REPLAY) { $env:REPLAY } else { Join-Path $ROOT "games\696\webcap\exchanges_ordered.jsonl" }
$REPLAY_SPINS = if ($env:REPLAY_SPINS) { $env:REPLAY_SPINS } else { Join-Path $ROOT "games\696\webcap\spins_raw" }
$ROUNDS = if ($Rounds) { $Rounds } elseif ($env:REPLAY_ROUNDS) { $env:REPLAY_ROUNDS } else { "" }

# -Source math:把 games\696\math\ 的每局用 math_adapter.math_to_wire 編回 raw → 產可重播的檔
# 這樣「改 math\ 裡的數字 → 重播就演你改的結果」。math→raw 是無損(math_adapter --selftest 驗過)。
if ($Source -eq "math") {
  $mathDir = Join-Path $ROOT "games\696\math"
  $genDir  = Join-Path $ROOT "games\696\webcap\spins_from_math"
  if (-not (Test-Path -LiteralPath $mathDir)) { Write-Host "✗ -Source math 但找不到 $mathDir"; exit 1 }
  Write-Host "由 math\ 編回 raw → $genDir …"
  $gen = @'
import json, glob, os, sys
import math_adapter as ma
srcdir, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
for f in glob.glob(os.path.join(outdir, '*.json')): os.remove(f)
n = bad = 0
# 依檔名排序 = 播放順序。你可用 001.json/002.json… 控制順序;檔名(去 .json)= round_id。
for i, f in enumerate(sorted(glob.glob(os.path.join(srcdir, '*.json')))):
    base = os.path.basename(f)
    try: env = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        print('  x 讀檔失敗', base, repr(e)); bad += 1; continue
    # 接受三種寫法:{data:{…}} / {spinresult:{…}} / 直接就是 spinresult(含 board)
    data = env.get('data') or env.get('spinresult') or (env if isinstance(env, dict) and 'board' in env else None)
    if not data:
        print('  x 略過(找不到 data/spinresult/board):', base); bad += 1; continue
    rid = base[:-5]
    try:
        raw = list(ma.math_to_wire(data))
    except Exception as e:
        print('  x 轉換失敗', base, '->', repr(e), '(欄位形狀要照 math_696.proto)'); bad += 1; continue
    json.dump({'round_id': rid, 'idx': i, 'type': 0, 'ret': 0, 'raw': raw},
              open(os.path.join(outdir, rid + '.json'), 'w', encoding='utf-8'))
    n += 1
print('  由 math 產出', n, '局' + (f'(另有 {bad} 檔略過/失敗)' if bad else ''))
if n == 0:
    print('  x 沒有任何有效的局 — 檢查 math\\ 檔的欄位形狀'); sys.exit(1)
'@
  $gen | & python - $mathDir $genDir
  if ($LASTEXITCODE -ne 0) { Write-Host "✗ math→raw 轉換失敗"; exit 1 }
  $REPLAY_SPINS = $genDir
}

if (-not (Get-Command python -EA SilentlyContinue)) { Write-Host "✗ 找不到 python"; exit 1 }
if (-not $CHROME -or -not (Test-Path $CHROME)) { Write-Host "✗ 找不到 Chrome(可設 CHROME=…)"; exit 1 }
if (-not (Test-Path -LiteralPath $REPLAY)) { Write-Host "✗ 找不到 REPLAY 檔:$REPLAY"; exit 1 }
if (-not (Test-Path -LiteralPath $REPLAY_SPINS)) { Write-Host "✗ 找不到 REPLAY_SPINS 目錄:$REPLAY_SPINS"; exit 1 }

# ① 停舊 mock(換局不生效的元凶:舊 mock 被重用)
try { Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'routex[\\/]+server\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } } catch {}
try { Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -like "*jili-replay-profile*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } } catch {}
Start-Sleep -Milliseconds 500

# ② hosts:4 個遊戲 host → 127.0.0.1(tag # jili-replay,stop.ps1 會清)
$esc=($ALL_HOSTS|ForEach-Object{[regex]::Escape($_)}) -join "|"
$lines=@(Get-Content -LiteralPath "$env:WINDIR\System32\drivers\etc\hosts")
$kept=@($lines | Where-Object { $_ -notmatch '#\s*jili-replay\s*$' -and $_ -notmatch "^\s*127\.0\.0\.1\s+.*($esc)" })
foreach ($h in $ALL_HOSTS) { $kept += "127.0.0.1 $h  # jili-replay" }
[System.IO.File]::WriteAllLines("$env:WINDIR\System32\drivers\etc\hosts",$kept); ipconfig /flushdns | Out-Null

# ③ 背景等 mock listen 後自動開 Chrome(本視窗留給 mock log)
$URL="https://$GHOST/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0"
$prof=Join-Path $env:TEMP ("jili-replay-profile-"+[DateTimeOffset]::Now.ToUnixTimeSeconds())
Get-ChildItem -LiteralPath $env:TEMP -Directory -Filter "jili-replay-profile-*" -EA SilentlyContinue | Remove-Item -Recurse -Force -EA SilentlyContinue
Start-Job -ArgumentList $CHROME,$URL,$prof {
  param($chrome,$url,$prof)
  for ($i=0;$i -lt 40;$i++){ & curl.exe -sk -o NUL --max-time 1 "https://127.0.0.1/" 2>$null; if ($LASTEXITCODE -eq 0) { break }; Start-Sleep -Milliseconds 500 }
  $a=@(('--user-data-dir="{0}"' -f $prof),"--ignore-certificate-errors","--disable-quic","--no-first-run","--no-default-browser-check","--disable-features=ChromeWhatsNewUI",('"{0}"' -f $url)) -join " "
  Start-Process -FilePath $chrome -ArgumentList $a
} | Out-Null

# ④ 前景起 mock(本視窗=log;Ctrl+C 收工)
if ($ROUNDS) { Write-Host "② 起 mock:★只播指定局★ → $ROUNDS" } else { Write-Host "② 起 mock:播 spins_raw 全部(循環)" }
Write-Host "   (Chrome 會在 mock listen 後自動開;收工 Ctrl+C,再跑 .\stop.ps1 還原 hosts)"
Write-Host "────────────────────────────────────────────"
$env:PORT="$PORT"; $env:TLS="1"; $env:VERBOSE="1"; $env:INJECT_BUNDLE="1"
$env:REPLAY="$REPLAY"; $env:REPLAY_SPINS="$REPLAY_SPINS"
if ($ROUNDS) { $env:REPLAY_ROUNDS="$ROUNDS" }
& python routex\server.py
