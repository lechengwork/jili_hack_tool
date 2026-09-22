#!/usr/bin/env python3
"""Live WASM keypatch for JILI 696 (run with sudo, alongside the mock server).

The fg5 crypto (Rust wasm-bindgen, embedded+decoded in the Jscrambler'd bundle) bakes the REAL
server's X25519 + Ed25519 pubs (XOR-0xAA obfuscated). We can't hook WebAssembly from JS
(Jscrambler self-defense) nor swap a file (wasm is decoded from the bundle), so we overwrite the
two baked pubs directly in the renderer's WASM linear memory via Frida. Applying the 8 chunk
replacements (routex/wasm_pub_patches.json) reproduces crypto.patched.wasm byte-for-byte (verified),
i.e. makes the in-memory crypto identical to the harness-proven-good patched module.

TIMING IS EVERYTHING (PROTOCOL_SOLVED.md 42-47):
  * Ed25519 verify re-reads the baked pub every response — patching it takes effect immediately.
  * The AES-GCM context is built ONCE (once_cell) from shared@1108480. If it was built from the
    ORIGINAL pub's shared key, patching the pub afterwards is too late — decrypt keeps failing and
    the game loops the handshake -> MSG 999.2. So the pub MUST be patched BEFORE the first key
    derivation of a freshly-loaded wasm instance.

API notes that cost us days: Memory.scanSync SILENTLY MISSES these WASM ranges on macOS (use
readByteArray whole-range + JS search); Memory.read/writeByteArray were removed (use the
NativePointer methods addr.read/writeByteArray). Direct in-process writes stick (no RO/COW issue).

WINNING SEQUENCE (attach is fast on a settled renderer, and a reload keeps the same pid):
  1. Game open & settled at 999.2.
  2. sudo SECS=300 ./.venv/bin/python patchwasm.py   # attaches, then loops a whole-range scan
                                                       # (~1-2s each) that re-patches every pass.
  3. Reload the page (Cmd-R). The fresh wasm loads in the SAME (still-attached) renderer; a scan
     pass patches its pub before once_cell builds the AES context (only built on the first decrypted
     response, a multi-second window) -> handshake verifies -> mock log advances to seq=2.
"""
import frida, subprocess, sys, json, time, os, threading
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # repo root (this file lives there) — portable


def patch_with_timeout(sc, timeout):
    """Run the agent's patch() but never block forever: if a readByteArray wedges on a bad range,
    return 'TIMEOUT' so the caller can detach + reattach instead of freezing the terminal."""
    box = {}
    def run():
        try:
            box['res'] = sc.exports_sync.patch()
        except Exception as e:
            box['err'] = e
    th = threading.Thread(target=run, daemon=True)
    th.start()
    deadline = time.time() + timeout
    while th.is_alive() and time.time() < deadline:
        th.join(0.3)          # short slices so Ctrl-C is handled between them (one long join
                              # would swallow SIGINT and make the process unkillable for `timeout`s)
    if th.is_alive():
        return 'TIMEOUT'
    if 'err' in box:
        raise box['err']
    return box['res']

REPLS = json.load(open('routex/wasm_pub_patches.json'))   # [{orig, new}, ...]
SECS = int(os.environ.get('SECS', '90'))
# Opt-in fallback: also overwrite shared@1108480 with the mock's correct shared (published by the
# server to this file). Set FIX_SHARED=1 (default path) or FIX_SHARED=/path/to/mock_shared.hex.
FIX_SHARED = os.environ.get('FIX_SHARED')
SHARED_FILE = (FIX_SHARED if (FIX_SHARED and FIX_SHARED not in ('1', 'true', 'yes', 'on'))
               else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'routex', 'mock_shared.hex'))

PAIRS = [{'origArr': list(bytes.fromhex(r['orig'])),
          'newArr': list(bytes.fromhex(r['new']))} for r in REPLS]

JS = r'''
var PAIRS = %s;

function bytesEqual(addr, arr) {
  try {
    var cur = new Uint8Array(addr.readByteArray(arr.length));
    for (var i = 0; i < arr.length; i++) { if (cur[i] !== arr[i]) return false; }
    return true;
  } catch (e) { return false; }   // addr can vanish mid-load; treat as "not equal", never crash
}

// mach_vm_protect(task, addr, size, set_maximum, new_protection). VM_PROT_COPY forces a
// copy-on-write break on shared/COW pages, which plain Memory.protect does NOT do.
var _machProtect = null, _task = 0;
try {
  var pProt = Module.findExportByName(null, 'mach_vm_protect');
  var pSelf = Module.findExportByName(null, 'mach_task_self_');
  if (pProt && pSelf) {
    _machProtect = new NativeFunction(pProt, 'int', ['uint', 'pointer', 'uint64', 'int', 'int']);
    _task = pSelf.readU32();
  }
} catch (e) {}
function cowBreak(addr, len) {
  if (!_machProtect || !_task) return false;
  return _machProtect(_task, addr, len, 0, 0x13) === 0;   // READ|WRITE|COPY
}

// Try in order: direct write, protect+write, patchCode (Apple-Silicon JIT/APRR/RX), COW-break.
// Read back after each — a write that throws nothing but does not stick counts as a failure.
function writeVerified(addr, newbytes, diag) {
  if (bytesEqual(addr, newbytes)) return 'already';
  var rr = Process.findRangeByAddress(addr);
  var prot = rr ? rr.protection : '???';
  try { addr.writeByteArray(newbytes); if (bytesEqual(addr, newbytes)) return 'direct'; }
  catch (e) { diag.push('w[' + prot + ']:' + e.message); }
  try { Memory.protect(addr, newbytes.length, 'rwx'); addr.writeByteArray(newbytes);
        if (bytesEqual(addr, newbytes)) return 'protect'; }
  catch (e) { diag.push('p[' + prot + ']:' + e.message); }
  try { Memory.patchCode(addr, newbytes.length, function (w) { w.writeByteArray(newbytes); });
        if (bytesEqual(addr, newbytes)) return 'patchCode'; }
  catch (e) { diag.push('pc[' + prot + ']:' + e.message); }
  try { if (cowBreak(addr, newbytes.length)) { addr.writeByteArray(newbytes);
        if (bytesEqual(addr, newbytes)) return 'cow'; } }
  catch (e) { diag.push('cow[' + prot + ']:' + e.message); }
  diag.push('FAIL[' + prot + ']:not-sticking');
  return null;
}

// First-byte dispatch: HIT[b] = [[pairIndex, kind], ...], kind 0=orig 1=new. FLAG is a PACKED
// fast-reject table — HIT is a holey Array whose hole-reads (nearly every byte) walk the prototype
// chain and crawl over ~GB of memory; a Uint8Array never holes, so FLAG[b]===0 rejects instantly.
var HIT = new Array(256);
var FLAG = new Uint8Array(256);
function _reg(b, pi, kind) { if (!HIT[b]) HIT[b] = []; HIT[b].push([pi, kind]); FLAG[b] = 1; }
for (var _p = 0; _p < PAIRS.length; _p++) {
  _reg(PAIRS[_p].origArr[0], _p, 0);
  _reg(PAIRS[_p].newArr[0], _p, 1);
}

// Remembered across calls: the range that last held the live copy, and the set of candidate bases
// seen last round. Reading the winner first makes steady state one 16KB read; reading only BRAND-NEW
// ranges after it (a reload's fresh wasm memory is always a new range) makes the catch a few reads.
var winBase = null, winSize = 0, prevBases = {};

// Whole-range readByteArray + JS search (scanSync silently misses WASM ranges on macOS). This
// reliably found+patched every copy at t=0 in all runs; we just loop it so a freshly-reloaded
// wasm gets its pub patched before once_cell builds the AES context — a multi-second window,
// since that context is only built on the FIRST decrypted response.
rpc.exports.patch = function () {
  var orig_hits = 0, new_present = 0, changed = 0, already = 0, fails = 0, scanned = 0, cands = 0;
  var diag = [], methods = {};
  // The pub's 8 chunks live in a ~4.5KB window at LINEAR offset 1048576 of the LIVE wasm memory
  // (dump-confirmed: chunk#0 @ 1048576, rest through 1053040). The live linear memory range starts
  // at linear 0, so we read ONLY 16KB at range_base+1048576 per candidate range — NO whole-range
  // reads (those wedge/crawl on huge sparse V8 reservations). +1048576 only lines up in the live
  // linear memory (the module-bytes / decoded copies hold chunk#0 at other offsets), so this also
  // auto-targets the one copy the crypto actually reads. Anonymous ranges only; file maps skipped.
  var PUB_OFF = 1048576, WINDOW = 16384;
  var cs = [], thisBases = {};
  var ranges = Process.enumerateRanges('rw-');
  for (var ri = 0; ri < ranges.length; ri++) {
    var r = ranges[ri];
    if (r.size >= PUB_OFF + WINDOW && !r.file) { cs.push(r); thisBases[r.base.toString()] = 1; }
  }
  // rank 0 = last winner, 1 = brand-new range (a reload's fresh wasm memory), 2 = already-seen.
  // We read only rank 0 and 1: the live pub is either still in the winner or in a new range; a range
  // we already scanned in an earlier round and rejected can't suddenly hold the live copy.
  function rankOf(r) {
    if (winBase && r.base.equals(winBase)) return 0;
    return prevBases[r.base.toString()] ? 2 : 1;
  }
  // Sort winner(0)/new(1)/seen(2) first, but SCAN ALL every pass. The old "break on rank-2"
  // early-out (an already-seen range can't suddenly hold the live copy) is FALSE while the game
  // is (re)loading: a range we scanned EMPTY still receives the wasm's data-segment copy when
  // crypto instantiates — cold start, OR a reload whose fresh wasm reuses a previously-seen base.
  // That early-out is exactly why the patcher went 0cand-idle and never patched. Each read is
  // just 16KB @ +1048576 (35 ranges ≈ 0.11s), so full re-scans are cheap. The sort still makes us
  // hit the live/fresh copy first, and `origHere` below stops the pass the moment we patch it.
  cs.sort(function (a, b) { return rankOf(a) - rankOf(b); });
  for (var k = 0; k < cs.length; k++) {
    var r = cs[k];
    cands++;
    var buf = null;
    try { buf = r.base.add(PUB_OFF).readByteArray(WINDOW); } catch (e) {}
    if (!buf) continue;
    var u8 = new Uint8Array(buf), n = u8.length, hitHere = false, origHere = false;
    scanned += n;
    for (var i = 0; i < n; i++) {
      if (FLAG[u8[i]] === 0) continue;
      var cand = HIT[u8[i]];
      for (var c = 0; c < cand.length; c++) {
        var pi = cand[c][0], kind = cand[c][1];
        var pat = kind === 0 ? PAIRS[pi].origArr : PAIRS[pi].newArr, m = pat.length;
        if (i + m > n) continue;
        var ok = true;
        for (var j = 1; j < m; j++) { if (u8[i + j] !== pat[j]) { ok = false; break; } }
        if (!ok) continue;
        hitHere = true;
        if (kind === 1) { new_present++; continue; }
        origHere = true; orig_hits++;
        var res = writeVerified(r.base.add(PUB_OFF + i), PAIRS[pi].newArr, diag);
        if (res === 'already') already++;
        else if (res) { changed++; methods[res] = (methods[res] || 0) + 1; }
        else fails++;
      }
    }
    if (hitHere) { winBase = r.base; winSize = r.size; }
    if (origHere) break;   // caught & patched a fresh, unpatched copy (the reload) — stop
  }
  prevBases = thisBases;
  // DIAGNOSTIC (read-only): dump the 32-byte X25519 shared the game derived+stored at
  // linear 1108480 of the LIVE memory. Compare against the mock's expected shared (server
  // logs it at handshake): equal => game used the mock pub (patch won); different+nonzero =>
  // game used the REAL pub (patch too late -> fallback); all-zero => not derived yet (winning).
  var shared_hex = '';
  if (winBase) {
    try {
      var sb = new Uint8Array(winBase.add(1108480).readByteArray(32)), hx = '';
      for (var si = 0; si < sb.length; si++) { hx += ('0' + sb[si].toString(16)).slice(-2); }
      shared_hex = hx;
    } catch (e) {}
  }
  var msum = Object.keys(methods).map(function (k) { return k + '=' + methods[k]; }).join(',');
  return { orig_hits: orig_hits, new_present: new_present, changed: changed, already: already,
           fails: fails, scanned_kb: Math.round(scanned / 1024), cands: cands,
           method: msum, diag: diag.slice(0, 5).join('  '), shared_hex: shared_hex };
};

// FALLBACK (opt-in, FIX_SHARED): overwrite the game's derived shared @1108480 with the mock's
// correct shared, so the AES-GCM decrypt uses the right key even though X25519 ran against the real
// pub. winBase is set by patch(); call this right AFTER patch() each pass so we keep the correct
// value present through the response-stall/decrypt window. If overwriting here still doesn't decrypt,
// the AES context was cached (once_cell) from the wrong value at derive time — then we also need to
// reset that flag (a further step). Returns what happened, for logging.
rpc.exports.fixshared = function (arr) {
  if (!winBase) return { ok: false, reason: 'no-winbase' };
  var addr = winBase.add(1108480), before = '';
  try {
    var b = new Uint8Array(addr.readByteArray(arr.length));
    for (var i = 0; i < b.length; i++) before += ('0' + b[i].toString(16)).slice(-2);
  } catch (e) { return { ok: false, reason: 'read-failed' }; }
  var res = writeVerified(addr, arr, []);
  return { ok: !!res, method: res, before: before };
};
'''


def renderers():
    # [(pid, rss_kb), ...] biggest-RSS first. ps aux columns: 2=pid, 6=RSS(KB).
    o = subprocess.check_output(['ps', 'aux']).decode()
    out = []
    for l in o.splitlines():
        if ('type=renderer' in l
                and ('Google Chrome' in l or 'chrome-mac-arm64' in l or 'Chrome for Testing' in l)):
            p = l.split()
            try:
                out.append((int(p[1]), int(p[5])))
            except (ValueError, IndexError):
                pass
    out.sort(key=lambda x: -x[1])
    return out


def main():
    print(f'[patchwasm] {len(PAIRS)} chunks, hammering for {SECS}s. Keep the game OPEN.\n'
          f'           Once it shows "(mock pub in place ✓)", RELOAD the page (Cmd-R) — the fresh '
          f'wasm gets patched before it derives its key.')
    t0 = time.time()
    sess = sc = cur_pid = None
    total_changed = 0
    last_printed_sh = None      # only re-print the full shared when it actually changes (no spam)
    while time.time() - t0 < SECS:
        tag = f't={int(time.time()-t0):>3}s'
        rs = renderers()
        alive = cur_pid is not None and cur_pid in [p for p, _ in rs]
        if sess is None or not alive:
            if sess:
                try: sess.detach()
                except Exception: pass
            sess = sc = cur_pid = None
            if not rs:
                print(f'  {tag}  renderers=0  waiting for game…', flush=True)
                time.sleep(1.0); continue
            pid, rss = rs[0]
            ta = time.time()
            try:
                sess = frida.attach(pid)
                sc = sess.create_script(JS % json.dumps(PAIRS)); sc.load()
                cur_pid = pid
                print(f'  {tag}  attached pid={pid} (RSS {rss//1024}MB) in {time.time()-ta:.1f}s',
                      flush=True)
            except Exception as e:
                print(f'  {tag}  attach pid={pid} failed after {time.time()-ta:.1f}s: {e!r} '
                      f'→ CfT + --no-sandbox?', flush=True)
                sess = sc = cur_pid = None
                time.sleep(1.0); continue
        tp = time.time()
        try:
            res = patch_with_timeout(sc, 25)
        except Exception as e:
            print(f'  {tag}  patch failed (renderer gone?): {e!r}', flush=True)
            sess = sc = cur_pid = None
            continue
        if res == 'TIMEOUT':
            print(f'  {tag}  scan TIMED OUT (>25s) — a range read wedged; detaching + reattaching',
                  flush=True)
            try: sess.detach()
            except Exception: pass
            sess = sc = cur_pid = None
            time.sleep(0.5)
            continue
        dt = time.time() - tp
        total_changed += res['changed']
        _sh = res.get('shared_hex') or ''
        _sh_full = None
        if not _sh:
            _shtag = 'sh=?'                     # couldn't read winBase+1108480 (no winner yet)
        elif set(_sh) == {'0'}:
            _shtag = 'sh=ZERO(not-derived)'    # good: game hasn't derived shared yet — patch is in time
        else:
            _shtag = 'sh=' + _sh[:16]          # compare vs mock's [fg5] expected shared: equal=win, diff=too-late
            _sh_full = _sh
        st = f'{res["cands"]}cand/{res["scanned_kb"]}KB/{dt:.2f}s {_shtag}'
        if res['changed']:
            print(f'  {tag}  pid={cur_pid} orig={res["orig_hits"]} new_present={res["new_present"]} '
                  f'changed={res["changed"]} fails={res["fails"]} {st}  [{res["method"]}]   ★ patched',
                  flush=True)
        elif res['fails']:
            print(f'  {tag}  pid={cur_pid} orig_hits={res["orig_hits"]} changed=0 '
                  f'fails={res["fails"]} {st}\n      diag: {res["diag"]}', flush=True)
        elif res['new_present']:
            print(f'  {tag}  pid={cur_pid} new_present={res["new_present"]} {st}  '
                  f'(mock pub in place ✓ — RELOAD now)', flush=True)
        else:
            print(f'  {tag}  pid={cur_pid} no chunks at +1048576 {st}  '
                  f'(wasm not loaded, or base != linear 0)', flush=True)
        if _sh_full and _sh_full != last_printed_sh:
            # Full 64-hex only when the derived shared first appears / changes — diff it against the
            # mock's "[fg5] expected shared". Equal ⇒ this handshake's crypto USED the mock pub (proof
            # the 8 patched bytes entered X25519); different ⇒ real pub was used (patch lost the race).
            print(f'        shared@1108480 (game-derived) = {_sh_full}', flush=True)
            last_printed_sh = _sh_full
        if FIX_SHARED and cur_pid:
            _hx = ''
            try:
                _hx = open(SHARED_FILE).read().strip()
            except Exception:
                pass
            if len(_hx) == 64:
                try:
                    fr = sc.exports_sync.fixshared(list(bytes.fromhex(_hx)))
                except Exception as e:
                    fr = {'ok': False, 'reason': repr(e)}
                if fr.get('ok') and fr.get('method') and fr.get('method') != 'already':
                    print(f'        FIX_SHARED @1108480 <- {_hx[:16]}…  '
                          f'(was {(fr.get("before") or "")[:16]}…)  [{fr.get("method")}]', flush=True)
                    # signal run.sh the patcher is armed (winBase known + shared overwrite works),
                    # so it can auto-reload the game to trigger a fresh (now-decryptable) handshake.
                    try:
                        open(os.environ.get('PATCH_READY_FILE', '/tmp/jili-patchwasm-ready'), 'w').close()
                    except Exception:
                        pass
        time.sleep(0.2)
    if sess:
        try: sess.detach()
        except Exception: pass
    print(f'[patchwasm] done — total chunk-writes {total_changed}. Watch the mock log for seq=2.')


if __name__ == '__main__':
    main()
