#!/usr/bin/env python3
"""math_adapter.py — 機率格式 ⇄ 線路格式,雙向 byte 級可逆。

    前端 spin
      → 我們解密,取出 SpinResult payload
      → wire_to_math()  → 機率格式(math_696.proto,全 int,沒有 bytes)
      → 機率算完吐回來
      → math_to_wire()  → 原本的 fg5_696.proto wire bytes
      → 加密 → 回前端

★這層只存在於交給機率的擷取包裡,正式跑的遊戲不需要。★

為什麼要這層:線路那份 proto 有 bytes 打包的符號陣列、兩個恆空的 reserved、
proto3 的零值省略規則、還有額外下注同時寫在兩個地方(BetInfo.ante 的「有沒有出現」
+ BoardDetail.ante_level 的「值 +1」)。那些是傳輸層的包裝,機率不該背。

驗證:games/696 的 58 局真實封包 wire → math → wire,58/58 byte 完全相同
      (跑 `python math_adapter.py --selftest`)。
"""
import os, sys, json, struct

# ★零相依★ 只用標準庫 —— 機率不必裝任何套件就能跑 --selftest。
# (以下三個 varint helper 與 routex/fg5.py 同實作,刻意內聯以免拉進 cryptography。)


def _enc_varint(n):
    out = bytearray()
    n &= (1 << 64) - 1
    while True:
        b = n & 0x7f
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _enc_tag(field, wire):
    return _enc_varint((field << 3) | wire)


def _dec_varint(buf, i):
    shift = result = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80):
            return result, i
        shift += 7

ANTE_NAMES = {0: 'ANTE_NONE', 1: 'ANTE_1_5X', 2: 'ANTE_8X'}
ANTE_VALS  = {v: k for k, v in ANTE_NAMES.items()}
ANTE_COST  = {0: 1.0, 1: 1.5, 2: 8.0}      # 實扣 = base_bet × 這個倍率(58 局餘額 Δ 實證)
PAYLINES   = 5


# ── 低階 protobuf ────────────────────────────────────────────────────────────
def _fields(buf):
    """[(field, wire, raw)] 保留順序與重複。"""
    i, n, out = 0, len(buf), []
    while i < n:
        key, i = _dec_varint(buf, i)
        f, w = key >> 3, key & 7
        if   w == 0: v, i = _dec_varint(buf, i)
        elif w == 2: ln, i = _dec_varint(buf, i); v = bytes(buf[i:i+ln]); i += ln
        elif w == 1: v = bytes(buf[i:i+8]); i += 8
        elif w == 5: v = bytes(buf[i:i+4]); i += 4
        else: raise ValueError(f'不支援的 wire type {w} @f{f}')
        out.append((f, w, v))
    return out


def _one(fs, f):
    for ff, w, v in fs:
        if ff == f:
            return v
    return None


def _all(fs, f):
    return [v for ff, w, v in fs if ff == f]


def _dbl(v):   return struct.unpack('<d', v)[0] if isinstance(v, bytes) and len(v) == 8 else 0.0
def _int(v):   return v if isinstance(v, int) else int.from_bytes(v, 'little')
def _syms(v):
    """符號/次數陣列是【packed varint】,不是原始 bytes。
    符號 id 都 <128 所以兩者長得一樣,但 Ex Nudge 的次數可到 200/500,
    當成 raw bytes 會變成兩格(244,3)而且值是錯的。"""
    if not isinstance(v, (bytes, bytearray)):
        return []
    out, i, n = [], 0, len(v)
    while i < n:
        x, i = _dec_varint(bytes(v), i)
        out.append(x)
    return out


def _enc_syms(lst):
    out = b''
    for x in (lst or []):
        out += _enc_varint(int(x))
    return out

def _e_var(f, v):  return _enc_tag(f, 0) + _enc_varint(v)
def _e_bytes(f, b): return _enc_tag(f, 2) + _enc_varint(len(b)) + bytes(b)
def _e_dbl(f, d):  return _enc_tag(f, 1) + struct.pack('<d', d)


# ── wire → 機率格式 ──────────────────────────────────────────────────────────
def wire_to_math(payload):
    """SpinResult payload bytes → math_696.proto 的 JSON 形狀。"""
    sr = _fields(bytes(payload))
    bd = _fields(_one(sr, 1) or b'')

    # 額外下注:線路寫在兩處,這裡收斂成一個 enum(以 board.ante_level 為準,它就是 enum 值)
    ante = _int(_one(bd, 18)) if _one(bd, 18) is not None else 0

    board = {
        'reels':        [{'symbols': _syms(_one(_fields(r), 1))} for r in _all(bd, 1)],
        'window':       _syms(_one(_fields(_one(bd, 2) or b''), 1)),
        'line_wins':    [_lw_to_math(w) for w in _all(bd, 6)],
        'win_type':     _int(_one(bd, 7)) if _one(bd, 7) is not None else 0,
        'multiplier':   _dbl(_one(bd, 12)),
        'rtp_const':    _dbl(_one(bd, 15)),
        'window_extra':  _int(_one(bd, 3)) if _one(bd, 3) is not None else 0,
        'window_extra2': _int(_one(bd, 4)) if _one(bd, 4) is not None else 0,
        'nudge_group':  _int(_one(bd, 5)) if _one(bd, 5) is not None else 0,
        'nudge_pos':    _syms(_one(bd, 8)),
        'gift_pool': _syms(_one(bd, 9)),        # 饋贈①(index0)挑中的 3~5 個倍率符號
        'boost_symbols': _syms(_one(bd, 10)),   # 饋贈③(index2)升級的候選倍率符號
        'respin_prev': _syms(_one(bd, 11)),     # 饋贈④(index4)被重轉那一軸【重轉前】的 3 個符號
        'post_nudge':   [{'cells': _syms(_one(_fields(p), 1))} for p in _all(bd, 19)],
    }
    bet = _fields(_one(sr, 23) or b'')
    return {
        'board':     board,
        'total_win': _dbl(_one(sr, 3)) if _one(sr, 3) is not None else 0.0,
        'balance':   _dbl(_one(sr, 6)),
        'round_id':  str(_int(_one(sr, 20))) if _one(sr, 20) is not None else '',
        'base_bet':  _dbl(_one(bet, 1)),
        'ante':      ANTE_NAMES.get(ante, 'ANTE_NONE'),
    }


def _lw_to_math(raw):
    f = _fields(raw)
    return {
        'symbol_id':     _int(_one(f, 1)) if _one(f, 1) is not None else 0,
        'match_count':   _int(_one(f, 2)) if _one(f, 2) is not None else 0,
        'payline_index': _int(_one(f, 3)) if _one(f, 3) is not None else 0,
        'win_cash':      _dbl(_one(f, 4)),
    }


# ── 機率格式 → wire ──────────────────────────────────────────────────────────
def math_to_wire(m):
    """math_696.proto 的 JSON 形狀 → SpinResult payload bytes。

    這裡負責所有「傳輸層包裝」:proto3 零值省略、恆空的 reserved 欄位、
    符號陣列打包成 bytes、額外下注拆回 BetInfo.ante + BoardDetail.ante_level。
    """
    b = m.get('board') or {}
    ante = m.get('ante', 'ANTE_NONE')
    ante = ANTE_VALS.get(ante, ante) if isinstance(ante, str) else int(ante)

    # ── BoardDetail(欄位號升冪;proto3 零值省略) ──
    out = b''
    for r in b.get('reels') or []:
        out += _e_bytes(1, _e_bytes(1, _enc_syms(r.get('symbols'))))
    out += _e_bytes(2, _e_bytes(1, _enc_syms(b.get('window'))))
    if b.get('window_extra'):
        out += _e_var(3, int(b['window_extra']))
    if b.get('window_extra2'):
        out += _e_var(4, int(b['window_extra2']))   # 連鎖第二段的抓取次數
    if b.get('nudge_group'):
        out += _e_var(5, int(b['nudge_group']))
    for w in b.get('line_wins') or []:
        lw = b''
        if w.get('symbol_id'):     lw += _e_var(1, int(w['symbol_id']))
        if w.get('match_count'):   lw += _e_var(2, int(w['match_count']))
        if w.get('payline_index'): lw += _e_var(3, int(w['payline_index']))
        if w.get('win_cash'):      lw += _e_dbl(4, float(w['win_cash']))
        out += _e_bytes(6, lw)
    # win_type(447/447 局實證):0=沒中、1=一般中獎、3=Ex Nudge 局中獎。
    # 不是線數也不是符號種類數(有局 5 條線是 1、有局 3 條線是 3)。
    # 機率沒填就自動推,填了就照填的走。
    wt = b.get('win_type')
    if wt is None:
        won = bool(b.get('line_wins') or [])
        nud = len(b.get('window') or []) > 5
        wt = (3 if nud else 1) if won else 0
    if wt:
        out += _e_var(7, int(wt))
    out += _e_bytes(8, _enc_syms(b.get('nudge_pos')))
    if b.get('gift_pool'):
        out += _e_bytes(9, _enc_syms(b['gift_pool']))        # 饋贈①(index0)挑中的符號池
    if b.get('boost_symbols'):
        out += _e_bytes(10, _enc_syms(b['boost_symbols']))   # 饋贈③(index2)升級候選
    if b.get('respin_prev'):
        out += _e_bytes(11, _enc_syms(b['respin_prev']))     # 饋贈④(index4)重轉前的那一軸
        # ★少了這欄前端會卡死在動畫階段(2026-09-21 實證)★
    out += _e_dbl(12, float(b.get('multiplier') or 0.0))
    tw = float(m.get('total_win') or 0.0)
    if tw:
        out += _e_dbl(13, tw)                       # board.total_win 與頂層同值
    out += _e_dbl(15, float(b.get('rtp_const') or 0.0))
    if ante:
        out += _e_var(18, ante)                     # ★線路的 ante_level 就是 enum 值★
    for p in b.get('post_nudge') or []:
        out += _e_bytes(19, _e_bytes(1, _enc_syms(p.get('cells'))))
    board = out

    # ── BetInfo ──
    bet = _e_dbl(1, float(m.get('base_bet') or 0.0))
    bet += _e_bytes(25, b'')                        # reserved,58/58 局恆空但固定出現
    if ante:
        inner = _e_var(1, ante - 1) if ante - 1 else b''   # ANTE_1_5X→{} / ANTE_8X→{level:1}
        bet += _e_bytes(26, inner)

    # ── SpinResult ──
    sr = _e_bytes(1, board)
    sr += _e_bytes(2, b'')                          # reserved,同上
    if tw:
        sr += _e_dbl(3, tw)
    sr += _e_dbl(6, float(m.get('balance') or 0.0))
    rid = str(m.get('round_id') or '')
    if rid:
        sr += _e_var(20, int(rid))
    sr += _e_bytes(23, bet)
    return sr


# ── 便利函式 ─────────────────────────────────────────────────────────────────
def paid_bet(m):
    """實扣金額。★封包裡沒有這個欄位,算 RTP 必須自己乘。★"""
    ante = m.get('ante', 'ANTE_NONE')
    ante = ANTE_VALS.get(ante, 0) if isinstance(ante, str) else int(ante)
    return float(m.get('base_bet') or 0.0) * ANTE_COST[ante]


def _selftest_payloads(root, gid):
    """測試向量優先(隨包附,離線可驗);沒有就從手邊的 capture 撈。"""
    vec = os.path.join(root, 'games', gid, 'math', 'roundtrip_vectors.jsonl')
    if os.path.exists(vec):
        for line in open(vec, encoding='utf-8'):
            line = line.strip()
            if line:
                yield bytes.fromhex(json.loads(line)['payload_hex'])
        return
    for src in [os.path.join(root, 'games', gid, 'exchanges_ordered.jsonl'),
                os.path.join(root, 'games', gid, 'webcap', 'exchanges_ordered.jsonl')]:
        if not os.path.exists(src):
            continue
        for line in open(src, encoding='utf-8'):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get('kind') == 'spin' and r.get('type') == 0 and r.get('raw'):
                yield bytes(r['raw'])


def selftest(gid='696'):
    """拿真實封包做 wire → math → wire,比對 byte 是否完全相同。"""
    root = os.path.dirname(os.path.abspath(__file__))
    ok = bad = 0
    if True:
        for wire in _selftest_payloads(root, gid):
            back = math_to_wire(wire_to_math(wire))
            if back == wire:
                ok += 1
            else:
                bad += 1
                print(f'  ✗ 第 {ok+bad} 局 原 {len(wire)}B / 還原 {len(back)}B')
                print(f'    原   {wire.hex()}')
                print(f'    還原 {back.hex()}')
    if ok + bad == 0:
        print('✗ selftest 找不到任何測試向量(games/%s/math/roundtrip_vectors.jsonl)— 不算通過' % gid)
        return False
    print(f'round-trip:{ok} 局 byte 完全相同 / {bad} 局不符')
    return bad == 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)
