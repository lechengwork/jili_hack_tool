#!/usr/bin/env python3
"""Robust ephemeral-key / AES-key grabber for JILI 696 (run with sudo).

Fixes the silent `+0 dumps` from b_all.py:
  · attaches to EVERY renderer and prints each one's rw- range count, size, and
    f4-hit-count — so a miss is diagnosable instead of silent
  · scans huge ranges in 32 MB chunks (Cocos renderers have multi-hundred-MB
    ranges that can make one big scanSync choke)
  · TWO recovery paths: (a) X25519 pub-match a 32B window against the request's f4
    → ephemeral priv; (b) if the raw priv is already freed, try each 32B window as
    the AES-256-GCM key directly against a captured (nonce, ct) — the session key
    lives in a once_cell and persists for the whole open session.

f4 and the ciphertext samples come from the CURRENT netlog (netlog_req.json), so
just keep the game window OPEN and run this any time after entering the game.

  sudo ./.venv/bin/python grabkey.py
  → on success writes /tmp/jili_grab.json  ({priv?, key})  — paste it to Claude.
"""
import frida, subprocess, sys, json, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # repo root (portable)
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NETLOG = os.environ.get('NETLOG', 'games/696/netlog_req.json')
SERVER_X = bytes.fromhex('26aa760e99da9a40f3ab907f0d7b07e17b36e6a199e8400abde61af01a08da17')
RADIUS = int(os.environ.get('RADIUS', '8192'))   # dump ±this around each f4 hit


def pf(h):
    b = bytes.fromhex(h); i = 0; f = {}
    while i < len(b):
        t = b[i]; fl = t >> 3; wt = t & 7; i += 1
        if wt == 0:
            v = 0; s = 0
            while i < len(b) and b[i] & 0x80:
                v |= (b[i] & 0x7f) << s; s += 7; i += 1
            v |= (b[i] & 0x7f) << s; i += 1; f[fl] = v
        elif wt == 2:
            ln = b[i]; i += 1; f[fl] = b[i:i+ln]; i += ln
        else:
            break
    return f


# 1) refresh exchanges from the CURRENT netlog and pull f4 + ciphertext samples
subprocess.run(['cp', NETLOG, '/tmp/netlog_now.json'])
subprocess.run(['./.venv/bin/python', 'extract_fg5.py', '696', '--netlog', '/tmp/netlog_now.json'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
ex = json.load(open('games/696/fg5_exchanges.json'))
F4 = None; samples = []
for e in ex:
    fr = pf(e['req_body_hex'])
    if not F4 and 4 in fr and isinstance(fr[4], (bytes, bytearray)) and len(fr[4]) == 32:
        F4 = bytes(fr[4])
    rb = bytes.fromhex(e['resp_body_hex'])
    if len(rb) >= 92:
        samples.append((rb[64:76], rb[76:]))
print(f'[netlog] {len(ex)} exchanges · F4={F4.hex() if F4 else None} · {len(samples)} resp samples')
if not F4:
    sys.exit('[!] netlog 裡沒有 f4 — 遊戲還沒握手完成,進到遊戲畫面再跑')


def renderers():
    o = subprocess.check_output(['ps', 'aux']).decode()
    return [int(l.split()[1]) for l in o.splitlines()
            if 'type=renderer' in l and ('chrome-mac-arm64' in l or 'Chrome for Testing' in l)]

JS = r'''
var PAT=%s;
// read up to sz bytes from addr, shrinking the SIZE on failure (addr itself is mapped
// because scanSync just read the pattern there) — beats all-or-nothing readByteArray.
function readFrom(addr, sz){
  // frida 17.x removed Memory.readByteArray — use the NativePointer method addr.readByteArray.
  var tr=[sz,16384,8192,4096,2048,1024,512,256,128,64,32];
  for(var i=0;i<tr.length;i++){ if(tr[i]<=sz+1){ try{return addr.readByteArray(tr[i]);}catch(e){} } }
  return null;
}
rpc.exports.scan=function(){
  var nR=0, tot=0, hits=0, dumped=0, RAD=%d;
  Process.enumerateRanges('rw-').forEach(function(r){
    nR++; tot+=r.size;
    var CH=32*1024*1024;
    for(var off=0; off<r.size; off+=CH){
      var sz=Math.min(CH, r.size-off);
      try{
        Memory.scanSync(r.base.add(off), sz, PAT).forEach(function(m){
          hits++;
          // forward: pub + up to RAD after it (reliable, addr is mapped)
          var fwd=readFrom(m.address, 32+RAD);
          if(fwd){ send({t:'dump'}, fwd); dumped++; }
          // backward: grab a chunk ending at the pub, from the nearest readable start
          var back=[RAD,4096,2048,1024,512,256,128];
          for(var j=0;j<back.length;j++){
            var st=m.address.sub(back[j]); if(st.compare(r.base)<0) continue;
            var b=readFrom(st, back[j]+32);
            if(b){ send({t:'dump'}, b); dumped++; break; }
          }
        });
      }catch(_){}
    }
  });
  return {ranges:nR, totalMB:Math.round(tot/1048576), hits:hits, dumped:dumped};
};
'''
pat = ' '.join('%02x' % x for x in F4)
dumps = []
pids = renderers()
print(f'[scan] {len(pids)} renderers: {pids}')
for pid in pids:
    try:
        s = frida.attach(pid)
        sc = s.create_script(JS % (json.dumps(pat), RADIUS))
        sc.on('message', lambda m, d: dumps.append(bytes(d)) if (m['type'] == 'send' and d) else None)
        sc.load()
        res = sc.exports_sync.scan()
        print(f'  pid {pid}: ranges={res["ranges"]:<5} {res["totalMB"]:>5}MB  f4_hits={res["hits"]}  dumps={res["dumped"]}')
        s.detach()
    except Exception as ex2:
        print(f'  pid {pid}: attach/scan FAIL {ex2!r}')
print(f'[dump] {len(dumps)} windows · {sum(len(d) for d in dumps)//1024}KB total')

# 2) recover priv (pub-match) or key (oracle)
cands = set()
for b in dumps:
    for off in range(0, len(b) - 31):
        w = b[off:off+32]
        if len(set(w)) >= 12:          # entropy gate
            cands.add(w)
print(f'[cands] {len(cands)} distinct high-entropy 32B windows')

out = {}
for w in cands:
    try:
        pub = X25519PrivateKey.from_private_bytes(w).public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        if pub == F4:
            out['priv'] = w.hex()
            key = X25519PrivateKey.from_private_bytes(w).exchange(X25519PublicKey.from_public_bytes(SERVER_X))
            out['key'] = key.hex()
            print(f'[!!!] ephemeral X25519 priv = {w.hex()}')
            print(f'[key] AES-256 key = {key.hex()}')
            break
    except Exception:
        pass

if 'key' not in out and samples:
    nonce, ct = samples[0]
    for w in cands:
        try:
            AESGCM(w).decrypt(nonce, ct, b'')
            out['key'] = w.hex()
            print(f'[!!!] AES-256 key (oracle match) = {w.hex()}')
            break
        except Exception:
            pass

if out.get('key'):
    out['f4'] = F4.hex()
    json.dump(out, open('/tmp/jili_grab.json', 'w'))
    print('\n[OK] 已存 /tmp/jili_grab.json — 貼給 Claude,他離線解全部回應。')
else:
    print('\n[MISS] 沒撈到。看上面每個 pid 的 f4_hits:')
    print('  · 全 f4_hits=0  → f4 不在被掃的記憶體(掛錯進程/wasm 沒列舉)。把 pid 那幾行貼我。')
    print('  · 有 hits 但 cands 找不到 → 加大半徑重跑:  sudo RADIUS=65536 ./.venv/bin/python grabkey.py')
