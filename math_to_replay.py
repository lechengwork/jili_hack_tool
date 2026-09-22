#!/usr/bin/env python3
"""math_to_replay.py — 把【機率格式】的每局 json 轉成 replay.sh 吃得下的 spins_raw 檔。

機率交回來的是 `games/696/math/<局號>.json` 那個形狀(envelope: data/spinReq/…),
沒有 `raw`;而 `routex/server.py` 的 REPLAY_SPINS 只讀有 `raw` 的檔。這支補中間那段:

    機率 json ──math_adapter.math_to_wire()──> SpinResult payload bytes ──> {…, raw:[…]}

用法:
    ./.venv/bin/python3 math_to_replay.py <輸入目錄或檔案…> -o <輸出目錄>
    REPLAY=games/696/webcap/exchanges_ordered.jsonl REPLAY_SPINS=<輸出目錄> ./replay.sh [局名片段]

驗證:同一支轉換在 829 局真實封包上 wire→math→wire byte 完全相同(math_adapter --selftest)。
"""
import argparse, glob, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import math_adapter as ma


def convert(path, outdir, name=None):
    m = json.load(open(path, encoding='utf-8'))
    data = m.get('data') or m            # 容忍直接給 data 的情況
    raw = ma.math_to_wire(data)
    rid = str(data.get('round_id') or m.get('roundIndexV2') or '')
    stem = name or os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(outdir, stem + '.json')
    json.dump({'round_id': rid, 'idx': 0, 'type': 0, 'ret': 0, 'raw': list(raw)},
              open(out, 'w', encoding='utf-8'))
    return out, len(raw), rid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src', nargs='+', help='機率格式 json 檔或目錄')
    ap.add_argument('-o', '--out', required=True, help='輸出目錄(給 REPLAY_SPINS)')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    files = []
    for s in a.src:
        files += sorted(glob.glob(os.path.join(s, '*.json'))) if os.path.isdir(s) else [s]
    for f in files:
        out, n, rid = convert(f, a.out)
        print(f'  {os.path.basename(f):48} -> {os.path.basename(out):48} {n:4}B rid={rid}')
    print(f'{len(files)} 局 -> {a.out}')


if __name__ == '__main__':
    main()
