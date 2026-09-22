#!/usr/bin/env python3
"""webcap_math_view.py — 把真實封包轉成【機率團隊介面】的參考樣本。

機率只關心兩件事:輸入 spinReq、輸出 spinresult。
加解密 / protobuf / envelope 怎麼串是遊戲層的事,不進這份檔案。

形狀 = 舊 JILI 機台(1811+)那個 envelope,一格不多一格不少:
    {"data":{…}, "service":{}, "postMoney":…, "roundIndexV2":"…", "spinReq":{…}}

裡面的 data / spinReq 就是 games/<gid>/math_696.proto 的 JSON 形狀
(全 int,沒有 bytes)。轉換走 math_adapter.py,與「機率吐回來要編回 wire」是同一份
實作的反向,所以不會兩套走鐘。

用法:
  ./.venv/bin/python webcap_math_view.py 696 --exch-raw games/696/exchanges_ordered.jsonl
  ./.venv/bin/python webcap_math_view.py 696 --exch-raw games/696/webcap/exchanges_ordered.jsonl
      # 可分次餵不同 capture;all.jsonl 每次由整個輸出目錄重建,不會蓋掉前一批

輸出(預設 games/<gid>/math/):
  <round_id>.json   每局一個 ★給機率的就是這批★
  all.jsonl         同內容一行一局
"""
import os, sys, json, glob, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import math_adapter as ma


def dumps(obj, width=96, _ind=0):
    """縮排式 JSON,但「整段塞得下一行」的 dict/list 就收成一行。

    機率習慣的舊格式本來就是緊湊的(`"Symbol":[6,2,2]`),而且 server 主控台每局要印,
    攤開成一格一行會直接刷爆畫面(一局 90 行 vs 30 行)。"""
    pad = ' ' * _ind
    flat = json.dumps(obj, ensure_ascii=False, separators=(', ', ': '))
    if len(flat) + _ind <= width or not isinstance(obj, (dict, list)) or not obj:
        return flat
    if isinstance(obj, list):
        # 純數字/字串的陣列一律【橫著排】,太長就折行 —— window 在 nudge 局可以到 505 格,
        # 一格一行會完全看不出形狀。
        if all(not isinstance(v, (dict, list)) for v in obj):
            parts = [json.dumps(v, ensure_ascii=False) for v in obj]
            rows, cur = [], ''
            for i, part in enumerate(parts):
                piece = part + (', ' if i < len(parts) - 1 else '')
                if cur and _ind + 2 + len(cur) + len(piece) > width:
                    rows.append(cur); cur = piece
                else:
                    cur += piece
            if cur:
                rows.append(cur)
            return '[\n' + '\n'.join(pad + '  ' + r for r in rows) + '\n' + pad + ']'
        items = [pad + '  ' + dumps(v, width, _ind + 2) for v in obj]
        return '[\n' + ',\n'.join(items) + '\n' + pad + ']'
    items = [pad + '  ' + json.dumps(k, ensure_ascii=False) + ': ' + dumps(v, width, _ind + 2)
             for k, v in obj.items()]
    return '{\n' + ',\n'.join(items) + '\n' + pad + '}'


def fmt_round(rid):
    s = str(rid or '')
    return f'{s[:5]}-{s[5:11]}-{s[11:]}' if len(s) == 19 else s


def iter_payloads(src_dir, exch_raw):
    """兩種來源都吃,統一吐 SpinResult 的 payload bytes:
         A. exchanges_ordered.jsonl — raw 已是解密後的 payload(局數通常多很多)
         B. backend_raw/spins/*.json — 取 payload_hex"""
    if exch_raw:
        for line in open(exch_raw, encoding='utf-8'):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get('kind') == 'spin' and r.get('type') == 0 and r.get('raw'):
                yield bytes(r['raw'])
        return
    for fp in sorted(glob.glob(os.path.join(src_dir, '*.json'))):
        d = json.load(open(fp, encoding='utf-8'))
        if d.get('payload_hex'):
            yield bytes.fromhex(d['payload_hex'])


ANTE_SPECIAL = {'ANTE_NONE': {}, 'ANTE_1_5X': {'ante': 'ANTE_1_5X'}, 'ANTE_8X': {'ante': 'ANTE_8X'}}


def build_envelope(payload):
    """外圈【完全對齊舊 JILI 機台】的形狀。

    ★`data` 是信封的槽位,不是訊息名★ —— 舊機台的訊息叫 SpinAck、一樣塞在 data 裡;
    我們的訊息叫 SpinResult(見 math_696.proto),同樣塞 data。外圈五格與舊機台完全相同。

    刻意不放 paidBet / totalWin —— 舊機台沒有,機率看了會覺得多。
    ★實扣 = base_bet × {1, 1.5, 8},封包裡沒有這一格,算 RTP 必須自己乘★
    (規則寫在 games/696/math/INTERFACE.md)。
    """
    sr = ma.wire_to_math(payload)
    return {
        'data':         sr,
        'service':      {},
        'postMoney':    sr['balance'],
        'roundIndexV2': sr['round_id'],
        # 舊機台的 spinReq 形狀:{bet, special}。special 空 = 沒開額外下注。
        'spinReq':      {'bet': sr['base_bet'], 'special': ANTE_SPECIAL.get(sr['ante'], {})},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('gid', nargs='?', default='696')
    ap.add_argument('--src', help='backend_raw/spins 目錄(預設 games/<gid>/webcap/backend_raw/spins)')
    ap.add_argument('--exch-raw', help='exchanges_ordered.jsonl(含已解密 raw);給了就用這個當來源')
    ap.add_argument('--out', help='輸出目錄(預設 games/<gid>/math)')
    a = ap.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    src = a.src or os.path.join(root, 'games', a.gid, 'webcap', 'backend_raw', 'spins')
    out = a.out or os.path.join(root, 'games', a.gid, 'math')
    os.makedirs(out, exist_ok=True)

    n = 0
    for payload in iter_payloads(src, a.exch_raw):
        env = build_envelope(payload)
        rid = fmt_round(env['roundIndexV2']) or f'spin{n:04d}'
        with open(os.path.join(out, f'{rid}.json'), 'w', encoding='utf-8') as fh:
            fh.write(dumps(env) + '\n')
        n += 1
    if not n:
        sys.exit(f'[FATAL] 來源沒有 spin;先跑 webcap_backend_raw.py {a.gid},或給 --exch-raw')

    merged = [json.load(open(fp, encoding='utf-8'))
              for fp in sorted(glob.glob(os.path.join(out, '*.json')))]
    merged.sort(key=lambda r: r.get('roundIndexV2') or '')
    with open(os.path.join(out, 'all.jsonl'), 'w', encoding='utf-8') as fh:
        for r in merged:
            fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'寫出 {n} 局 → {out}/<round_id>.json;all.jsonl 累計 {len(merged)} 局')


if __name__ == '__main__':
    main()
