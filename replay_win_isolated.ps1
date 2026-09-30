# replay_win_isolated.ps1 — Windows 版 696 重播「per-process 隔離版」。
#   跟 replay_win.ps1 差在:【不改系統時鐘、不改 hosts、免系統管理員】。
#   時間用 RunAsDate 只騙這兩個進程(python server + Chrome),DNS 用 --host-resolver-rules 只導向這個
#   Chrome 實例。→ 可以【另開一個正常 Chrome 同時連 JFS 玩真遊戲】,互不干擾(全機時鐘/DNS 都沒動)。
#
# 需要(比 replay_win.ps1 多一個):
#   • RunAsDate(NirSoft 免費):https://www.nirsoft.net/utils/run_as_date.html 下載 x64 解壓,
#     把 RunAsDate.exe 放到本資料夾,或設 $env:RUNASDATE 指到它。
#   • ★RunAsDate 要先在 GUI 勾一次「Inject the date/time into child processes」★
#     (Chrome 的遊戲 JS 跑在 renderer 子進程,不勾的話子進程沒被騙時鐘→date-lock 照樣觸發)。
#     勾完那個設定會記住,之後這支 CLI 就吃得到。
#
#   .\replay_win_isolated.ps1                        # 播全部
#   .\replay_win_isolated.ps1 24126-883680-00240696  # 只播指定局(可逗號多局)
#   .\replay_win_isolated.ps1 -Source math           # 改讀 games\696\math\ 編回 raw 再播
#
# 收工:mock log 視窗 Ctrl+C;Chrome 關視窗即可(沒有系統時鐘/hosts 要還原)。★別開 DevTools★。
#
# ⚠ 兩個要現場驗的坑:
#   1) RunAsDate 子進程注入沒開/沒生效 → 進遊戲會出 dateLock(handshake 前停)。→ 去 GUI 勾好再跑。
#   2) --host-resolver-rules 在某些 Windows 上不穩(這也是 replay.ps1 當初改用 hosts 的原因)。
#      若 Chrome 一直連不到本機 mock(splash 卡死、log 沒 [GET]),就改用 replay_win.ps1(全機版)。

param([string]$Rounds = "", [ValidateSet("spins","math")][string]$Source = "spins")
$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$ROOT = $PSScriptRoot; Set-Location -LiteralPath $ROOT
$env:PYTHONUTF8 = "1"
$PORT = 8443                          # 免 443 → 免系統管理員
$GHOST = "uat-wbgame.jlfafafa3.com"
# 撥到擷取日(在 date-lock 窗內)。要調就設 $env:FAKE_DATE="2026-09-05"
$FAKE = if ($env:FAKE_DATE) { [DateTime]::Parse($env:FAKE_DATE) } else { [DateTime]::Parse("2026-09-11") }
$RAD_DATE = $FAKE.ToString("dd\\MM\\yyyy")     # RunAsDate 日期格式 dd\mm\yyyy
$RAD_TIME = "12:00:00"

# --- RunAsDate ---
$RAD = $env:RUNASDATE
if (-not $RAD) { foreach ($p in @("$ROOT\RunAsDate.exe","$ROOT\RunAsDate-x64\RunAsDate.exe","$env:USERPROFILE\Downloads\RunAsDate.exe","$env:USERPROFILE\Downloads\RunAsDate-x64\RunAsDate.exe")) { if (Test-Path $p) { $RAD=$p; break } } }
if (-not $RAD -or -not (Test-Path $RAD)) {
  Write-Host "✗ 找不到 RunAsDate.exe。請到 https://www.nirsoft.net/utils/run_as_date.html 下載 x64,"
  Write-Host "  放到本資料夾(或設 `$env:RUNASDATE 指到它),並在其 GUI 勾一次「Inject the date/time into child processes」。"
  exit 1
}

$CHROME = $env:CHROME
if (-not $CHROME) { foreach ($p in @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe","${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe","$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe")) { if (Test-Path $p) { $CHROME=$p; break } } }
$REPLAY = if ($env:REPLAY) { $env:REPLAY } else { Join-Path $ROOT "games\696\webcap\exchanges_ordered.jsonl" }
$REPLAY_SPINS = if ($env:REPLAY_SPINS) { $env:REPLAY_SPINS } else { Join-Path $ROOT "games\696\webcap\spins_raw" }
$ROUNDS = if ($Rounds) { $Rounds } elseif ($env:REPLAY_ROUNDS) { $env:REPLAY_ROUNDS } else { "" }

if (-not (Get-Command python -EA SilentlyContinue)) { Write-Host "✗ 找不到 python"; exit 1 }
if (-not $CHROME -or -not (Test-Path $CHROME)) { Write-Host "✗ 找不到 Chrome(可設 `$env:CHROME=…)"; exit 1 }
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

# ① 停舊 mock / 舊 replay Chrome
try { Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'routex[\\/]+server\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } } catch {}
try { Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -like "*jili-iso-profile*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue } } catch {}
Start-Sleep -Milliseconds 500

# ② 起 mock(RunAsDate 騙時鐘 → server 回應時戳 f1 = 假日期;新視窗=log)
#    env 先設好,RunAsDate 起的 python 會繼承。
$env:PORT="$PORT"; $env:TLS="1"; $env:VERBOSE="1"; $env:INJECT_BUNDLE="1"
$env:REPLAY="$REPLAY"; $env:REPLAY_SPINS="$REPLAY_SPINS"
if ($ROUNDS) { $env:REPLAY_ROUNDS="$ROUNDS" } else { Remove-Item Env:\REPLAY_ROUNDS -EA SilentlyContinue }
$pyExe = (Get-Command python).Source
Write-Host "② 起 mock(RunAsDate 假時鐘 $($FAKE.ToString('yyyy-MM-dd')),埠 $PORT,不動系統時鐘)…"
Start-Process -FilePath $RAD -ArgumentList @("/movetime", $RAD_DATE, $RAD_TIME, "`"$pyExe`"", "routex\server.py")

# 等 mock listen
$ok=$false
for ($i=0;$i -lt 40;$i++){ & curl.exe -sk -o NUL --max-time 1 "https://127.0.0.1:$PORT/" 2>$null; if ($LASTEXITCODE -eq 0) { $ok=$true; break }; Start-Sleep -Milliseconds 500 }
if (-not $ok) { Write-Host "✗ mock 沒起來(看 RunAsDate 起的視窗;或 8443 被占)"; exit 1 }

# ③ 開 Chrome(RunAsDate 假時鐘 + host-resolver 只導這個實例 → 全機 DNS 不動)
$URL="https://$GHOST/fg5/?ssoKey=local-mock-token&lang=zh-CN&apiId=1778&be=moc.2afafaflj.ipabewbw-tau&domain_gs=1afafaflj&domain_platform=moc.3afafaflj.mroftalp-tolsbw-tau&gameID=696&gs=moc.1afafaflj.df-tolsbw-tau&iu=true&legalLang=true&skin=0"
$prof=Join-Path $env:TEMP ("jili-iso-profile-"+[DateTimeOffset]::Now.ToUnixTimeSeconds())
Get-ChildItem -LiteralPath $env:TEMP -Directory -Filter "jili-iso-profile-*" -EA SilentlyContinue | Remove-Item -Recurse -Force -EA SilentlyContinue
$chromeArgs = "--user-data-dir=`"$prof`" --host-resolver-rules=`"MAP * 127.0.0.1:$PORT`" --ignore-certificate-errors --disable-quic --no-first-run --no-default-browser-check --disable-features=ChromeWhatsNewUI `"$URL`""
Write-Host "③ 開 replay Chrome(RunAsDate 假時鐘 + host-resolver 只導本實例)…"
Start-Process -FilePath $RAD -ArgumentList @("/movetime", $RAD_DATE, $RAD_TIME, "`"$CHROME`"", $chromeArgs)

Write-Host ""
Write-Host "✅ 隔離版已啟動(系統時鐘/hosts 都沒動):"
Write-Host "   • 這個 replay Chrome:假時鐘 $($FAKE.ToString('yyyy-MM-dd')) + DNS 全導本機 mock。"
Write-Host "   • 要同時玩真的 → 【另開一個「正常的 Chrome」】連 JFS,不受影響。"
Write-Host "   • 看 mock log:有 handshake / kind=init / spin 就是通了;若出 dateLock=RunAsDate 子進程注入沒開(去 GUI 勾)。"
Write-Host "   ★別開 DevTools★。收工:mock 視窗 Ctrl+C、Chrome 關視窗(無需還原)。"
