#!/usr/bin/env python3
"""Route X step 1: generate the mock server keypair and patch crypto.wasm so the
client uses OUR baked public keys instead of the real server's.

Both baked pubs are stored in the wasm data section as 4x8-byte chunks, each
byte XOR 0xAA. We locate the current (real-server) obfuscated chunks by content
search and overwrite them with our mock pubs' obfuscated chunks. This is exactly
equivalent to the runtime patch that harness_run2.js already proved works: the
data section is copied verbatim into linear memory at instantiation, before
__wbindgen_start, and the constants are read (and de-XOR'd) fresh at crypto time.
"""
import json, os, sys
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives import serialization

HERE = os.path.dirname(os.path.abspath(__file__))
WASM_IN  = os.path.join(HERE, '..', 'games', '696', 'crypto.wasm')
WASM_OUT = os.path.join(HERE, 'crypto.patched.wasm')
KEYS_OUT = os.path.join(HERE, 'mockkeys.json')

# Real server baked pubs (recovered last session) — used only to locate the
# obfuscated chunks in the file.
REAL_X25519_PUB  = bytes.fromhex('26aa760e99da9a40f3ab907f0d7b07e17b36e6a199e8400abde61af01a08da17')
REAL_ED25519_PUB = bytes.fromhex('81c785c85653e6a1e92c9359646e23f662f5615975ae7faa6a5721358018ff8c')

xor = lambda b: bytes(x ^ 0xAA for x in b)
raw_pub = lambda ko: ko.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
raw_priv = lambda ko: ko.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                       serialization.NoEncryption())


def gen_keys():
    if os.path.exists(KEYS_OUT):
        keys = json.load(open(KEYS_OUT))
        print('[keys] reusing existing', KEYS_OUT)
        return keys
    xp = x25519.X25519PrivateKey.generate()
    ep = ed25519.Ed25519PrivateKey.generate()
    keys = {
        'x25519_priv':  raw_priv(xp).hex(),
        'x25519_pub':   raw_pub(xp.public_key()).hex(),
        'ed25519_priv': raw_priv(ep).hex(),
        'ed25519_pub':  raw_pub(ep.public_key()).hex(),
    }
    json.dump(keys, open(KEYS_OUT, 'w'), indent=2)
    print('[keys] generated', KEYS_OUT)
    return keys


def patch_pub(buf, real_pub, mock_pub, label):
    """Replace the 4 obfuscated 8-byte chunks of real_pub with mock_pub's."""
    for i in range(4):
        real_obf = xor(real_pub[i*8:i*8+8])
        mock_obf = xor(mock_pub[i*8:i*8+8])
        occ = []
        start = 0
        while True:
            idx = buf.find(real_obf, start)
            if idx < 0:
                break
            occ.append(idx); start = idx + 1
        if len(occ) != 1:
            raise SystemExit(f'[FATAL] {label} chunk{i} found {len(occ)} times (expected 1): {occ}')
        off = occ[0]
        buf[off:off+8] = mock_obf
        print(f'  {label} chunk{i} @file+{off}: {real_obf.hex()} -> {mock_obf.hex()}')


def main():
    keys = gen_keys()
    print('[keys]')
    for k, v in keys.items():
        print(f'  {k} = {v}')

    buf = bytearray(open(WASM_IN, 'rb').read())
    print(f'[patch] {WASM_IN} ({len(buf)} bytes)')
    patch_pub(buf, REAL_X25519_PUB,  bytes.fromhex(keys['x25519_pub']),  'X25519')
    patch_pub(buf, REAL_ED25519_PUB, bytes.fromhex(keys['ed25519_pub']), 'Ed25519')
    open(WASM_OUT, 'wb').write(buf)
    print(f'[patch] wrote {WASM_OUT} ({len(buf)} bytes)')

    # Verify: re-locate the mock obfuscated chunks in the output, de-XOR, compare.
    out = bytes(buf)
    for label, pub in (('X25519', keys['x25519_pub']), ('Ed25519', keys['ed25519_pub'])):
        pub = bytes.fromhex(pub)
        for i in range(4):
            mock_obf = xor(pub[i*8:i*8+8])
            assert out.count(mock_obf) == 1, f'{label} chunk{i} not uniquely present after patch'
        # neither real pub chunk should remain
    for label, pub in (('X25519', REAL_X25519_PUB), ('Ed25519', REAL_ED25519_PUB)):
        for i in range(4):
            assert xor(pub[i*8:i*8+8]) not in out, f'{label} real chunk{i} still present!'
    print('[verify] all mock chunks present, no real chunks remain — OK')


if __name__ == '__main__':
    main()
