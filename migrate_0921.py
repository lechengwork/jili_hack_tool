#!/usr/bin/env python3
"""migrate_0921.py — 把 0911 版的舊局檔補成 0921 的新格式。

0921 起 board 固定多兩個鍵(沒觸發＝空陣列):
    gift_pool    饋贈①(nudge_pos[0])挑中的 3~5 個倍率符號
    respin_prev  饋贈④(nudge_pos[4])被重轉那一軸【重轉前】的 3 個符號

舊檔沒有這兩個鍵,新舊混在一起會讓解析器炸掉。這支就是把舊檔補齊。

★零相依,Windows 內建 python 直接跑★
    python migrate_0921.py games\\696\\math
    python migrate_0921.py games\\696\\math --dry-run     只看會改幾個,不寫檔

安全性:只在【缺鍵】時補【空陣列】,不動任何既有值;已經是新格式的檔會跳過。
舊檔本來就不可能有這兩個欄位的值 —— 那兩種效果在舊樣本裡一次都沒出現過。
"""
import json, os, sys, glob

def migrate(path, dry=False):
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    b = (d.get('data') or {}).get('board')
    if not isinstance(b, dict):
        return False
    if 'gift_pool' in b and 'respin_prev' in b:
        return False                      # 已經是新格式
    out = {}
    for k, v in b.items():
        out[k] = v
        if k == 'nudge_pos':              # 插在 nudge_pos 後面,與新檔同序
            out['gift_pool'] = []
            out.setdefault('boost_symbols', b.get('boost_symbols', []))
            out['respin_prev'] = []
    out.setdefault('gift_pool', [])
    out.setdefault('respin_prev', [])
    # boost_symbols 只留一份,位置以第一次出現為準
    d['data']['board'] = out
    if not dry:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    return True

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    root = args[0] if args else os.path.join('games', '696', 'math')
    files = sorted(glob.glob(os.path.join(root, '*.json')))
    if not files:
        print(f'找不到任何 .json:{root}'); return 1
    n = sum(1 for p in files if migrate(p, dry))
    print(f'{"[試跑] 會補" if dry else "已補"} {n} 個檔 / 掃描 {len(files)} 個({len(files)-n} 個已是新格式)')
    return 0

if __name__ == '__main__':
    sys.exit(main())
