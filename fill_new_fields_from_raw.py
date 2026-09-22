#!/usr/bin/env python3
"""fill_new_fields_from_raw.py — 用原始封包(raw)還原舊 math 檔缺的 gift_pool / respin_prev(★真值,非猜測★)。

對 games/696/math 底下每個局檔:
  依檔名 round_id(去掉 SP 資料夾的 "prefix__")找對應 raw
     webcap/spins_raw/<rid>.json 優先,backend_raw/spins/<rid>.json 備援
  → 用新 math_adapter.wire_to_math(raw) 取【真正的】gift_pool / respin_prev
  → 補進 board(鍵序比照 migrate_0921:gift_pool、boost_symbols、respin_prev 接在 nudge_pos 後)
找不到 raw 的(例如附帶的 6 個新樣本,本就已有正確值)保留原值。
有 all.jsonl 的資料夾會一併重建。冪等、可重跑。

用法:
  python fill_new_fields_from_raw.py --dry-run          # 只看會改幾個
  python fill_new_fields_from_raw.py                     # 實跑(games/696/math 全部)
  python fill_new_fields_from_raw.py games/696/math/normal   # 指定目錄
"""
import json, glob, os, sys
sys.path.insert(0, '.')
import math_adapter as ma

def build_raw_index():
    idx = {}
    for d in ['games/696/webcap/spins_raw', 'games/696/webcap/backend_raw/spins']:
        for f in glob.glob(d + '/*.json'):
            idx.setdefault(os.path.basename(f)[:-5], f)   # spins_raw 先掃 → 優先
    return idx

def raw_board(path):
    o = json.load(open(path, encoding='utf-8'))
    raw = bytes(o['raw']) if o.get('raw') else bytes.fromhex(o.get('payload_hex', ''))
    return ma.wire_to_math(raw)['board']

def reorder(b, gp, rp):
    out = {}
    for k, v in b.items():
        if k in ('gift_pool', 'respin_prev', 'boost_symbols'):
            continue
        out[k] = v
        if k == 'nudge_pos':
            out['gift_pool'] = gp
            out['boost_symbols'] = b.get('boost_symbols', [])
            out['respin_prev'] = rp
    out.setdefault('gift_pool', gp)
    out.setdefault('boost_symbols', b.get('boost_symbols', []))
    out.setdefault('respin_prev', rp)
    return out

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    root = args[0] if args else os.path.join('games', '696', 'math')
    files = glob.glob(os.path.join(root, '**', '*.json'), recursive=True)
    idx = build_raw_index()
    frm_raw = kept = changed = trig = 0
    touched_dirs = set()
    for f in files:
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        b = (d.get('data') or {}).get('board')
        if not isinstance(b, dict):
            continue
        rid = os.path.basename(f)[:-5].split('__')[-1]
        if rid in idx:
            rb = raw_board(idx[rid]); gp = rb.get('gift_pool', []); rp = rb.get('respin_prev', []); frm_raw += 1
        else:
            gp = b.get('gift_pool', []); rp = b.get('respin_prev', []); kept += 1
        if gp or rp:
            trig += 1
        new = reorder(b, gp, rp)
        if new != b:
            changed += 1
            if not dry:
                d['data']['board'] = new
                with open(f, 'w', encoding='utf-8') as fh:
                    json.dump(d, fh, ensure_ascii=False, indent=2)
                touched_dirs.add(os.path.dirname(f))
    # 重建有 all.jsonl 的資料夾
    if not dry:
        for dpath in touched_dirs:
            ap = os.path.join(dpath, 'all.jsonl')
            if os.path.exists(ap):
                rows = [json.load(open(p, encoding='utf-8'))
                        for p in sorted(glob.glob(os.path.join(dpath, '*.json')))]
                rows.sort(key=lambda r: r.get('roundIndexV2') or '')
                with open(ap, 'w', encoding='utf-8') as fh:
                    for r in rows:
                        fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(('[dry-run] ' if dry else '') +
          f'掃描 {len(files)} 檔:raw還原 {frm_raw} / 無raw保留原值 {kept} / '
          f'實際改動 {changed} / 其中有觸發值(gift_pool或respin_prev非空){trig}')

if __name__ == '__main__':
    sys.exit(main())
