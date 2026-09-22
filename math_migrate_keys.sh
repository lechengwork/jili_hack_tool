#!/usr/bin/env bash
# math_migrate_keys.sh — 把既有樣本檔同步到最新格式(冪等,可重複跑)。
#   1) 有對應的 backend_raw 原始封包 → 直接從 payload_hex 重新產生(最可靠)
#   2) 沒有的 → 就地補欄位:win_line_cnt→has_win、補上缺的 window_extra2
# 擷取中的 server 用的是載入記憶體的舊模組,收工後跑一次即可。
#   ./math_migrate_keys.sh            # 掃所有 games/696/math* 目錄
#   ./math_migrate_keys.sh <目錄>…
set -u
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIRS="${*:-$(ls -d games/696/math* 2>/dev/null)}"
.venv/bin/python - $DIRS <<'PYEOF'
import sys, os, json, glob
sys.path.insert(0, '.')
import webcap_math_view as mv

# round_id → payload_hex(有原始封包的就用它重產)
RAW = {}
for fp in glob.glob('games/696/webcap/backend_raw/spins/*.json'):
    try:
        d = json.load(open(fp, encoding='utf-8'))
        if d.get('type') == 0 and d.get('payload_hex') and d.get('round_id'):
            RAW[str(d['round_id'])] = d['payload_hex']
    except Exception:
        pass

RENAME = {'win_line_cnt': 'win_type', 'has_win': 'win_type'}
# ★順序要跟 math_adapter.wire_to_math 產出的完全一致★,不然「重產的」和「就地補的」
# 兩批檔案 key 順序會不同,肉眼 diff 起來很煩。
ORDER = ['reels', 'window', 'line_wins', 'win_type', 'multiplier', 'rtp_const',
         'window_extra', 'window_extra2', 'nudge_group', 'nudge_pos',
         'boost_symbols', 'post_nudge']
rebuilt = patched = clean = 0
for d in sys.argv[1:]:
    for fp in glob.glob(os.path.join(d, '*.json')):
        env = json.load(open(fp, encoding='utf-8'))
        rid = os.path.basename(fp)[:-5]
        if rid in RAW:                                   # ① 從原始封包重產
            env = mv.build_envelope(bytes.fromhex(RAW[rid]))
            rebuilt += 1
        else:                                            # ② 就地補(沒有原始封包可重產時)
            before = json.dumps(env)   # ★不能用 sort_keys★:那會忽略順序,純重排就不會被改寫
            b = (env.get('data') or env.get('spinresult') or {}).get('board') or {}
            b = {RENAME.get(k, k): v for k, v in b.items()}
            b.setdefault('window_extra2', 0)
            b.setdefault('boost_symbols', [])
            sr = env.get('data') or env['spinresult']
            sr['board'] = {k: b[k] for k in ORDER if k in b}
            # 外圈正規化成【舊機台形狀】:訊息塞 data,丟掉 totalWin / paidBet,spinReq 用 special
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
PYEOF
