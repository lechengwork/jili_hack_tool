#!/usr/bin/env python3
"""把 webcap 解出的 exchanges_ordered.jsonl 套上語意標籤 → 可讀 JSON(每局一行)。

欄位語意來自 games/696/GAME_FORMAT_SPEC.md(已驗證):
  回應外層明文 = {f3=type, f5=data, f6=error_msg, f7=ret};data 是各 type 的遊戲負載。
  decrypt_capture 已把 data 存成每行的 'raw'(bytes 陣列),本工具只負責「貼標籤」。

type 0 (spin):  f6=餘額 f3/f13=總中獎 f20=單號 f23.f1=底注 f23.f26=額外下注
                f1.f2.f1=盤面符號 f1.f1[]=各軸 f1.f6[]=中獎線(f3=線號,f4=線中獎) f1.f7=中獎線數 f1.f12=倍率
type 1 (config):f1.f3=幣別 f1.f4=餘額 f1.f5=bet 選單(packed f64) f1.f6/7/8=限額
type 2 (balance):f1.f2=餘額     type 58 (session):f1.f3=回合號 f1.f4=底注

用法:
  ./.venv/bin/python webcap_pretty.py 696            # 讀 games/696/webcap/exchanges_ordered.jsonl
  ./.venv/bin/python webcap_pretty.py 696 --in <jsonl> --out <jsonl>
  → 寫 games/696/webcap/pretty.jsonl(全部)+ 印 spin 摘要表
"""
import os, sys, json, struct, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'routex'))
from fg5 import dec_varint


def parse(buf):
    """protobuf → {field: [(wire, value), ...]}(保留重複欄位)。
    wire0→int, wire1→8B, wire2→bytes, wire5→4B。"""
    buf = bytes(buf)
    out, i, n = {}, 0, len(buf)
    try:
        while i < n:
            key, i = dec_varint(buf, i)
            f, w = key >> 3, key & 7
            if w == 0:   v, i = dec_varint(buf, i)
            elif w == 2: ln, i = dec_varint(buf, i); v = buf[i:i+ln]; i += ln
            elif w == 1: v = buf[i:i+8]; i += 8
            elif w == 5: v = buf[i:i+4]; i += 4
            else: break
            out.setdefault(f, []).append((w, v))
    except (IndexError, ValueError):
        pass
    return out


def _last(d, f):
    return d[f][-1][1] if f in d and d[f] else None

def V(d, f):                       # varint(int)
    v = _last(d, f); return v if isinstance(v, int) else None

def F(d, f):                       # f64(double)
    v = _last(d, f)
    return struct.unpack('<d', v)[0] if isinstance(v, (bytes, bytearray)) and len(v) == 8 else None

def M(d, f):                       # 巢狀 msg → parse
    v = _last(d, f)
    return parse(v) if isinstance(v, (bytes, bytearray)) else {}

def MALL(d, f):                    # 重複 msg → [parse,...]
    return [parse(v) for (w, v) in d.get(f, []) if isinstance(v, (bytes, bytearray))]

def B(d, f):                       # bytes → list[int]
    v = _last(d, f)
    return list(v) if isinstance(v, (bytes, bytearray)) else None


def fmt_round(n):
    """單號 varint → 顯示格式(5-6-8);末三碼=gameID。"""
    if not isinstance(n, int): return None
    s = str(n)
    return f'{s[:5]}-{s[5:11]}-{s[11:]}' if len(s) == 19 else s


def unpack_f64_array(raw):
    if not isinstance(raw, (bytes, bytearray)) or len(raw) % 8: return None
    return [struct.unpack('<d', raw[i:i+8])[0] for i in range(0, len(raw), 8)]


def ante_of(f23):
    """f23.f26 → 額外下注級別 + 付費倍率。無=沒開。"""
    if 26 not in f23:
        return None, 1.0
    f26 = M(f23, 26)
    lvl = V(f26, 1)
    if lvl == 1:  return '8x', 8.0
    return '1.5x', 1.5           # f26 空(f1=0 省略)= 1.5 倍


def pretty_spin(raw):
    top = parse(raw)
    info = M(top, 1)                 # f1 局面明細
    f23 = M(top, 23)                 # 下注資訊
    base = F(f23, 1)
    ante, mult_pay = ante_of(f23)
    paylines = []
    for ln in MALL(info, 6):         # f6[] 中獎線
        paylines.append({'line': V(ln, 3), 'win': F(ln, 4)})
    reels = [B(r, 1) for r in MALL(info, 1)]   # f1[] 各軸符號
    out = {
        'type': 0, 'kind': 'spin',
        'round_id': fmt_round(V(top, 20)),
        'balance': F(top, 6),
        'total_win': F(top, 3) or 0.0,
        'base_bet': base,
        'ante': ante,
        'paid_bet': round(base * mult_pay, 4) if isinstance(base, float) else None,
        'multiplier': F(info, 12),
        'win_lines': V(info, 7) or 0,
        'board': B(M(info, 2), 1),   # f2.f1 盤面符號窗
        'reels': [r for r in reels if r],
        'paylines': [p for p in paylines if p['line'] is not None],
    }
    return out


def pretty_config(raw):
    top = parse(raw); f1 = M(top, 1)
    cur = _last(f1, 3)
    return {
        'type': 1, 'kind': 'config',
        'currency': cur.decode('utf-8', 'replace') if isinstance(cur, (bytes, bytearray)) else None,
        'balance': F(f1, 4),
        'bet_menu': unpack_f64_array(_last(f1, 5)),
        'limits': {'min': F(f1, 6), 'step': F(f1, 7), 'max': F(f1, 8)},
    }


def pretty_balance(raw):
    f1 = M(parse(raw), 1)
    return {'type': 2, 'kind': 'balance', 'balance': F(f1, 2)}


def pretty_session(raw):
    f1 = M(parse(raw), 1)
    return {'type': 58, 'kind': 'session',
            'round_id': fmt_round(V(f1, 3)), 'base_bet': F(f1, 4)}


def prettify(row):
    t, raw = row.get('type'), row.get('raw') or []
    try:
        if t == 0:  d = pretty_spin(raw)
        elif t == 1: d = pretty_config(raw)
        elif t == 2: d = pretty_balance(raw)
        elif t == 58: d = pretty_session(raw)
        else:
            d = {'type': t, 'kind': row.get('kind', '?'), 'note': '(ack/empty or 未映射)',
                 'data_len': row.get('len', 0)}
    except Exception as e:
        d = {'type': t, 'kind': row.get('kind', '?'), 'error': f'{e!r}'}
    d['idx'] = row.get('idx')
    d['ret'] = row.get('ret', 0)
    return d


def write_spin_pair(pretty, raw, spins_dir, spins_raw_dir):
    """每把 spin 落兩個檔(live / 批次共用,確保一致):
       spins_dir/<局號>.json      純分析(無 raw,給機率團隊反覆研究)
       spins_raw_dir/<局號>.json  含 raw(供 server REPLAY_SPINS 回放):{round_id,idx,type,ret,raw}
    只有 kind=='spin' 且有 round_id 才寫。回傳寫出的檔路徑 list(有寫=非空,可當 truthy;供呼叫端 chown)。"""
    if pretty.get('kind') != 'spin':
        return []
    rid = str(pretty.get('round_id') or '').strip()
    if not rid:
        return []
    safe = rid.replace('/', '_').replace('\\', '_').replace(':', '_')
    written = []
    clean = {k: v for k, v in pretty.items() if k != 'raw'}   # 分析檔:去掉 raw 保持乾淨
    os.makedirs(spins_dir, exist_ok=True)
    _p = os.path.join(spins_dir, safe + '.json')
    with open(_p, 'w', encoding='utf-8') as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
    written.append(_p)
    if raw is not None:
        os.makedirs(spins_raw_dir, exist_ok=True)
        rec = {'round_id': pretty.get('round_id'), 'idx': pretty.get('idx'),
               'type': pretty.get('type', 0), 'ret': pretty.get('ret', 0), 'raw': list(raw)}
        _p2 = os.path.join(spins_raw_dir, safe + '.json')
        with open(_p2, 'w', encoding='utf-8') as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        written.append(_p2)
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('gid', nargs='?', default='696')
    ap.add_argument('--in', dest='inp')
    ap.add_argument('--out', dest='out')
    a = ap.parse_args()
    inp = a.inp or f'games/{a.gid}/webcap/exchanges_ordered.jsonl'
    out = a.out or f'games/{a.gid}/webcap/pretty.jsonl'
    if not os.path.exists(inp):
        sys.exit(f'✗ 找不到 {inp} — 先跑 ./webcapture_finish.sh {a.gid}')
    rows = [json.loads(l) for l in open(inp) if l.strip()]
    pretty = [prettify(r) for r in rows]
    with open(out, 'w') as f:
        for d in pretty:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')
    spins = [d for d in pretty if d.get('type') == 0]
    print(f'[wrote] {out} ({len(pretty)} 筆,其中 spin {len(spins)} 局)')

    # 一 spin 兩個檔:spins/(純分析,無 raw) + spins_raw/(含 raw,供回放)。檔名=局號(單調遞增=順序)。
    base = os.path.dirname(out) or '.'
    spindir = os.path.join(base, 'spins')
    spinrawdir = os.path.join(base, 'spins_raw')
    nw = 0
    for r, d in zip(rows, pretty):
        if write_spin_pair(d, r.get('raw'), spindir, spinrawdir):
            nw += 1
    print(f'[wrote] {spindir}/*.json + {spinrawdir}/*.json '
          f'({nw} 局;spins=純分析, spins_raw=含raw供回放)')
    if spins:
        print('\n  局號        底注   額外   實付   倍率   中獎線  總中獎     餘額')
        print('  ' + '-' * 74)
        for s in spins[:40]:
            print('  {rid:<11} {bb:<6} {an:<5} {pb:<6} {mx:<6} {wl:<6} {tw:<10} {bal}'.format(
                rid=str(s.get('round_id'))[:11], bb=s.get('base_bet'),
                an=s.get('ante') or '-', pb=s.get('paid_bet'),
                mx=s.get('multiplier'), wl=s.get('win_lines'),
                tw=round(s.get('total_win') or 0, 4), bal=s.get('balance')))
        if len(spins) > 40:
            print(f'  … 還有 {len(spins)-40} 局(全部在 {out})')


if __name__ == '__main__':
    main()
