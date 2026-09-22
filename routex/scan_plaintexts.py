#!/usr/bin/env python3
"""Read-only: scan a renderer heap dump for the game's cached decrypted responses.

The game caches each decrypted /fg5/req response as a JSON blob in the JS heap:
    {"type":N,"ret":0,"error_msg":"...","data":[<byte,byte,...>]}
We recover every such blob (all message types, incl. the handshake/config one we
are missing) so the mock server can re-encrypt and replay them. Pure analysis of
an existing dump — no live process, no crypto, no patching.
"""
import sys, os, re, json

DUMP = sys.argv[1] if len(sys.argv) > 1 else '/tmp/bet100.bin'
OUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plaintexts.jsonl')

# Stream the (large) file in overlapping chunks and find blob starts.
CHUNK = 64 * 1024 * 1024
OVERLAP = 1 << 20  # 1 MB, longer than any single blob
START = re.compile(rb'\{"type":')

def parse_blob(buf, at):
    """Try to JSON-decode the object beginning at buf[at]; return (obj, end) or None."""
    depth = 0
    i = at
    n = len(buf)
    in_str = False
    esc = False
    while i < n:
        c = buf[i]
        if in_str:
            if esc:            esc = False
            elif c == 0x5c:    esc = True      # backslash
            elif c == 0x22:    in_str = False  # quote
        else:
            if c == 0x22:      in_str = True
            elif c == 0x7b:    depth += 1      # {
            elif c == 0x7d:                    # }
                depth -= 1
                if depth == 0:
                    frag = buf[at:i+1]
                    try:
                        return json.loads(frag.decode('latin-1')), i + 1
                    except Exception:
                        return None
        i += 1
    return None  # ran off the end of this window; caught by overlap next round


def main():
    size = os.path.getsize(DUMP)
    print(f'[scan] {DUMP} ({size/1e9:.2f} GB)')
    seen = set()
    out = []
    with open(DUMP, 'rb') as f:
        pos = 0
        prev_tail = b''
        while pos < size:
            f.seek(pos)
            chunk = f.read(CHUNK)
            buf = prev_tail + chunk
            base = pos - len(prev_tail)
            for m in START.finditer(buf):
                r = parse_blob(buf, m.start())
                if not r:
                    continue
                obj, _ = r
                if not isinstance(obj, dict) or 'type' not in obj or 'data' not in obj:
                    continue
                data = obj.get('data')
                if not isinstance(data, list):
                    continue
                key = (obj.get('type'), tuple(data))
                if key in seen:
                    continue
                seen.add(key)
                out.append({
                    'type': obj.get('type'),
                    'ret': obj.get('ret'),
                    'error_msg': obj.get('error_msg', ''),
                    'len': len(data),
                    'data': data,
                })
            prev_tail = buf[-OVERLAP:]
            pos += CHUNK
            print(f'\r[scan] {min(pos,size)/1e9:.2f} GB, {len(out)} unique blobs', end='', flush=True)
    print()
    out.sort(key=lambda x: (x['type'], x['len']))
    with open(OUT, 'w') as fo:
        for o in out:
            fo.write(json.dumps(o) + '\n')
    print(f'[scan] wrote {len(out)} unique plaintext(s) -> {OUT}')
    from collections import Counter
    c = Counter((o['type'] for o in out))
    for t in sorted(c):
        lens = sorted({o['len'] for o in out if o['type'] == t})
        print(f'  type {t}: {c[t]} blob(s), data lens={lens}')


if __name__ == '__main__':
    main()
