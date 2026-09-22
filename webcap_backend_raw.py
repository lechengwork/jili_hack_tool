#!/usr/bin/env python3
"""webcap_backend_raw.py — 匯出「後端原始、還沒被動過的那一包」。

背景(給機率團隊):
  spins/*.json 與 pretty.jsonl 是 webcap_pretty.py 事後「貼語意標籤」的可讀視圖——
  它會【改名】(window→board、reels→reels…)、【丟欄位】(nudge_pos/rtp_const/post_nudge/
  外層時間戳…)、甚至【自己算出封包裡沒有的欄位】(paid_bet = base×ante、total_win 補 0)。
  那是「我們的解讀」,不是後端送來的協定封包,所以跟你在記憶體裡看到的形狀對不上。

  這支工具只做解密,不做任何改名/推導,輸出後端【原封不動】的三層:
    response_wire_hex  = 線上實際那串 bytes(加密:sig64‖nonce12‖ct+tag)。真正 raw,但沒有 key 看不懂。
    plaintext_hex      = AES 解密後的【完整 Envelope】(f3=type f5=data f6=err f7=ret,外加 f1=server 時間戳)。
                         這就是後端產生、原封不動的那一包(只做了不可避免的解密)。
    payload_hex        = Envelope.f5 = 遊戲負載本體(spin=SpinResult,對應 games/<gid>/fg5_696.proto)。
                         ★這一層就是重播單位★:server.py make_response(data=payload) 會自己補回外層+重新加密。
    payload_decoded    = payload 的忠實 protobuf 傾印(只有 field 編號+wire,零改名零推導),供你比對 proto。

用法:
  ./.venv/bin/python webcap_backend_raw.py 696                      # key 自動找 /tmp/jili_grab.json 或 webcap_grv.jsonl
  ./.venv/bin/python webcap_backend_raw.py 696 --grab /tmp/jili_grab.json
  ./.venv/bin/python webcap_backend_raw.py 696 --grv games/696/webcap_grv.jsonl
  ./.venv/bin/python webcap_backend_raw.py 696 --key <64hex>        # 直接給 AES-256 key

輸出(games/<gid>/webcap/backend_raw/):
  backend_raw.jsonl                 全部回應各一筆(依 seq/idx),含上面三層 hex + payload_decoded
  spins/<round_id>.json             ★每局一個,只含 spin(type0);機率團隊主要看這批★
  README.txt                        這段說明的精簡版
"""
import os, sys, json, struct, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'routex'))
import fg5
import decrypt_capture as dc
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature


def resolve_key(exch, args):
    """回傳 (aes_key_bytes, how_str)。優先 --key / --grab.key,再 X25519(priv or grv)。"""
    # client ephemeral pub (f4) — 一場一把
    pubs = set()
    for e in exch:
        f4 = fg5.parse_fields(bytes.fromhex(e['req_body_hex'])).get(4, b'')
        if isinstance(f4, (bytes, bytearray)):
            pubs.add(bytes(f4))
    client_pub = next(iter(pubs)) if pubs else None

    key_hex, priv_hex = args.key, args.priv
    if args.grab and os.path.exists(args.grab):
        g = json.load(open(args.grab))
        key_hex = key_hex or g.get('key')
        priv_hex = priv_hex or g.get('priv')
    if key_hex:
        return bytes.fromhex(key_hex), f'--key/grab 直接給的 AES key'
    if priv_hex:
        priv = bytes.fromhex(priv_hex)
        if client_pub and dc.x_pub_of(priv) != client_pub:
            sys.exit('[FATAL] --priv 與這場 capture 的 client_pub 不符')
        return dc.shared_key(priv), 'X25519(--priv, server_pub)'
    if args.grv and os.path.exists(args.grv):
        cands = dc.load_grv_outputs(args.grv)
        priv = dc.find_priv(cands, client_pub)
        if not priv:
            sys.exit(f'[FATAL] {args.grv} 裡沒有能推出 client_pub 的私鑰候選')
        return dc.shared_key(priv), f'X25519(從 {os.path.basename(args.grv)} 反查的 priv, server_pub)'
    sys.exit('[FATAL] 找不到 key:請給 --key / --grab / --priv / --grv 其一')


# ── fg5_696.proto 欄位對照(逆向;部分欄位 proto 內標「待確認」) ──────────────
_SCHEMA = {
  'SpinResult': {1:('board','msg:BoardDetail'),2:('reserved_f2','bytes'),3:('total_win','double'),
                 6:('balance','double'),20:('round_id','varint'),23:('bet','msg:BetInfo')},
  'BoardDetail': {1:('reels','msg:Reel','R'),2:('window','msg:SymbolWindow'),3:('unknown_f3','varint'),
                  5:('unknown_f5','varint'),6:('line_wins','msg:LineWin','R'),7:('win_line_cnt','varint'),
                  8:('nudge_pos','symbols'),12:('multiplier','double'),13:('total_win','double'),
                  15:('rtp_const','double'),18:('ante_level','varint'),19:('post_nudge','msg:PostNudgeState','R')},
  'Reel': {1:('symbols','symbols')},
  'SymbolWindow': {1:('symbols','symbols')},
  'LineWin': {1:('symbol_id','varint'),2:('match_count','varint'),3:('payline_index','varint'),4:('win_cash','double')},
  'PostNudgeState': {1:('a','symbols'),2:('b','bytes')},
  'BetInfo': {1:('base_bet','double'),25:('reserved_f25','bytes'),26:('ante','msg:Ante')},
  'Ante': {1:('level','varint')},
  'GameConfig': {1:('core','msg:ConfigCore'),5:('extra','msg:ConfigExtra'),13:('max_pay','double'),
                 14:('reserved_f14','string'),15:('no_limit','varint')},
  'ConfigCore': {1:('flag_f1','varint'),2:('cur_code','string'),3:('cur_symbol','string'),4:('balance','double'),
                 5:('bet_menu','packed_double'),6:('limit_f6','double'),7:('step_f7','double'),
                 8:('limit_f8','double'),12:('flag_f12','varint')},
  'ConfigExtra': {2:('packed_doubles_f2','packed_double')},
  'BalanceUpdate': {1:('body','msg:BalanceBody')},
  'BalanceBody': {1:('kind','varint'),2:('balance','double'),5:('flag_f5','varint')},
  'SessionInfo': {1:('body','msg:SessionBody'),2:('flag_f2','varint')},
  'SessionBody': {1:('txn_id','varint'),2:('id_frag','string'),3:('round_id','varint'),4:('bet','double'),
                  5:('range_f5','double'),6:('limit_f6','double'),7:('flag_f7','varint'),8:('ts','msg:Timestamp')},
  'Timestamp': {1:('unix_sec','varint'),2:('sub','varint')},
  'SmallState': {3:('flag_f3','varint')},
}
_TYPE_ROOT = {0:'SpinResult', 1:'GameConfig', 2:'BalanceUpdate', 58:'SessionInfo', 19:'SmallState'}


def _iter_fields(buf):
    """(field, wire, rawvalue) 逐一,保留順序與重複。"""
    i, n, out = 0, len(buf), []
    try:
        while i < n:
            key, i = fg5.dec_varint(buf, i); f, w = key >> 3, key & 7
            if   w == 0: v, i = fg5.dec_varint(buf, i)
            elif w == 2: ln, i = fg5.dec_varint(buf, i); v = bytes(buf[i:i+ln]); i += ln
            elif w == 1: v = bytes(buf[i:i+8]); i += 8
            elif w == 5: v = bytes(buf[i:i+4]); i += 4
            else: break
            out.append((f, w, v))
    except Exception:
        pass
    return out


def _dbl(v):
    if isinstance(v, (bytes, bytearray)) and len(v) == 8: return struct.unpack('<d', v)[0]
    return v if isinstance(v, int) else None

def _vint(v):
    return v if isinstance(v, int) else int.from_bytes(v, 'little')

def _str(v):
    if isinstance(v, (bytes, bytearray)):
        try:
            s = v.decode('utf-8')
            if all((31 < ord(c) < 127) or ord(c) > 127 for c in s): return s
        except Exception:
            pass
        return list(v)
    return v

def _packed_dbl(v):
    if isinstance(v, (bytes, bytearray)) and len(v) % 8 == 0:
        return [struct.unpack('<d', v[j:j+8])[0] for j in range(0, len(v), 8)]
    return list(v) if isinstance(v, (bytes, bytearray)) else v


def decode_named(buf, msgname):
    """套 fg5_696.proto 名字的可讀解讀(★我們逆向的解讀,非封包原生;ground truth 仍是 payload_hex)。
    未知欄位保留 f<N> 不隱藏。"""
    sch = _SCHEMA.get(msgname, {})
    out = {'_message': msgname}
    grouped = {}
    for f, w, v in _iter_fields(bytes(buf)):
        grouped.setdefault(f, []).append((w, v))
    for f, items in grouped.items():
        spec = sch.get(f)
        if not spec:
            vals = []
            for w, v in items:
                if   w == 1: vals.append(struct.unpack('<d', v)[0] if len(v) == 8 else list(v))
                elif w == 2: vals.append(list(v))
                else:        vals.append(v)
            out['f%d' % f] = vals if len(vals) > 1 else vals[0]
            continue
        name, kind = spec[0], spec[1]
        rep = len(spec) > 2 and spec[2] == 'R'
        dec = []
        for w, v in items:
            if   kind.startswith('msg:'):    dec.append(decode_named(v, kind[4:]))
            elif kind == 'double':           dec.append(_dbl(v))
            elif kind == 'varint':           dec.append(_vint(v))
            elif kind == 'string':           dec.append(_str(v))
            elif kind in ('symbols', 'bytes'): dec.append(list(v) if isinstance(v, (bytes, bytearray)) else v)
            elif kind == 'packed_double':    dec.append(_packed_dbl(v))
            else:                            dec.append(list(v) if isinstance(v, (bytes, bytearray)) else v)
        out[name] = dec if rep else dec[-1]
    return out


def split_envelope(pt):
    """完整明文 → (envelope_fields dict, payload_bytes, type, ret, err, time)。不改名。"""
    f = fg5.parse_fields(pt)
    def as_int(x, d=0): return x if isinstance(x, int) else (int.from_bytes(x, 'little') if isinstance(x, (bytes, bytearray)) else d)
    typ = as_int(f.get(fg5.Fg5Crypto.F_TYPE, 0))
    ret = as_int(f.get(fg5.Fg5Crypto.F_RET, 0))
    err = f.get(fg5.Fg5Crypto.F_ERRMSG, b'')
    tim = as_int(f.get(fg5.Fg5Crypto.F_TIME, 0))
    data = f.get(fg5.Fg5Crypto.F_DATA, b'')
    payload = bytes(data) if isinstance(data, (bytes, bytearray)) else b''
    env = {}
    for k, v in sorted(f.items()):
        env[k] = v.hex() if isinstance(v, (bytes, bytearray)) else v
    return env, payload, typ, ret, (err.decode('utf-8', 'replace') if isinstance(err, (bytes, bytearray)) else ''), tim


def fmt_round(n):
    s = str(n)
    return f'{s[:5]}-{s[5:11]}-{s[11:]}' if isinstance(n, int) and len(s) == 19 else (s if n else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('gid', nargs='?', default='696')
    ap.add_argument('--exchanges'); ap.add_argument('--out')
    ap.add_argument('--key'); ap.add_argument('--priv')
    ap.add_argument('--grab', default='/tmp/jili_grab.json')
    ap.add_argument('--grv')
    a = ap.parse_args()

    exch_path = a.exchanges or f'games/{a.gid}/webcap/fg5_exchanges.json'
    if not os.path.exists(exch_path):
        sys.exit(f'✗ 找不到 {exch_path}(先跑 webcapture.sh + webcapture_finish.sh)')
    if a.grv is None:
        g = f'games/{a.gid}/webcap_grv.jsonl'
        a.grv = g if os.path.exists(g) else None
    exch = json.load(open(exch_path))
    exch.sort(key=lambda e: e.get('seq') or 0)

    key, how = resolve_key(exch, a)
    print(f'[key] {how}\n      AES-256 = {key.hex()}')

    outdir = a.out or f'games/{a.gid}/webcap/backend_raw'
    spindir = os.path.join(outdir, 'spins')

    rows, spin_recs, nspin, sig_all = [], [], 0, True
    for i, e in enumerate(exch):
        wire = bytes.fromhex(e['resp_body_hex'])
        if len(wire) < 76:
            continue
        sig, nonce, ct = wire[:64], wire[64:76], wire[76:]
        try:
            pt = AESGCM(key).decrypt(nonce, ct, b'')
        except Exception as ex:
            print(f'  ex{i:2} 解密失敗 {ex!r}'); sig_all = False; continue
        sig_ok = None
        try:
            ed25519.Ed25519PublicKey.from_public_bytes(dc.SERVER_ED25519_PUB).verify(sig, nonce + ct)
            sig_ok = True
        except InvalidSignature:
            sig_ok = False; sig_all = False
        env, payload, typ, ret, err, tim = split_envelope(pt)
        rid = None
        if typ == 0 and payload:
            top = fg5.parse_fields(payload)
            v20 = top.get(20)
            if isinstance(v20, int):
                rid = fmt_round(v20)
        rec = {
            'idx': i, 'seq': e.get('seq'), 'type': typ, 'ret': ret,
            'round_id': rid, 'sig_ok': sig_ok, 'server_time': tim,
            'response_wire_hex': wire.hex(),          # 線上加密原文(真 raw)
            'plaintext_hex': pt.hex(),                # 完整 Envelope 明文(後端原封不動那一包)
            'payload_hex': payload.hex(),             # f5 = SpinResult(重播單位)
            'envelope_fields': env,                   # {f#: 值},忠實
            'payload_decoded': dc.decode_pb(payload), # SpinResult 忠實 protobuf 傾印(零改名)
            'payload_named': (decode_named(payload, _TYPE_ROOT[typ])
                              if (typ in _TYPE_ROOT and payload) else None),  # ★套 proto 名字(逆向解讀)
        }
        rows.append(rec)
        if typ == 0 and rid:
            nspin += 1
            spin_recs.append((rid.replace('/', '_'), rec))

    # 安全鎖:一筆都沒解出(通常=/tmp/jili_grab.json 的 key 是別次 capture 的)→ 不寫、不覆蓋既有輸出
    if not rows:
        sys.exit(f'[FATAL] 0 筆解密成功 — key 對不上這份 capture'
                 f'(多半是 /tmp/jili_grab.json 為別次擷取的 key)。未寫入任何檔,既有 backend_raw/ 保留。\n'
                 f'  改用這份自己的 key:  webcap_backend_raw.py {a.gid} '
                 f'--grv games/{a.gid}/webcap_grv.jsonl   (或 --key <64hex>)')

    os.makedirs(spindir, exist_ok=True)
    for safe, rec in spin_recs:
        with open(os.path.join(spindir, safe + '.json'), 'w', encoding='utf-8') as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)

    with open(os.path.join(outdir, 'backend_raw.jsonl'), 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    with open(os.path.join(outdir, 'README.txt'), 'w', encoding='utf-8') as f:
        f.write(
            '這批是後端原封不動的封包(只做了不可避免的 AES 解密),沒有任何改名/推導。\n'
            '每筆三層:\n'
            '  response_wire_hex = 線上實際 bytes(加密:sig64‖nonce12‖ct+tag)\n'
            '  plaintext_hex     = 解密後完整 Envelope(f3=type f5=data f6=err f7=ret,+f1=server時間戳)\n'
            '  payload_hex       = Envelope.f5 = 遊戲負載(spin=SpinResult),對應 fg5_696.proto\n'
            '                      ★這一層就是重播單位:server.py make_response(data=payload) 會自己補外層+重新加密\n'
            '  payload_decoded   = payload 的忠實 protobuf 傾印(field 編號+wire,零改名零推導)\n'
            '  payload_named     = 套 fg5_696.proto 名字的可讀解讀(★我們逆向的解讀,非封包原生;\n'
            '                      未知欄位保留 f<N>;proto 部分欄位標「待確認」;ground truth 仍是 payload_hex)\n'
            '\n'
            '對照:spins/*.json、pretty.jsonl 是 webcap_pretty.py 的「可讀視圖」——會改名/丟欄位/自算欄位,\n'
            '     機率/RTP 請以本目錄的 payload_hex + payload_decoded + fg5_696.proto 為準。\n')

    print(f'[wrote] {outdir}/backend_raw.jsonl  ({len(rows)} 筆回應)')
    print(f'[wrote] {spindir}/*.json           ({nspin} 局 spin)')
    print(f'[wrote] {outdir}/README.txt')
    print(f'[check] 全部 Ed25519 簽章有效: {sig_all}')


if __name__ == '__main__':
    main()
