# fetch_assets.ps1 — 一口氣解決換平台的圖檔 404。Windows 版。
#   掃 mirror 缺的 .webp(astc→webp 缺口)→ 能從真站抓的抓回、抓不到的補「透明佔位圖」→ 零 404。
#   每次 server 換整包(game_site_backup 被換掉)後跑一次即可。
#   ★抓真站要 VPN=巴西(BR)★;沒 BR 也會跑,只是抓不到的會全變佔位圖。
# 用法:.\fetch_assets.ps1   [696]

param([string]$GID = "696")

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$ROOT = $PSScriptRoot; Set-Location -LiteralPath $ROOT
$env:PYTHONUTF8 = "1"

$c = (& curl.exe -s --max-time 6 https://ipinfo.io/json 2>$null | ConvertFrom-Json).country
Write-Host "出口國 = $c  $(if ($c -eq 'BR'){'✓'}else{'⚠ 不是 BR;抓不到的會補佔位圖'})"

$py = @'
import sys, os, base64
sys.path.insert(0, '.')
import fetch_missing_assets as fa
BASE = fa.BASE
PLACE = base64.b64decode('UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4HAA==')  # 1x1 透明 webp
missing = []
for dp, _, fns in os.walk(BASE):
    for fn in fns:
        if fn.endswith('.astc'):
            w = os.path.join(dp, fn[:-5] + '.webp')
            if not os.path.isfile(w):
                missing.append(os.path.relpath(w, BASE).replace(os.sep, '/'))
print(f'缺 {len(missing)} 個 webp')
got = place = 0
for rel in missing:
    data = fa.fetch(rel)                 # 需 BR;抓不到回 None
    dest = os.path.join(BASE, *rel.split('/'))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if data:
        open(dest, 'wb').write(data); got += 1
        print('  [real]', rel, len(data), 'B')
    else:
        open(dest, 'wb').write(PLACE); place += 1
        print('  [placeholder]', rel)
print(f'完成:真站抓回 {got} / 補佔位圖 {place} / 共 {len(missing)}')
'@
$py | & python -
