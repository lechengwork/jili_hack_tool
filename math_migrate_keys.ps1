# math_migrate_keys.ps1 — 把既有樣本檔同步到最新格式(冪等,可重複跑)。Windows 版。
# 對應 math_migrate_keys.sh。收工後跑一次即可。
#   .\math_migrate_keys.ps1            # 掃所有 games\696\math* 目錄
#   .\math_migrate_keys.ps1 <目錄>…

param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Dirs)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$ROOT = $PSScriptRoot; Set-Location -LiteralPath $ROOT
$env:PYTHONUTF8 = "1"

if (-not $Dirs -or $Dirs.Count -eq 0) {
  $Dirs = @(Get-ChildItem -LiteralPath "games\696" -Directory -Filter "math*" -EA SilentlyContinue | ForEach-Object { "games/696/$($_.Name)" })
}
if (-not $Dirs -or $Dirs.Count -eq 0) { Write-Host "(沒有 games\696\math* 目錄可處理)"; exit 0 }

$py = @'
import sys, os, json, glob
sys.path.insert(0, '.')
import webcap_math_view as mv

RAW = {}
for fp in glob.glob('games/696/webcap/backend_raw/spins/*.json'):
    try:
        d = json.load(open(fp, encoding='utf-8'))
        if d.get('type') == 0 and d.get('payload_hex') and d.get('round_id'):
            RAW[str(d['round_id'])] = d['payload_hex']
    except Exception:
        pass

RENAME = {'win_line_cnt': 'win_type', 'has_win': 'win_type'}
ORDER = ['reels', 'window', 'line_wins', 'win_type', 'multiplier', 'rtp_const',
         'window_extra', 'window_extra2', 'nudge_group', 'nudge_pos',
         'boost_symbols', 'post_nudge']
rebuilt = patched = clean = 0
for d in sys.argv[1:]:
    for fp in glob.glob(os.path.join(d, '*.json')):
        env = json.load(open(fp, encoding='utf-8'))
        rid = os.path.basename(fp)[:-5]
        if rid in RAW:
            env = mv.build_envelope(bytes.fromhex(RAW[rid]))
            rebuilt += 1
        else:
            before = json.dumps(env)
            b = (env.get('data') or env.get('spinresult') or {}).get('board') or {}
            b = {RENAME.get(k, k): v for k, v in b.items()}
            b.setdefault('window_extra2', 0)
            b.setdefault('boost_symbols', [])
            sr = env.get('data') or env['spinresult']
            sr['board'] = {k: b[k] for k in ORDER if k in b}
            ante = sr.get('ante', 'ANTE_NONE')
            env = {
                'data':         sr,
                'service':      {},
                'postMoney':    sr.get('balance', 0.0),
                'roundIndexV2': sr.get('round_id', ''),
                'spinReq':      {'bet': sr.get('base_bet', 0.0),
                                 'special': {} if ante == 'ANTE_NONE' else {'ante': ante}},
            }
            if json.dumps(env) == before:
                clean += 1
                continue
            patched += 1
        with open(fp, 'w', encoding='utf-8') as fh:
            fh.write(mv.dumps(env) + '\n')
    rows = [json.load(open(f, encoding='utf-8'))
            for f in sorted(glob.glob(os.path.join(d, '*.json')))]
    if rows:
        rows.sort(key=lambda r: r.get('roundIndexV2') or '')
        with open(os.path.join(d, 'all.jsonl'), 'w', encoding='utf-8') as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f'從原始封包重產 {rebuilt} 檔 / 就地補欄位 {patched} 檔 / 已是最新 {clean} 檔;all.jsonl 已重建')
'@
$py | & python - @Dirs
