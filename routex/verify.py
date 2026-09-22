#!/usr/bin/env python3
"""Self-consistency test for the mock crypto core (fg5.py).

Plays BOTH sides of the solved protocol in Python:
  1. a fake client makes an ephemeral X25519 keypair and a /fg5/req request,
  2. the mock server (fg5.Fg5Crypto) parses it and builds a response,
  3. we then verify/decrypt the response exactly as the patched WASM would:
       - Ed25519_verify(mock_ed_pub, sig, M)      (M = response[64:])
       - key = X25519(client_priv, mock_x_pub)    (client's view of the shared secret)
       - AES-256-GCM decrypt (aad=b"")
       - parse outer protobuf -> {type, ret, error_msg, data}

If the client's independently-derived key decrypts what the server encrypted, and
the signature verifies under the mock Ed25519 pub, the core matches the spec.
This does NOT re-run the real WASM (that was already done end-to-end last session
via harness_run2.js); it proves our implementation is faithful.
"""
import os, json, sys
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
import fg5

raw_pub = lambda ko: ko.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
raw_priv = lambda ko: ko.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                       serialization.NoEncryption())

HERE = os.path.dirname(os.path.abspath(__file__))


def mock_keys():
    p = os.path.join(HERE, 'mockkeys.json')
    if os.path.exists(p):
        return json.load(open(p))
    xp = x25519.X25519PrivateKey.generate()
    ep = ed25519.Ed25519PrivateKey.generate()
    return {
        'x25519_priv': raw_priv(xp).hex(), 'x25519_pub': raw_pub(xp.public_key()).hex(),
        'ed25519_priv': raw_priv(ep).hex(), 'ed25519_pub': raw_pub(ep.public_key()).hex(),
    }


def build_request(seq, token, client_pub, action=b''):
    """A minimal /fg5/req request, same field layout as real captures."""
    out = bytearray()
    out += fg5.field_varint(1, seq)
    if action:
        out += fg5.field_bytes(2, action)
    out += fg5.field_bytes(3, token)
    out += fg5.field_bytes(4, client_pub)
    return bytes(out)


def client_decrypt_verify(resp, client_xpriv_raw, mock_x_pub_raw, mock_ed_pub_raw):
    assert len(resp) >= 64 + 12 + 16, f'response too short: {len(resp)}'
    sig, M = resp[:64], resp[64:]
    # 1) Ed25519 signature over M
    ed25519.Ed25519PublicKey.from_public_bytes(mock_ed_pub_raw).verify(sig, M)
    # 2) client's shared secret = X25519(client_priv, server_pub)
    key = fg5.x_priv(client_xpriv_raw).exchange(fg5.x_pub(mock_x_pub_raw))
    # 3) AES-256-GCM decrypt
    nonce, ct = M[:12], M[12:]
    pt = AESGCM(key).decrypt(nonce, ct, b'')
    # 4) parse outer wrapper (field numbers verified vs real WASM: type=3,data=5,err=6,ret=7)
    f = fg5.parse_fields(pt)
    return {
        'type': f.get(fg5.Fg5Crypto.F_TYPE, 0),
        'ret': f.get(fg5.Fg5Crypto.F_RET, 0),
        'error_msg': (f.get(fg5.Fg5Crypto.F_ERRMSG, b'') or b'').decode('utf-8', 'replace') if isinstance(f.get(fg5.Fg5Crypto.F_ERRMSG), (bytes, bytearray)) else '',
        'data': list(f.get(fg5.Fg5Crypto.F_DATA, b'')) if isinstance(f.get(fg5.Fg5Crypto.F_DATA), (bytes, bytearray)) else [],
    }


def main():
    mk = mock_keys()
    server = fg5.Fg5Crypto(mk['x25519_priv'], mk['ed25519_priv'])
    mock_x_pub = bytes.fromhex(mk['x25519_pub'])
    mock_ed_pub = bytes.fromhex(mk['ed25519_pub'])

    # fake client
    c_xpriv = x25519.X25519PrivateKey.generate()
    c_xpriv_raw = raw_priv(c_xpriv)
    c_xpub_raw = raw_pub(c_xpriv.public_key())
    token = os.urandom(20)

    passed = 0
    cases = []

    # Case A: the harness's canonical minimal response {type:0} (plaintext "0800").
    cases.append(('empty type:0', 0, b''))

    # Cases B..: replay the real decrypted samples we captured.
    rj = os.path.join(HERE, '..', 'games', '696', 'responses.jsonl')
    if os.path.exists(rj):
        for line in open(rj):
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            raw = o.get('raw', o.get('data', []))   # responses.jsonl stores the f4 payload under 'raw'
            cases.append((f"replay type:{o['type']} ({len(raw)}B)", o['type'], bytes(raw)))

    for name, mtype, data in cases:
        req = build_request(seq=42, token=token, client_pub=c_xpub_raw, action=b'\x08\x00')
        parsed = server.parse_request(req)
        assert parsed['client_pub'] == c_xpub_raw, 'client_pub roundtrip mismatch'
        assert parsed['token'] == token, 'token roundtrip mismatch'
        assert parsed['seq'] == 42, f"seq mismatch: {parsed['seq']}"

        resp = server.make_response(parsed['client_pub'], mtype, data=data)
        decoded = client_decrypt_verify(resp, c_xpriv_raw, mock_x_pub, mock_ed_pub)
        assert decoded['type'] == mtype, f"type mismatch {decoded['type']} != {mtype}"
        assert list(decoded['data']) == list(data), 'data roundtrip mismatch'
        print(f"  OK  {name:32s} resp={len(resp)}B  ->  type={decoded['type']} ret={decoded['ret']} data={len(decoded['data'])}B")
        passed += 1

    # Negative: a tampered signature must fail verification.
    req = build_request(1, token, c_xpub_raw, action=b'\x08\x00')
    resp = bytearray(server.make_response(c_xpub_raw, 0, data=b''))
    resp[10] ^= 0xff
    try:
        client_decrypt_verify(bytes(resp), c_xpriv_raw, mock_x_pub, mock_ed_pub)
        print('  FAIL  tampered signature was accepted!'); sys.exit(1)
    except Exception:
        print('  OK  tampered signature rejected'); passed += 1

    # Negative: wrong client key must fail AEAD.
    other = raw_priv(x25519.X25519PrivateKey.generate())
    resp = server.make_response(c_xpub_raw, 0, data=b'')
    try:
        client_decrypt_verify(resp, other, mock_x_pub, mock_ed_pub)
        print('  FAIL  wrong key decrypted!'); sys.exit(1)
    except Exception:
        print('  OK  wrong client key rejected'); passed += 1

    print(f"\n[verify] {passed} checks passed — crypto core matches PROTOCOL_SOLVED.md")


if __name__ == '__main__':
    main()
