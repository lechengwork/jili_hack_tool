#!/usr/bin/env python3
"""把一次 capture 的 exchanges_ordered.jsonl 切成「每局兩個檔」:
   <base>/spins/<局號>.json      純分析(無 raw,給機率團隊)
   <base>/spins_raw/<局號>.json  含 raw(供 server REPLAY_SPINS 回放)
與 live 擷取(server.py)、批次收尾(webcap_pretty.py)產出的格式完全一致——
這支專門補「舊的、只有 exchanges 沒切每局檔」的 capture。

用法:
  ./.venv/bin/python spins_split.py games/696/webcap/exchanges_ordered.jsonl
      # 預設 base = 該 exchanges 所在目錄 → 寫 games/696/webcap/{spins,spins_raw}
  ./.venv/bin/python spins_split.py <exch.jsonl> --out <base_dir>

  回放: REPLAY_SPINS=<base>/spins_raw ... routex/server.py
"""
import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import webcap_pretty as wp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exch', help='某次 capture 的 exchanges_ordered.jsonl(含 raw)')
    ap.add_argument('--out', help='輸出 base 目錄(預設=exch 所在目錄);底下會建 spins/ 與 spins_raw/')
    a = ap.parse_args()
    base = a.out or (os.path.dirname(a.exch) or '.')
    spins_dir = os.path.join(base, 'spins')
    spins_raw_dir = os.path.join(base, 'spins_raw')
    n = 0
    for line in open(a.exch, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if not (r.get('kind') == 'spin' and r.get('type') == 0 and r.get('raw')):
            continue
        pretty = wp.prettify({'type': r['type'], 'ret': r.get('ret', 0),
                              'len': r.get('len', 0), 'raw': r['raw'], 'idx': r.get('idx')})
        if wp.write_spin_pair(pretty, r['raw'], spins_dir, spins_raw_dir):
            n += 1
    print(f'寫出 {n} 局 → {spins_dir}/ (純分析) + {spins_raw_dir}/ (含raw供回放)')


if __name__ == '__main__':
    main()
