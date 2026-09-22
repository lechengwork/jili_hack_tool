#!/usr/bin/env python3
"""JILI /fg5/req crypto core — the mock server side of route X.

Protocol (fully solved last session, see PROTOCOL_SOLVED.md):

  request  (plaintext protobuf, client -> server):
     f1 = seq (varint)
     f2 = action message
     f3 = token (20B)
     f4 = client ephemeral X25519 pubkey (32B)

  response (server -> client):
     [0:64]  = Ed25519_sign(server_ed_priv, M)      where M = response[64:]
     [64:76] = nonce (12B, random)
     [76:]   = AES-256-GCM(key, nonce, plaintext, aad=b"")   (ciphertext || tag)

     key       = X25519(server_x_priv, client_pub)   # raw shared secret, no KDF
     plaintext = protobuf { f3=type, f5=data, f6=error_msg, f7=ret }
                 (field numbers verified against the real WASM — see build_plaintext)

Because we cannot obtain the real server's private keys, route X patches the two
baked pubkeys inside crypto.wasm to OURS (gen_and_patch.py); this module then
signs/encrypts with the matching mock private keys.
"""
import os, time
from cryptography.hazmat.primitives.asymmetric import x25519, ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ─── protobuf (minimal, wire-level) ──────────────────────────────────────────

def enc_varint(n):
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


def enc_tag(field, wire):
    return enc_varint((field << 3) | wire)


def field_varint(field, value):
    return enc_tag(field, 0) + enc_varint(value)


def field_bytes(field, data):
    return enc_tag(field, 2) + enc_varint(len(data)) + bytes(data)


def dec_varint(buf, i):
    shift = 0
    result = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80):
            return result, i
        shift += 7


def parse_fields(buf):
    """Parse top-level protobuf fields -> {field_num: raw_value}. Last wins.

    Values: wire 0 (varint)->int, wire 2 (len-delimited)->bytes, wire 1->8 bytes,
    wire 5->4 bytes. Enough to read a /fg5/req request.
    """
    out = {}
    i = 0
    n = len(buf)
    while i < n:
        key, i = dec_varint(buf, i)
        field = key >> 3
        wire = key & 7
        if wire == 0:
            val, i = dec_varint(buf, i)
        elif wire == 2:
            ln, i = dec_varint(buf, i)
            val = bytes(buf[i:i+ln]); i += ln
        elif wire == 1:
            val = bytes(buf[i:i+8]); i += 8
        elif wire == 5:
            val = bytes(buf[i:i+4]); i += 4
        else:
            raise ValueError(f'unsupported wire type {wire} at {i}')
        out[field] = val
    return out


# ─── raw key <-> KeyObject ───────────────────────────────────────────────────

def x_priv(raw):  return x25519.X25519PrivateKey.from_private_bytes(bytes(raw))
def x_pub(raw):   return x25519.X25519PublicKey.from_public_bytes(bytes(raw))
def ed_priv(raw): return ed25519.Ed25519PrivateKey.from_private_bytes(bytes(raw))


# ─── request / response ──────────────────────────────────────────────────────

class Fg5Crypto:
    """Holds the mock server private keys; parses requests, builds responses."""

    def __init__(self, x25519_priv_hex, ed25519_priv_hex):
        self._xpriv = x_priv(bytes.fromhex(x25519_priv_hex))
        self._epriv = ed_priv(bytes.fromhex(ed25519_priv_hex))

    def parse_request(self, body):
        f = parse_fields(body)
        seq = f.get(1, 0)
        if isinstance(seq, bytes):  # defensive
            seq = int.from_bytes(seq, 'little')
        action = f.get(2, b'')
        token = f.get(3, b'')
        client_pub = f.get(4, b'')
        return {
            'seq': seq,
            'action': action if isinstance(action, (bytes, bytearray)) else b'',
            'token': token if isinstance(token, (bytes, bytearray)) else b'',
            'client_pub': client_pub if isinstance(client_pub, (bytes, bytearray)) else b'',
        }

    def shared_key(self, client_pub):
        return self._xpriv.exchange(x_pub(client_pub))  # 32-byte raw shared secret

    # Outer response wrapper field numbers — VERIFIED empirically against the real
    # WASM (probe: send value at field N, read back which key changes). NOTE: this
    # is NOT {f1=type,f2=ret,f3=error_msg,f4=data} as older notes assumed — that only
    # ever "worked" because the all-zero "0800" test left every field at its default.
    F_TIME, F_TYPE, F_DATA, F_ERRMSG, F_RET = 1, 3, 5, 6, 7

    def build_plaintext(self, msg_type, data=b'', ret=0, error_msg='', ts_ms=None):
        """Outer wrapper protobuf: f1=server_time_ms(varint), f3=type(varint),
        f5=data(bytes), f6=error_msg(string), f7=ret(varint). Zero/empty fields omitted
        (proto3). f1 is present on EVERY real response (a millisecond server clock the game
        uses for time-sync/connection validation) — omitting it makes the client re-handshake
        and time out (MSG 999.2), so we always emit a CURRENT timestamp."""
        out = bytearray()
        out += field_varint(self.F_TIME, ts_ms if ts_ms is not None else int(time.time() * 1000))
        if msg_type:
            out += field_varint(self.F_TYPE, msg_type)         # f3 = type
        if data:
            out += field_bytes(self.F_DATA, bytes(data))       # f5 = data (inner game protobuf)
        if error_msg:
            out += field_bytes(self.F_ERRMSG, error_msg.encode())  # f6 = error_msg
        if ret:
            out += field_varint(self.F_RET, ret)               # f7 = ret
        return bytes(out)

    def encrypt_response(self, client_pub, plaintext, nonce=None):
        key = self.shared_key(client_pub)
        if nonce is None:
            nonce = os.urandom(12)
        ct = AESGCM(key).encrypt(nonce, plaintext, b'')     # ciphertext || tag(16)
        M = nonce + ct
        sig = self._epriv.sign(M)                            # 64 bytes
        return sig + M

    def make_response(self, client_pub, msg_type, data=b'', ret=0, error_msg='', nonce=None):
        pt = self.build_plaintext(msg_type, data=data, ret=ret, error_msg=error_msg)
        return self.encrypt_response(client_pub, pt, nonce=nonce)
