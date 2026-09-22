#!/usr/bin/env python3
"""Offline decryptor for a real /fg5/req capture — closes the config data gap.

WHY: the mock replies to the handshake with a fake empty {type:0}, so the game
times out at init (MSG 999.2). The REAL handshake/config response is a ~235-byte
payload we never had decrypted. We CANNOT derive it from the stored capture alone,
because the response AES key = X25519(client_ephemeral_priv, server_x25519_pub) and
the ephemeral PRIVATE key was never logged (X25519 pub->priv is infeasible).

FIX (one real capture): during the next live session, log every getRandomValues
OUTPUT (hook.js / jili_hook_ext already do: `out: hex(r)`) AND save the /fg5/req
request+response bodies (as games/696/fg5_exchanges.json already are). Then run this
script: it finds the ephemeral priv whose X25519 pubkey matches the request's f4,
derives the shared key with the KNOWN real server pub, and AES-256-GCM-decrypts EVERY
response — config, all init replies, balance, spins — writing responses.jsonl. No new
crypto, no heap-timing luck; one capture yields the whole session, permanently.

Usage:
  ./decrypt_capture.py --selftest         # prove the crypto chain (no capture needed)
  ./decrypt_capture.py --exchanges games/696/fg5_exchanges.json --grv hooklog.jsonl
  ./decrypt_capture.py --exchanges <capture.json> --priv <64hex>   # if priv known directly
  (writes games/696/responses.jsonl by default; --out to override)
"""
import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fg5
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

# Real server pubs, XOR-0xAA-deobfuscated from crypto.wasm consts (PROTOCOL_SOLVED.md).
SERVER_X25519_PUB = bytes.fromhex('26aa760e99da9a40f3ab907f0d7b07e17b36e6a199e8400abde61af01a08da17')
SERVER_ED25519_PUB = bytes.fromhex('81c785c85653e6a1e92c9359646e23f662f5615975ae7faa6a5721358018ff8c')


def x_pub_of(priv32):
    """X25519 public key (raw 32B) for a raw 32-byte private scalar (lib clamps)."""
    return (x25519.X25519PrivateKey.from_private_bytes(priv32)
            .public_key().public_bytes(serialization.Encoding.Raw,
                                        serialization.PublicFormat.Raw))


def shared_key(priv32, server_pub=SERVER_X25519_PUB):
    return (x25519.X25519PrivateKey.from_private_bytes(priv32)
            .exchange(x25519.X25519PublicKey.from_public_bytes(server_pub)))


def parse_plaintext(pt):
    """Outer wrapper -> dict. f3=type, f5=data(bytes), f6=error_msg, f7=ret."""
    f = fg5.parse_fields(pt)
    typ = f.get(fg5.Fg5Crypto.F_TYPE, 0)
    data = f.get(fg5.Fg5Crypto.F_DATA, b'')
    ret = f.get(fg5.Fg5Crypto.F_RET, 0)
    err = f.get(fg5.Fg5Crypto.F_ERRMSG, b'')
    tim = f.get(fg5.Fg5Crypto.F_TIME, 0)
    return {
        'type': typ if isinstance(typ, int) else int.from_bytes(typ, 'little'),
        'ret': ret if isinstance(ret, int) else int.from_bytes(ret, 'little'),
        'error_msg': err.decode('utf-8', 'replace') if isinstance(err, (bytes, bytearray)) else '',
        'time': tim if isinstance(tim, int) else int.from_bytes(tim, 'little'),
        'raw': list(data) if isinstance(data, (bytes, bytearray)) else [],
    }


def decode_pb(buf, depth=0):
    """Best-effort recursive protobuf pretty-decode for the 'decoded' field."""
    out = []
    i, n = 0, len(buf)
    try:
        while i < n:
            key, i = fg5.dec_varint(buf, i)
            field, wire = key >> 3, key & 7
            if wire == 0:
                v, i = fg5.dec_varint(buf, i); out.append({'f': field, 'k': 'varint', 'v': v})
            elif wire == 2:
                ln, i = fg5.dec_varint(buf, i); raw = bytes(buf[i:i+ln]); i += ln
                sub = decode_pb(raw, depth+1) if depth < 6 and raw else None
                if sub:
                    out.append({'f': field, 'k': 'msg', 'v': sub})
                else:
                    try:
                        out.append({'f': field, 'k': 'str', 'v': raw.decode('utf-8')})
                    except Exception:
                        out.append({'f': field, 'k': 'bytes', 'v': list(raw)})
            elif wire == 1:
                import struct
                b = bytes(buf[i:i+8]); i += 8
                out.append({'f': field, 'k': 'f64', 'v': struct.unpack('<d', b)[0],
                            'i64': int.from_bytes(b, 'little')})
            elif wire == 5:
                b = bytes(buf[i:i+4]); i += 4
                out.append({'f': field, 'k': 'f32/i32', 'v': int.from_bytes(b, 'little')})
            else:
                break
    except Exception:
        pass
    return out


def decrypt_response(resp, aes_key, verify_sig=True):
    """resp = sig(64) || nonce(12) || ct||tag. Returns parsed dict (+ _sig_ok)."""
    if len(resp) < 76:
        raise ValueError(f'response too short: {len(resp)}')
    sig, nonce, ct = resp[:64], resp[64:76], resp[76:]
    sig_ok = None
    if verify_sig:
        try:
            ed25519.Ed25519PublicKey.from_public_bytes(SERVER_ED25519_PUB).verify(sig, nonce + ct)
            sig_ok = True
        except InvalidSignature:
            sig_ok = False
    pt = AESGCM(aes_key).decrypt(nonce, ct, b'')
    d = parse_plaintext(pt)
    d['pt_hex'] = pt.hex()          # 完整 Envelope 明文 = 後端原封不動那一包(只做了解密)
    d['len'] = len(d['raw'])
    d['decoded'] = decode_pb(bytes(d['raw']))
    d['_sig_ok'] = sig_ok
    return d


def load_grv_outputs(path):
    """Collect candidate 32-byte priv scalars from a getRandomValues log.
    Accepts jsonl/json lines each with an 'out'/'bytes'/'hex' hex field, or a
    json list of hex strings. Any >=32-byte output contributes its first 32 bytes."""
    outs = []
    txt = open(path).read().strip()
    def grab(o):
        if isinstance(o, str):
            h = o
        elif isinstance(o, dict):
            h = o.get('out') or o.get('hex') or o.get('bytes') or ''
        else:
            return
        try:
            b = bytes.fromhex(h)
        except Exception:
            return
        if len(b) >= 32:
            outs.append(b[:32])
    try:
        j = json.loads(txt)
        if isinstance(j, list):
            for o in j: grab(o)
        else:
            grab(j)
    except json.JSONDecodeError:
        for line in txt.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                grab(json.loads(line))
            except Exception:
                grab(line)
    return outs


def find_priv(candidates, client_pub):
    for p in candidates:
        try:
            if x_pub_of(p) == bytes(client_pub):
                return p
        except Exception:
            continue
    return None


def kind_of(af):
    """Label a request by its action fields (mirror of server.py classify), for the replay file."""
    f1 = af.get(1)
    if isinstance(f1, (bytes, bytearray)) and len(f1) == 8:
        return 'spin'
    if not af:
        return 'keepalive'
    if 3 in af and 5 in af:
        return 'handshake'
    if isinstance(f1, (bytes, bytearray)) and 2 in af:
        return 'poll'
    if isinstance(f1, (bytes, bytearray)):
        return 'setlang'
    if isinstance(f1, int):
        return 'status'
    return 'unknown'


def run(exchanges_path, grv_path, priv_hex, out_path, key_hex=None):
    exch = json.load(open(exchanges_path))
    # client_pub (f4) — must be identical across the session (one ephemeral key).
    pubs = set()
    for e in exch:
        rb = bytes.fromhex(e['req_body_hex'])
        f4 = fg5.parse_fields(rb).get(4, b'')
        if isinstance(f4, (bytes, bytearray)):
            pubs.add(bytes(f4))
    if len(pubs) != 1:
        print(f'[warn] {len(pubs)} distinct client_pub in capture — session not single-key; '
              f'this script assumes one ephemeral key.')
    client_pub = next(iter(pubs))
    print(f'[info] client_pub (f4) = {client_pub.hex()}')

    if key_hex:
        # AES key supplied directly (e.g. grabkey.py oracle result) — skip X25519.
        key = bytes.fromhex(key_hex)
        print(f'[ok]   using AES key directly ({len(key)}B): {key.hex()}')
    else:
        if priv_hex:
            priv = bytes.fromhex(priv_hex)
            if x_pub_of(priv) != client_pub:
                sys.exit(f'[FATAL] given --priv does not match the capture client_pub '
                         f'(derived {x_pub_of(priv).hex()})')
            print('[ok]   --priv matches client_pub')
        else:
            if not grv_path:
                sys.exit('[FATAL] need --key, --priv, or --grv (a getRandomValues output log)')
            cands = load_grv_outputs(grv_path)
            print(f'[info] {len(cands)} getRandomValues candidates from {grv_path}')
            priv = find_priv(cands, client_pub)
            if not priv:
                sys.exit('[FATAL] no getRandomValues output derives the capture client_pub — '
                         'the ephemeral priv was not in that log. Re-capture with the hook.')
            print(f'[ok]   recovered ephemeral priv from getRandomValues log')
        key = shared_key(priv)
        print(f'[info] AES key = X25519(priv, server_pub) = {key.hex()}')

    rows, by_type, sig_ok_all = [], {}, True
    for i, e in enumerate(exch):
        resp = bytes.fromhex(e['resp_body_hex'])
        try:
            d = decrypt_response(resp, key)
        except Exception as ex:
            print(f'  ex{i:2} DECRYPT FAIL: {ex!r}  (resplen={len(resp)})')
            sig_ok_all = False
            continue
        by_type.setdefault(d['type'], (i, d['len']))
        req = fg5.parse_fields(bytes.fromhex(e['req_body_hex']))
        af = fg5.parse_fields(req.get(2, b'')) if isinstance(req.get(2), (bytes, bytearray)) else {}
        d['idx'] = i; d['reqlen'] = e.get('req_body_len', 0); d['kind'] = kind_of(af)
        rows.append(d)
        print(f'  ex{i:2} req_af={sorted(af)} -> type={d["type"]:<3} data={d["len"]:<4}B '
              f'ret={d["ret"]} sig_ok={d["_sig_ok"]}')
        if d['_sig_ok'] is False:
            sig_ok_all = False
    print(f'\n[summary] decrypted {len(rows)} responses; distinct types (first seen): '
          f'{ {t: v for t, v in sorted(by_type.items())} }')
    print(f'[summary] all signatures valid: {sig_ok_all}')
    if not rows:
        sys.exit('[FATAL] 0 responses decrypted — wrong key for THIS capture? NOT writing anything, '
                 'so the existing responses.jsonl / exchanges_ordered.jsonl are preserved. '
                 '(Grab the current session key with grabkey.py while the game is OPEN.)')

    # write responses.jsonl: one line per DISTINCT type (first occurrence), matching the
    # existing format {type, ret, len, raw, decoded}. server.py keys SAMPLES by type.
    seen, lines = set(), []
    for d in rows:
        if d['type'] in seen:
            continue
        seen.add(d['type'])
        lines.append(json.dumps({'type': d['type'], 'ret': d['ret'], 'len': d['len'],
                                 'time': d.get('time', 0), 'pt_hex': d.get('pt_hex'),
                                 'raw': d['raw'], 'decoded': d['decoded']}, ensure_ascii=False))
    if out_path:
        open(out_path, 'w').write('\n'.join(lines) + '\n')
        print(f'[wrote] {out_path} ({len(lines)} distinct types: {sorted(seen)})')
        # ALSO write the FULL ORDERED session — server.py replays this (cycles spin boards, switches
        # to the post-spin balance). This is what makes >2 captured spins show up in the mock.
        ordered = os.path.join(os.path.dirname(out_path) or '.', 'exchanges_ordered.jsonl')
        with open(ordered, 'w') as f:
            for d in rows:
                f.write(json.dumps({'idx': d['idx'], 'kind': d['kind'], 'reqlen': d['reqlen'],
                                    'type': d['type'], 'ret': d['ret'], 'len': d['len'],
                                    'time': d.get('time', 0), 'pt_hex': d.get('pt_hex'),
                                    'raw': d['raw'], 'decoded': d['decoded']}, ensure_ascii=False) + '\n')
        nspin = sum(1 for d in rows if d['kind'] == 'spin')
        print(f'[wrote] {ordered} ({len(rows)} exchanges, {nspin} spins) — mock auto-loads this on restart')


def selftest():
    """Prove the ECDH-symmetry + AES-GCM + Ed25519 + parse chain without a real capture:
    play the server side with fg5.Fg5Crypto, then decrypt from the CLIENT side here."""
    print('[selftest] round-trip a response through encrypt(server) -> decrypt(client)')
    # server keypair (stand-in for the real baked keys)
    xs = x25519.X25519PrivateKey.generate()
    xs_pub = xs.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    es = ed25519.Ed25519PrivateKey.generate()
    es_pub = es.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    crypto = fg5.Fg5Crypto(xs.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                            serialization.NoEncryption()).hex(),
                           es.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                            serialization.NoEncryption()).hex())
    # client ephemeral from a fake getRandomValues output
    rand32 = os.urandom(32)
    client_pub = x_pub_of(rand32)
    # server builds a response (like a 235B config: type 9 + some data)
    payload = bytes(range(60)) * 4  # 240 bytes of "config"
    resp = crypto.make_response(client_pub, msg_type=9, data=payload, ret=0)
    # client decrypts with key = X25519(client_priv, server_pub) and REAL-style verify
    global SERVER_X25519_PUB, SERVER_ED25519_PUB
    SERVER_X25519_PUB, SERVER_ED25519_PUB = xs_pub, es_pub  # point verify at our test server
    key = shared_key(rand32, xs_pub)
    d = decrypt_response(resp, key)
    assert d['type'] == 9, d
    assert bytes(d['raw']) == payload, 'payload mismatch'
    assert d['_sig_ok'] is True, 'signature failed'
    # and the priv-finder recovers the priv from a grv-style log
    assert find_priv([os.urandom(32), rand32, os.urandom(32)], client_pub) == rand32
    print(f'[selftest] OK — type={d["type"]} data={d["len"]}B sig_ok={d["_sig_ok"]} '
          f'priv-finder matched. Chain is correct; ready for a real capture.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--exchanges', default='../games/696/fg5_exchanges.json')
    ap.add_argument('--grv', help='getRandomValues output log (jsonl/json, field out/hex/bytes)')
    ap.add_argument('--priv', help='ephemeral X25519 priv (64 hex) if known directly')
    ap.add_argument('--key', help='AES-256 key (64 hex) directly, e.g. grabkey.py oracle result')
    ap.add_argument('--grab', help='a grabkey.py /tmp/jili_grab.json (uses its priv or key)')
    ap.add_argument('--out', default='../games/696/responses.jsonl')
    a = ap.parse_args()
    if a.selftest:
        selftest()
    else:
        priv, key = a.priv, a.key
        if a.grab:
            g = json.load(open(a.grab))
            priv = priv or g.get('priv'); key = key or g.get('key')
        run(a.exchanges, a.grv, priv, a.out, key_hex=key)
