#!/usr/bin/env python3
"""Grab the REAL session AES key the RELIABLE way (run with sudo, game OPEN).

grabkey.py hunts the ephemeral priv/key near the pub in the general heap — brittle.
But we already KNOW where the key is: the X25519 shared (= the AES-256 key, no KDF)
sits at LINEAR offset 1108480 of the live WASM linear memory, the exact spot patchwasm's
FIX_SHARED reads/writes. This finds that memory (the range whose baked server-pub chunk#0
sits at +1048576, i.e. base == linear 0), reads 32B at +1108480, and CONFIRMS it by
AES-256-GCM-decrypting a captured response. On success writes /tmp/jili_grab.json {key,f4}.
"""
import frida, subprocess, sys, json, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 'routex')
import fg5
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NETLOG = os.environ.get('NETLOG', 'games/696/netlog_req.json')
REPLS = json.load(open('routex/wasm_pub_patches.json'))
ORIG0 = list(bytes.fromhex(REPLS[0]['orig']))          # anchor: chunk#0 of the baked server pub

# refresh exchanges from the current netlog → F4 (client_pub) + response samples for the oracle
subprocess.run(['./.venv/bin/python', 'extract_fg5.py', '696', '--netlog', NETLOG],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
ex = json.load(open('games/696/fg5_exchanges.json'))
F4, samples = None, []
for e in ex:
    f = fg5.parse_fields(bytes.fromhex(e['req_body_hex']))
    f4 = f.get(4, b'')
    if not F4 and isinstance(f4, (bytes, bytearray)) and len(f4) == 32:
        F4 = bytes(f4)
    rb = bytes.fromhex(e['resp_body_hex'])
    if len(rb) >= 92:
        samples.append((rb[64:76], rb[76:]))            # nonce(12) , ciphertext||tag
if not F4 or not samples:
    sys.exit('[!] netlog 還沒有 f4/樣本 — 確認進到遊戲畫面、握手完成再跑')
print(f'[netlog] {len(ex)} exchanges · F4={F4.hex()[:16]}… · {len(samples)} samples')

JS = r'''
var ORIG0 = %s;
function eqAt(u8, i, a){ for (var j=0;j<a.length;j++) if (u8[i+j]!==a[j]) return false; return true; }
rpc.exports.readshared = function () {
  var PUB_OFF=1048576, SH_OFF=1108480, out=[];
  Process.enumerateRanges('rw-').forEach(function (r) {
    if (r.file || r.size < SH_OFF + 32) return;
    var buf; try { buf = r.base.add(PUB_OFF).readByteArray(ORIG0.length); } catch (e) { return; }
    if (!buf) return;
    var u8 = new Uint8Array(buf);
    if (!eqAt(u8, 0, ORIG0)) return;          // chunk#0 AT +1048576 => this range base == linear 0
    try {
      var sh = new Uint8Array(r.base.add(SH_OFF).readByteArray(32)), hx='';
      for (var k=0;k<32;k++) hx += ('0'+sh[k].toString(16)).slice(-2);
      out.push(hx);
    } catch (e) {}
  });
  return out;
};
'''

def renderers():
    o = subprocess.check_output(['ps', 'aux']).decode()
    rs = []
    for l in o.splitlines():
        if 'type=renderer' in l and ('chrome-mac-arm64' in l or 'Chrome for Testing' in l):
            p = l.split()
            try: rs.append((int(p[1]), int(p[5])))
            except (ValueError, IndexError): pass
    return sorted(rs, key=lambda x: -x[1])

def works(keyhex):
    key = bytes.fromhex(keyhex)
    for nonce, ct in samples[:8]:
        try:
            AESGCM(key).decrypt(nonce, ct, b''); return True
        except Exception:
            pass
    return False

cands = []
for pid, rss in renderers():
    try:
        s = frida.attach(pid)
        sc = s.create_script(JS % json.dumps(ORIG0)); sc.load()
        res = sc.exports_sync.readshared()
        print(f'  pid {pid} ({rss//1024}MB): {len(res)} @1108480 候選')
        cands += res
        s.detach()
    except Exception as e:
        print(f'  pid {pid}: attach/read FAIL {e!r}')

key = next((c for c in dict.fromkeys(cands) if works(c)), None)
if key:
    json.dump({'key': key, 'f4': F4.hex()}, open('/tmp/jili_grab.json', 'w'))
    print(f'\n[OK] AES key = {key}')
    print('[OK] 已存 /tmp/jili_grab.json — 回 ./capture_finish.sh 或直接 decrypt。')
else:
    print(f'\n[MISS] 讀到 {len(set(cands))} 個 @1108480 候選,但都解不開樣本。')
    print('  · 候選=0 → 沒找到 WASM linear memory(遊戲進到畫面了嗎?renderer 夠大嗎?)')
    print('  · 有候選但解不開 → shared 位址可能位移了,把上面每行貼給 Claude。')
