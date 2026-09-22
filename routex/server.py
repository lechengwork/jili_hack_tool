#!/usr/bin/env python3
"""Route X mock server for JILI game 696.

Serves the patched game front-end and impersonates the backend:
  GET  /fg5/            + static assets  -> games/696/static  (shared fallback)
  POST /sso-login.api                    -> JSON login (returns a token)
  POST /fg5/req                          -> encrypted protobuf response (fg5.py)
  GET  /                                 -> redirect into the game entry URL

The client's WASM has been patched (gen_and_patch.py) to trust OUR baked pubkeys,
so it accepts responses we sign/encrypt with the mock private keys in mockkeys.json.

Run:
  1. ../.venv/bin/python3 gen_and_patch.py        # once: mock keys + crypto.patched.wasm
  2. cp crypto.patched.wasm ../games/696/static/fg5/<path-to>/crypto.wasm   (see README)
  3. ../.venv/bin/python3 server.py                # PORT / HOST / TLS via env
Then open the URL it prints (accept the self-signed cert warning).
"""
import os, sys, json, ssl, datetime, mimetypes, hashlib, base64, time, threading
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# WebSocket (RFC 6455) — the keepalive channel /lifeservice/ws2. Captured protocol
# (games/696/traffic_raw.json, 38 frames): client sends ONE binary protobuf handshake
# frame, server replies with the single text frame {"error":0}; thereafter the client
# sends a JSON heartbeat {"cmdType":-1,...} every ~7s and the server NEVER replies. It's
# pure keepalive ("保活，非遊戲邏輯") — no crypto, no game logic. Without it the client
# can't open the life channel and bails out with "无法连接服务器 (MSG 999.1)".
WS_GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'


def ws_recv_frame(rfile):
    """Read one client->server frame (client frames are always masked). Returns
    (opcode, payload) or None on EOF. Fragmented messages (FIN=0) aren't reassembled —
    the handshake and heartbeats are each a single frame, so that's fine here."""
    hdr = rfile.read(2)
    if len(hdr) < 2:
        return None
    b1, b2 = hdr[0], hdr[1]
    opcode = b1 & 0x0f
    masked = b2 & 0x80
    ln = b2 & 0x7f
    if ln == 126:
        ln = int.from_bytes(rfile.read(2), 'big')
    elif ln == 127:
        ln = int.from_bytes(rfile.read(8), 'big')
    mask = rfile.read(4) if masked else b''
    data = rfile.read(ln) if ln else b''
    if masked:
        data = bytes(data[i] ^ mask[i % 4] for i in range(len(data)))
    return opcode, data


def ws_send_frame(wfile, opcode, payload=b''):
    """Send one server->client frame (unmasked, single-fragment)."""
    b1 = 0x80 | opcode
    n = len(payload)
    if n < 126:
        hdr = bytes([b1, n])
    elif n < 65536:
        hdr = bytes([b1, 126]) + n.to_bytes(2, 'big')
    else:
        hdr = bytes([b1, 127]) + n.to_bytes(8, 'big')
    wfile.write(hdr + payload)
    wfile.flush()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fg5

try:                                   # line-buffer logs so they show promptly when piped
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
# Front-end root: prefer the full captured mirror (game_site_backup — has fg5 + smallicon
# + astarte2 together), fall back to games/696/static. Override with STATIC=<dir>.
_BACKUP = os.path.abspath(os.path.join(HERE, '..', 'game_site_backup', 'uat-wbgame.jlfafafa3.com'))
_MINI = os.path.abspath(os.path.join(HERE, '..', 'games', '696', 'static'))
STATIC_ROOT = os.path.abspath(os.environ.get('STATIC') or (_BACKUP if os.path.isdir(_BACKUP) else _MINI))
SHARED_ROOT = os.path.abspath(os.path.join(HERE, '..', 'games', 'shared'))
RESPONSES = os.path.join(HERE, '..', 'games', '696', 'responses.jsonl')
VERBOSE = os.environ.get('VERBOSE', '0') != '0'   # log every request (use on first run)

PORT = int(os.environ.get('PORT', '8443'))
HOST = os.environ.get('HOST', 'localhost')          # bind address
# Hostname to show in the entry URL (and reverse into gs/be). The front-end is
# Jscrambler domain-locked, so it must be opened on an AUTHORISED domain, not
# localhost — map that domain to 127.0.0.1 in /etc/hosts and set URL_HOST to it.
URL_HOST = os.environ.get('URL_HOST', HOST)
TLS = os.environ.get('TLS', '1') != '0'
GAME_PATH = os.environ.get('GAME_PATH', '/fg5/')
# Two independent stalls (seconds). Load order is wasm-instantiate -> sso-login -> handshake, and
# the shared key is DERIVED at handshake-send (gated by sso completing) — the 2026-09-01 shared-oracle
# run proved the game derives from the REAL pub because the derive (≈sso_end) beat patchwasm's patch
# by ~1s (the reload patch-pass took 6.02s while sso stalled only 5s). So:
#   SSO_DELAY  = stall sso-login. This is the ONE that matters: it delays handshake-send/derive,
#                opening the window for patchwasm to overwrite the fresh wasm's pub BEFORE derive.
#                Make it comfortably longer than the worst-case patch-pass (~6s) — e.g. 12.
#   HS_DELAY   = stall the first handshake RESPONSE. Does NOT affect derive (derive already happened
#                at send); only risks a client-side response timeout. Keep 0 unless needed.
HS_DELAY = float(os.environ.get('HS_DELAY', '0'))
SSO_DELAY = float(os.environ.get('SSO_DELAY', str(HS_DELAY)))   # defaults to HS_DELAY (back-compat)
# FALLBACK: on every request we write the CORRECT shared (= X25519(mock_priv, client_pub), i.e. the
# AES key the game MUST use) to this file, so patchwasm can overwrite the game's @1108480 with it —
# bypassing the whole "did the pub patch beat the derive" race. Written BEFORE any response stall.
SHARED_HEX_PATH = os.environ.get('SHARED_HEX_PATH', os.path.join(HERE, 'mock_shared.hex'))

# crypto.wasm is fetched by the client at runtime from a remote URL and is NOT part
# of the static mirror, so we must intercept that request and hand back the *patched*
# wasm (baked pubs -> ours). CRYPTO_WASM = a path substring that identifies it; any
# .wasm whose URL contains it (default 'crypto') is served patched. On first run watch
# the [GET]/[404] logs for the real wasm path and set CRYPTO_WASM to match if needed.
PATCHED_WASM_PATH = os.path.join(HERE, 'crypto.patched.wasm')
ORIG_WASM_PATH = os.path.abspath(os.path.join(HERE, '..', 'games', '696', 'crypto.wasm'))
CRYPTO_WASM_MARK = os.environ.get('CRYPTO_WASM', 'crypto')


# ─── load mock keys + captured plaintexts ────────────────────────────────────

def load_keys():
    p = os.path.join(HERE, 'mockkeys.json')
    if not os.path.exists(p):
        sys.exit('[FATAL] mockkeys.json missing — run gen_and_patch.py first')
    return json.load(open(p))

KEYS = load_keys()
CRYPTO = fg5.Fg5Crypto(KEYS['x25519_priv'], KEYS['ed25519_priv'])

# 重播資料來源(可覆寫):
#   REPLAY=<exchanges_ordered.jsonl>  一整場 capture(含 raw);只要指到這份,init 序列 /
#     per-type 樣本 / spins 全從它推導 → 單檔即可重播整場(不需 responses/init_sequence)。
#   REPLAY_SPINS=<dir>  「每局一個 .json(含 raw)」目錄,只覆蓋 spin 序列(init 仍取自 EXCH)。
REPLAY_SPINS = os.environ.get('REPLAY_SPINS')
# 只播指定的幾局(逗號分隔;可給完整局號或片段)。★依你給的順序播★,不是檔名順序。
#   REPLAY_ROUNDS=24126-883680-00240696,24126-544640-00800696
REPLAY_ROUNDS = os.environ.get('REPLAY_ROUNDS')
EXCH_PATH = os.environ.get('REPLAY') or os.path.join(HERE, '..', 'games', '696', 'exchanges_ordered.jsonl')
_EXCH_ROWS = []
if os.path.exists(EXCH_PATH):
    _EXCH_ROWS = [json.loads(l) for l in open(EXCH_PATH) if l.strip()]

# Captured decrypted plaintexts, keyed by type. Value = the f4 game payload bytes.
# 優先 responses.jsonl;沒有就從 exchanges_ordered.jsonl 推導(每 type 第一筆 raw)。
SAMPLES = {}
if os.path.exists(RESPONSES):
    for line in open(RESPONSES):
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        SAMPLES.setdefault(o['type'], bytes(o.get('raw', o.get('data', []))))
if not SAMPLES and _EXCH_ROWS:
    for r in _EXCH_ROWS:
        if r.get('type') is not None and r.get('raw') is not None:
            SAMPLES.setdefault(r['type'], bytes(r['raw']))
print('[samples] captured decrypted types:', sorted(SAMPLES.keys()),
      '(payload lens:', {t: len(d) for t, d in sorted(SAMPLES.items())}, ')')

# Ordered gameplay replay (games/696/exchanges_ordered.jsonl, the FULL decrypted session).
# Fixes what a single per-type sample can't: (1) each spin is a DIFFERENT board, so cycle the
# recorded spin results instead of repeating one; (2) the balance CHANGES after a spin, so
# post-spin balance polls must return the post-spin value — otherwise the client sees the balance
# never update and won't enable the next spin (the "press spin, nothing happens" freeze).
SPIN_SAMPLES = []                 # ordered type-0 spin boards
BAL_PRE = SAMPLES.get(2, b'')     # balance before any spin (init default)
BAL_POST = b''                    # balance after a spin

def _load_spin_dir(d):
    """讀一個目錄的每局 json(每檔一個 spin,需含 'raw') → ([bytes], 檔數)。

    預設依檔名(=局號)排序;設了 REPLAY_ROUNDS 就只載那幾局,而且【依你給的順序】,
    方便直接跳到想看的那一局(例如饋贈或 Ex Nudge 連鎖)。
    """
    import glob
    files = sorted(glob.glob(os.path.join(d, '*.json')))
    if REPLAY_ROUNDS:
        want = [x.strip() for x in REPLAY_ROUNDS.split(',') if x.strip()]
        picked, missing = [], []
        for w in want:
            hit = [f for f in files if w in os.path.basename(f)]
            if hit:
                picked.extend(hit)
            else:
                missing.append(w)
        if missing:
            print(f'[replay] ⚠ REPLAY_ROUNDS 找不到:{", ".join(missing)}')
        if picked:
            print(f'[replay] ★只播指定的 {len(picked)} 局★(依你給的順序):')
            for f in picked:
                print(f'           {os.path.basename(f)[:-5]}')
            files = picked
        else:
            print('[replay] ⚠ REPLAY_ROUNDS 一局都沒對上,改播全部')
    out = []
    for fp in files:
        try:
            o = json.load(open(fp, encoding='utf-8'))
        except Exception:
            continue
        if o.get('raw'):              # 只有含 raw 的檔能重播;純報表檔(無 raw)略過
            out.append(bytes(o['raw']))
    return out, len(files)

if REPLAY_SPINS and os.path.isdir(REPLAY_SPINS):
    SPIN_SAMPLES, _nfiles = _load_spin_dir(REPLAY_SPINS)
    _skipped = _nfiles - len(SPIN_SAMPLES)
    print(f'[replay] 每局目錄 {REPLAY_SPINS}: 載入 {len(SPIN_SAMPLES)}/{_nfiles} 局'
          + (f' (⚠ {_skipped} 個檔沒有 raw 欄位=純報表,無法重播;需以新版 capture 重抓)' if _skipped else ''))
else:
    SPIN_SAMPLES = [bytes(r['raw']) for r in _EXCH_ROWS
                    if r.get('kind') == 'spin' and r.get('type') == 0 and r.get('raw')]
# 第一個 spin 之後的第一筆 balance poll = 後餘額(兩種 spin 來源都適用)
_seen_spin = False
for r in _EXCH_ROWS:
    if r.get('kind') == 'spin':
        _seen_spin = True
    elif _seen_spin and r.get('type') == 2 and r.get('raw'):
        BAL_POST = bytes(r['raw']); break
if not SPIN_SAMPLES and SAMPLES.get(0):
    SPIN_SAMPLES = [SAMPLES[0]]    # fall back to the single per-type sample
if not BAL_POST:
    BAL_POST = BAL_PRE
print(f'[replay] {len(SPIN_SAMPLES)} spin board(s); balance pre={len(BAL_PRE)}B post={len(BAL_POST)}B')

# Ordered init/handshake response sequence (games/696/init_sequence.jsonl, produced by
# decrypting a real capture). The game's init is a SCRIPTED sequence: the same-shaped
# request (e.g. an empty keepalive) gets a DIFFERENT typed response depending on its
# position, so we replay by order — the Nth non-spin request of a session gets the Nth
# entry here — rather than by request shape. Each entry = {type, ret, raw}.
INIT_SEQ_PATH = os.path.join(HERE, '..', 'games', '696', 'init_sequence.jsonl')
INIT_SEQ = []
if os.path.exists(INIT_SEQ_PATH):
    for line in open(INIT_SEQ_PATH):
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        INIT_SEQ.append((o['type'], o.get('ret', 0), bytes(o.get('raw', []))))
if not INIT_SEQ and _EXCH_ROWS:            # 沒有 init_sequence.jsonl → 取 exchanges「第一個 spin 前」的前綴
    for r in _EXCH_ROWS:
        if r.get('kind') == 'spin':
            break
        INIT_SEQ.append((r.get('type'), r.get('ret', 0), bytes(r.get('raw') or [])))
print(f'[initseq] {len(INIT_SEQ)} ordered init responses '
      f'(types: {[t for t, _, _ in INIT_SEQ]})')

# Runtime crypto.wasm keypatch shim (wasm_patch_shim.js). The crypto wasm is built at
# runtime from the bundles (not a static .wasm we can swap on the wire), so we instead
# inject this <script> at the top of the served fg5 HTML; it hooks WebAssembly.instantiate/
# compile and rewrites the two baked server pubkeys to ours before the module is built.
# DISABLED BY DEFAULT: injecting a WebAssembly.instantiate hook trips the bundle's
# Jscrambler self-defense (it reads WebAssembly.*.toString() while decoding, and a wrapped
# function breaks that -> "Invalid or unexpected token" in index.22de5.js -> stuck at load).
# The crypto wasm's baked pubs are instead patched in WASM linear memory at runtime via
# Frida (patchwasm.py), which never touches JS. Set INJECT_SHIM=1 only to experiment.
WASM_SHIM_PATH = os.path.join(HERE, 'wasm_patch_shim.js')
WASM_SHIM = ''
# INJECT_BUNDLE=1: prepend the shim INTO an existing JS bundle (default polyfills.bundle) instead of
# adding a new <script> to the HTML. HTML stays byte-identical, DOM/script structure unchanged —
# tests whether "modify existing carrier" evades the injection/HTML-integrity check that kills a new <script>.
INJECT_BUNDLE = os.environ.get('INJECT_BUNDLE') == '1'
BUNDLE_TARGET = os.environ.get('BUNDLE_TARGET', 'polyfills.bundle')
# CANARY_TARGET: 獨立於主 shim 的「探針」——往「path 含此字串的 .js」內容前面塞一句無害 beacon,
# 用來測「改某個 bundle(尤其是 Jscrambler 保護的 index.22de5.js)的內容會不會觸發自毀」。空=關。
CANARY_TARGET = os.environ.get('CANARY_TARGET', '')
if (os.environ.get('INJECT_SHIM') == '1' or INJECT_BUNDLE) and os.path.exists(WASM_SHIM_PATH):
    WASM_SHIM = open(WASM_SHIM_PATH).read()
    if INJECT_BUNDLE:
        print(f'[shim] shim loaded ({len(WASM_SHIM)}B) — BUNDLE-prepend into "{BUNDLE_TARGET}" (HTML unchanged, no new <script>)')
    else:
        print(f'[shim] wasm-keypatch shim INJECTION ENABLED ({len(WASM_SHIM)}B) — HTML <head> inject — may break Jscrambler')
else:
    print('[shim] shim injection OFF (patch the wasm in memory via patchwasm.py instead)')

# ─── CAPTURE mode ─────────────────────────────────────────────────────────────
# CAPTURE=1 (with INJECT_BUNDLE=1): web-based packet capture against the REAL server —
# no Frida, no netlog. Instead of the pubkey-patch shim we prepend capture_shim.js, which
# hooks fetch to side-log every /fg5/req request+response and reads the session AES key
# (X25519 shared @linear 1108480) straight out of the crypto-wasm memory, POSTing both to
# /__capture__. We DON'T patch pubkeys (we want the game to derive the REAL shared and talk
# to the REAL server). REQUIRES a SPLIT /etc/hosts: ONLY the document host -> 127.0.0.1
# (we serve static + shim); the api hosts (be/gs) must resolve to the REAL server over VPN.
# Collect with webcapture.sh, decode afterwards with webcapture_finish.sh (decrypt_capture.py).
CAPTURE = os.environ.get('CAPTURE') == '1'
CAPTURE_SHIM_PATH = os.path.join(HERE, 'capture_shim.js')
GRAB_PATH = os.environ.get('GRAB', '/tmp/jili_grab.json')
CAP_EXCH_PATH = os.environ.get('CAP_OUT', os.path.join(HERE, '..', 'games', '696', 'webcap_exchanges.jsonl'))
GRV_PATH = os.environ.get('GRV_OUT', os.path.join(HERE, '..', 'games', '696', 'webcap_grv.jsonl'))
_cap_lock = threading.Lock()
_cap_count = 0
_grv_seen = set()
_cap_key = None            # cached AES-256 session key once known (from wasm mem, or grv fallback)
_cap_grv = []              # accumulated getRandomValues priv candidates (fallback key derivation)
LIVE_DECODE = os.environ.get('LIVE_DECODE', '1') == '1'   # decode+print each captured spin immediately
# One JSON file per spin, named by round_id (局號) — for the probability team.
# round_id is monotonic (fixed-width, zero-padded) so files sort in play order; each file
# also carries 'idx' (capture seq) as a guaranteed-ordered tiebreaker. Dir override: SPIN_OUT.
SPIN_JSON = os.environ.get('SPIN_JSON', '1') == '1'
SPIN_DIR = os.environ.get('SPIN_OUT') or os.path.join(os.path.dirname(CAP_EXCH_PATH), 'webcap', 'spins')
SPIN_RAW_DIR = os.environ.get('SPIN_RAW_OUT') or os.path.join(os.path.dirname(CAP_EXCH_PATH), 'webcap', 'spins_raw')
# 明文一局檔(★機率即時看的):backend_raw/spins/<局號>.json,含 payload_hex/payload_named 等
BR_SPIN_DIR = os.environ.get('BR_SPIN_OUT') or os.path.join(os.path.dirname(CAP_EXCH_PATH), 'webcap', 'backend_raw', 'spins')
# ★機率介面一局檔:games/<gid>/math/<局號>.json(math_696.proto 形狀,全 int、沒有密文欄位)
MATH_SPIN_DIR = os.environ.get('MATH_OUT') or os.path.join(os.path.dirname(CAP_EXCH_PATH), 'math')
# 主控台每局要印什麼:預設印機率視圖;LIVE_RAW=1 才印工程用的 payload_hex + payload_named
LIVE_RAW = os.environ.get('LIVE_RAW', '0') == '1'
# shim 說它抓到了(GET 信標,不受配額限制) vs 資料真的送達(POST)。兩者一旦拉開,
# 代表 beacon 被瀏覽器丟掉、那幾局【永遠不會有資料】—— 必須當場吵,不能靜默。
_seq_reported = [0]
_seq_received = [0]

import pwd as _pwd   # SUDO_USER uid 查詢(chown-back)
def _chown_back(path):
    """跑在 sudo(root)下時,把 path 擁有者改回原使用者(SUDO_USER),讓非 sudo 的
    webcapture_finish.sh 能寫入 webcap/。非 root / 無 SUDO_USER / 失敗都靜默 no-op。"""
    try:
        if not hasattr(os, 'geteuid') or os.geteuid() != 0:
            return
        su = os.environ.get('SUDO_USER')
        if not su:
            return
        pw = _pwd.getpwnam(su)
        os.chown(path, pw.pw_uid, pw.pw_gid)
    except Exception:
        pass
# 每局檔(spins/ 純分析 + spins_raw/ 含raw)的寫入由 webcap_pretty.write_spin_pair 統一處理,見 _live_decode。

# ─── live decode: decrypt + prettify ONE captured exchange for immediate console print ───
_DECMOD = None
_PRETTYMOD = None
_BRMOD = None
_MVMOD = None
def _dec_mods():
    """Lazy-import the offline decoder (routex/decrypt_capture.py) + prettifier
    (../webcap_pretty.py). Imported on first spin so a non-capture run pays nothing."""
    global _DECMOD, _PRETTYMOD, _BRMOD, _MVMOD
    if _DECMOD is None:
        import decrypt_capture as _dc
        _parent = os.path.dirname(HERE)
        if _parent not in sys.path:
            sys.path.insert(0, _parent)
        import webcap_pretty as _wp
        import webcap_backend_raw as _br
        import webcap_math_view as _mv          # 機率介面視圖(內含 math_adapter 雙向轉換)
        _DECMOD, _PRETTYMOD, _BRMOD, _MVMOD = _dc, _wp, _br, _mv
    return _DECMOD, _PRETTYMOD, _BRMOD, _MVMOD

def _set_cap_key(k):
    """shim 有時是【單獨一筆】只送 key(沒有 resp_body_hex),那筆不會進 _live_decode,
    以前就會導致 _cap_key 永遠是 None、整場即時解碼靜靜不動(封包還是有存,只是不即時解)。
    所以 key 一到就先收下。2026-09-21 修。"""
    global _cap_key
    if _cap_key is None and k:
        try:
            _cap_key = bytes.fromhex(k)
            print(f'  ★ [capture] session key 收到({len(_cap_key)}B)，之後每局即時解碼')
        except Exception:
            _cap_key = None


def _live_decode(rec):
    """Decrypt + prettify one captured /fg5/req exchange RIGHT NOW -> printable string.
    Returns None if the session key isn't known yet (packet is still saved for batch decode)."""
    global _cap_key
    dc, wp, br, mv = _dec_mods()
    if _cap_key is None:                       # (1) key straight from wasm mem (shim sends it once)
        k = rec.get('key')
        if k:
            try: _cap_key = bytes.fromhex(k)
            except Exception: _cap_key = None
    if _cap_key is None and _cap_grv:          # (2) fallback: derive from a getRandomValues priv
        try:
            f4 = fg5.parse_fields(bytes.fromhex(rec.get('req_body_hex') or '')).get(4)
            if isinstance(f4, (bytes, bytearray)):
                priv = dc.find_priv(_cap_grv, bytes(f4))
                if priv: _cap_key = dc.shared_key(priv)
        except Exception:
            pass
    if _cap_key is None:
        return None
    try:
        d = dc.decrypt_response(bytes.fromhex(rec.get('resp_body_hex') or ''), _cap_key, verify_sig=True)
    except Exception as e:
        return ('  ⚠ [decode] seq=%s 解密失敗: %r '
                '(這把 key 對得上 THIS capture 嗎?)' % (rec.get('seq'), e))
    pretty = wp.prettify({'type': d['type'], 'ret': d['ret'], 'len': d['len'],
                          'raw': d['raw'], 'idx': rec.get('seq')})
    # ── 組「後端原封不動封包(明文)」一局檔,和 backend_raw(finish 版)同格式 ──
    pt = bytes.fromhex(d.get('pt_hex') or '')
    env, payload_b, typ, _ret, _err, tim_ = br.split_envelope(pt)
    rid = pretty.get('round_id')
    named = (br.decode_named(payload_b, br._TYPE_ROOT[typ])
             if (typ in br._TYPE_ROOT and payload_b) else None)
    rec_br = {
        'idx': rec.get('seq'), 'seq': rec.get('seq'), 'type': typ, 'ret': d['ret'],
        'round_id': rid, 'sig_ok': d['_sig_ok'], 'server_time': tim_,
        'response_wire_hex': rec.get('resp_body_hex'),
        'plaintext_hex': pt.hex(),                 # 完整 Envelope 明文
        'payload_hex': payload_b.hex(),            # f5 = SpinResult(重播單位)
        'envelope_fields': env,
        'payload_decoded': d.get('decoded'),
        'payload_named': named,                    # ★套 proto 名字(逆向解讀)
    }
    if SPIN_JSON and pretty.get('kind') == 'spin' and rid:
        try:
            os.makedirs(BR_SPIN_DIR, exist_ok=True)               # (a) ★明文一局檔:即時給機率看
            _bp = os.path.join(BR_SPIN_DIR, str(rid).replace('/', '_') + '.json')
            with open(_bp, 'w', encoding='utf-8') as _f:
                json.dump(rec_br, _f, ensure_ascii=False, indent=2)
            _chown_back(_bp)
            for _wf in wp.write_spin_pair(pretty, d['raw'], SPIN_DIR, SPIN_RAW_DIR):  # (b) spins_raw 供回放
                _chown_back(_wf)
            if typ == 0 and payload_b:                                # (c) ★機率介面一局檔
                os.makedirs(MATH_SPIN_DIR, exist_ok=True)
                _mp = os.path.join(MATH_SPIN_DIR, str(rid).replace('/', '_') + '.json')
                with open(_mp, 'w', encoding='utf-8') as _f:
                    _f.write(mv.dumps(mv.build_envelope(payload_b)) + '\n')
                _chown_back(_mp); _chown_back(MATH_SPIN_DIR)
            for _wd in (BR_SPIN_DIR, os.path.dirname(BR_SPIN_DIR),
                        SPIN_DIR, SPIN_RAW_DIR, os.path.dirname(SPIN_DIR)):
                _chown_back(_wd)                                  # 連目錄,好讓 finish 寫得進
        except Exception as e:
            print(f'  ⚠ [spin-json] 寫檔失敗: {e!r}')
    # ── 主控台:spin 印【機率介面】(輸入 spinReq / 輸出 data,沒有密文欄位、沒有 _message);
    #    其餘 type 與 LIVE_RAW=1 時,才印工程用的 payload_hex + payload_named ──
    if typ == 0 and payload_b and not LIVE_RAW:
        try:
            _env = mv.build_envelope(payload_b)
            body = '\n'.join('    ' + ln for ln in mv.dumps(_env).splitlines())
        except Exception as e:
            body = '    ⚠ 機率視圖轉換失敗: %r\n    payload_hex : %s' % (e, rec_br['payload_hex'])
    else:
        lines = ['    payload_hex : ' + rec_br['payload_hex']]
        if named is not None:
            lines.append('    payload_named:')
            lines += ['    ' + ln for ln in json.dumps(named, ensure_ascii=False, indent=2).splitlines()]
        body = '\n'.join(lines)
    head = ('  ┌── [decode] seq=%s  type=%s (%s)  round=%s  ret=%s  sig_ok=%s ──'
            % (rec.get('seq'), d['type'], pretty.get('kind', '?'), rid, d['ret'], d['_sig_ok']))
    return head + '\n' + body + '\n  └' + '─' * 44
if CAPTURE:
    if not INJECT_BUNDLE:
        print('[capture] ⚠ CAPTURE=1 needs INJECT_BUNDLE=1 (the capture shim rides in polyfills.bundle) — disabling capture')
        CAPTURE = False
    elif not os.path.exists(CAPTURE_SHIM_PATH):
        print(f'[capture] ⚠ capture_shim.js missing at {CAPTURE_SHIM_PATH} — disabling capture')
        CAPTURE = False
    else:
        try:
            _orig0 = list(bytes.fromhex(json.load(open(os.path.join(HERE, 'wasm_pub_patches.json')))[0]['orig']))
        except Exception as _e:
            _orig0 = []
            print(f'[capture] ⚠ could not load ORIG0 anchor from wasm_pub_patches.json ({_e!r}) — key grab will not fire')
        WASM_SHIM = open(CAPTURE_SHIM_PATH).read().replace('__ORIG0__', json.dumps(_orig0))
        try:
            os.remove(CAP_EXCH_PATH)            # fresh file per capture run
        except OSError:
            pass
        try:
            os.remove(GRAB_PATH)               # fresh key per capture run
        except OSError:
            pass
        try:
            os.remove(GRV_PATH)                 # fresh getRandomValues log per capture run
        except OSError:
            pass
        print(f'[capture] ★ CAPTURE MODE — capture-shim into "{BUNDLE_TARGET}"; exchanges -> {CAP_EXCH_PATH}')
        print(f'[capture] ★ key -> {GRAB_PATH} (from wasm mem);  getRandomValues -> {GRV_PATH} (priv fallback)')
        print('[capture] ★ REQUIRES split /etc/hosts: ONLY document host -> 127.0.0.1; api hosts (be/gs) = REAL server (VPN).')

# DLPROBE=1: Jscrambler Domain-Lock 破解 PoC — 在 mock patch shim 之前再 prepend 一段
# location 網域偽裝 shim(routex/dl_probe_shim.js),讓 22de5 讀 location 時看到 jili 網域。
# 只在 mock 模式(INJECT_BUNDLE=1、非 CAPTURE、patch shim 已載入 WASM_SHIM)有意義。
# ERRPROBE=1: 把前端未接住的 JS 錯誤送回本 server 的 log(POST /__err__)。
# 用在「畫面卡住但沒有任何後續請求」= 前端在 JS 裡爆掉的情境,取代不能開的 DevTools。
ERRPROBE = os.environ.get('ERRPROBE') == '1'
ERR_PROBE_SHIM_PATH = os.path.join(HERE, 'err_probe_shim.js')

DLPROBE = os.environ.get('DLPROBE') == '1'
DL_PROBE_SHIM_PATH = os.path.join(HERE, 'dl_probe_shim.js')
if DLPROBE:
    if not (INJECT_BUNDLE and not CAPTURE and WASM_SHIM):
        print('[dlprobe] ⚠ DLPROBE 需要 mock 模式(INJECT_BUNDLE=1、無 CAPTURE、patch shim 已載)— 已略過')
    elif not os.path.exists(DL_PROBE_SHIM_PATH):
        print(f'[dlprobe] ⚠ 找不到 {DL_PROBE_SHIM_PATH} — 已略過')
    else:
        _probe = open(DL_PROBE_SHIM_PATH).read()
        WASM_SHIM = _probe + '\n;\n' + WASM_SHIM     # 偽裝先跑,再跑 pubkey patch
        print(f'[dlprobe] ★ domain-lock 探路 shim 已 prepend 到 patch shim 前 ({len(_probe)}B)。看 [shim-report] DLPROBE OK/FAIL。')

if ERRPROBE:
    if not INJECT_BUNDLE:
        print('[errprobe] ⚠ 需要 INJECT_BUNDLE=1 才注得進去 — 已略過')
    elif not os.path.exists(ERR_PROBE_SHIM_PATH):
        print(f'[errprobe] ⚠ 找不到 {ERR_PROBE_SHIM_PATH} — 已略過')
    else:
        _ep = open(ERR_PROBE_SHIM_PATH).read()
        WASM_SHIM = _ep + '\n;\n' + (WASM_SHIM or '')
        print(f'[errprobe] ★ JS 錯誤回報 shim 已注入 ({len(_ep)}B)。前端爆掉會印 [jserr]。')

# EXTRA_SHIM=<path>:把任一 shim 檔的內容 prepend 到 polyfills(在 WASM_SHIM 最前面)。通用診斷用
# (如 sjl_trace_shim.js 定位 domain-lock 檢查點)。需 INJECT_BUNDLE=1。
_extra = os.environ.get('EXTRA_SHIM', '')
if _extra:
    _ep = _extra if os.path.isabs(_extra) else os.path.join(HERE, os.path.basename(_extra))
    if not (INJECT_BUNDLE and WASM_SHIM):
        print('[extra] ⚠ EXTRA_SHIM 需要 INJECT_BUNDLE=1(patch shim 已載)— 已略過')
    elif not os.path.exists(_ep):
        print(f'[extra] ⚠ 找不到 EXTRA_SHIM {_ep} — 已略過')
    else:
        _es = open(_ep).read()
        WASM_SHIM = _es + '\n;\n' + WASM_SHIM
        print(f'[extra] ★ EXTRA_SHIM 已 prepend 到最前 ({os.path.basename(_ep)}, {len(_es)}B)')

# Patched wasm bytes (from gen_and_patch.py) + the original (to swap by content if it
# ever appears in the static tree under any name).
PATCHED_WASM = open(PATCHED_WASM_PATH, 'rb').read() if os.path.exists(PATCHED_WASM_PATH) else None
ORIG_WASM = open(ORIG_WASM_PATH, 'rb').read() if os.path.exists(ORIG_WASM_PATH) else None
if PATCHED_WASM is None:
    print('[warn] crypto.patched.wasm missing — run gen_and_patch.py; wasm swap disabled')
else:
    print(f'[wasm] will serve patched crypto.wasm ({len(PATCHED_WASM)}B) for any *.wasm '
          f'path containing {CRYPTO_WASM_MARK!r}')


def classify(req):
    """Label a request by its f2 (action) field shape — matches the shapes seen in
    fg5_exchanges.json (39 captured live requests). Returns a short kind string.

        spin       f2 = { f1:f64 bet, f25:opts [, f26:ante] }   (req 76/81B)
        handshake  f2 = { f1,f2,f3,f4,f5 device/locale info }    (req 120B)
        setlang    f2 = { f1:str }                               (req 67B)
        poll       f2 = { f1:str, f2:varint }                    (req 69B)
        status     f2 = { f1:varint }                            (req 62B)
        keepalive  f2 = {} (empty)                               (req 58B)
    """
    action = req['action']
    try:
        af = fg5.parse_fields(action) if action else {}
    except Exception:
        af = {}
    f1 = af.get(1)
    if isinstance(f1, (bytes, bytearray)) and len(f1) == 8:
        return 'spin', af          # f2.f1 = 8-byte f64 bet
    if not af:
        return 'keepalive', af
    if 3 in af and 5 in af:
        return 'handshake', af      # device/locale block
    if isinstance(f1, (bytes, bytearray)) and 2 in af:
        return 'poll', af
    if isinstance(f1, (bytes, bytearray)):
        return 'setlang', af
    if isinstance(f1, int):
        return 'status', af
    return 'unknown', af


# Steady-state (post-init) fallback: spins get a real spin sample; balance polls get a
# balance; anything else gets an empty ack. Only used once INIT_SEQ is exhausted.
import threading
_SEQ_LOCK = threading.Lock()
# Single-player local mock -> GLOBAL gameplay state (NOT keyed by client_pub: the game rotates
# its ephemeral pub between phases — handshake / init / spin all use different cp — so a per-cp
# counter would restart the init walk when the post-spin poll arrives under a new cp and replay
# init data instead of a balance, freezing the game).
_GAME = {'hs_cp': b'', 'init_pos': 0, 'spin_idx': 0, 'after_spin': False}
STEADY_ACK = 25        # empty {type:25} ack

# ── round_id bump ─────────────────────────────────────────────────────────────
# 重播同一局(或循環少數幾局)時,原封 board 的 round_id(SpinResult 欄位20)會重複,前端
# 認定「非遞增/重複局號」→ 第二把 spin 就卡死。這裡在每次發 spin 前,把欄位20改成嚴格
# 遞增值(board 其餘內容一字不動;末3碼=gameID 保留)。多局照順序播時本來就遞增 → 原值直用。
# 設 NO_RID_BUMP=1 可關掉(回到原封 bytes)。
_NO_RID_BUMP = bool(os.environ.get('NO_RID_BUMP'))
_RID = {'last': 0}

def _rid_read_varint(b, i):
    shift = 0; val = 0
    while True:
        x = b[i]; i += 1; val |= (x & 0x7f) << shift
        if not (x & 0x80): break
        shift += 7
    return val, i

def _rid_enc_varint(v):
    out = bytearray()
    while True:
        byte = v & 0x7f; v >>= 7
        out.append(byte | 0x80 if v else byte)
        if not v: break
    return bytes(out)

def _rid_find_f20(b):
    """回傳頂層欄位20(round_id, wiretype0)的 (值起, 值迄, 值);找不到=None。"""
    i = 0; n = len(b)
    while i < n:
        tag, j = _rid_read_varint(b, i); f = tag >> 3; wt = tag & 7
        if f == 20 and wt == 0:
            v, k = _rid_read_varint(b, j); return j, k, v
        if wt == 0: _, j = _rid_read_varint(b, j)
        elif wt == 1: j += 8
        elif wt == 2: ln, j = _rid_read_varint(b, j); j += ln
        elif wt == 5: j += 4
        else: return None
        i = j
    return None

def _bump_rid(board):
    """發 spin 前改寫 round_id 為嚴格遞增值。回傳 (新board, 生效的round_id 或 None)。"""
    if _NO_RID_BUMP or not board:
        return board, None
    span = _rid_find_f20(board)
    if not span:
        return board, None
    vs, ve, rid = span
    last = _RID['last']
    new = rid if rid > last else (last // 1000 + 1) * 1000 + (rid % 1000)  # 保留末3碼、嚴格遞增
    _RID['last'] = new
    if new == rid:
        return board, rid
    return board[:vs] + _rid_enc_varint(new) + board[ve:], new

# ── 回放時把每 spin 印成完整【機率介面】(和 capture 的 [decode] 同一個 formatter) ──
# capture 是解真站回應後印;回放我們手上就是明文 board,直接套 webcap_math_view.build_envelope。
# 設 REPLAY_LOG=0 可關掉(只留精簡的 spin[idx] rid=… 行)。
_REPLAY_LOG = os.environ.get('REPLAY_LOG', '1') == '1'

def _replay_spin_print(idx, board, rid):
    if CAPTURE or not _REPLAY_LOG or not board:
        return
    try:
        _, _, _, mv = _dec_mods()
        env = mv.build_envelope(board)
        body = '\n'.join('    ' + ln for ln in mv.dumps(env).splitlines())
    except Exception as e:
        body = '    ⚠ 機率視圖轉換失敗: %r' % (e,)
    head = '  ┌── [replay] spin[%s]  type=0 (spin)  round=%s  ret=0 ──' % (idx, rid)
    print(head + '\n' + body + '\n  └' + '─' * 44, flush=True)


def pick_response(req):
    """Choose (type, data, ret, label).

    handshake  -> config (type 1) ALWAYS, on every retry; never consumes the init sequence
                  (the client re-sends the 120B handshake until satisfied).
    spin       -> the NEXT recorded spin board (cycles SPIN_SAMPLES), and flips the balance to
                  its post-spin value so the game will enable the following spin.
    everything else -> walk the NON-handshake init responses in order once (global), then
                  steady-state: balance polls return pre/post-spin balance, others get an ack.
    """
    kind, _ = classify(req)
    if kind == 'handshake':
        cp = bytes(req['client_pub']) if isinstance(req.get('client_pub'), (bytes, bytearray)) else b''
        with _SEQ_LOCK:
            if cp and cp != _GAME['hs_cp']:     # new page load — handshake cp is stable within one
                _GAME.update(hs_cp=cp, init_pos=0, spin_idx=0, after_spin=False)  # load, changes across
        if INIT_SEQ:
            t, ret, raw = INIT_SEQ[0]           # ex0 = the real 223B config
        else:
            t, ret, raw = 1, 0, SAMPLES.get(1, b'')
        return t, raw, ret, 'handshake'
    if kind == 'spin':
        with _SEQ_LOCK:
            if SPIN_SAMPLES:
                board = SPIN_SAMPLES[_GAME['spin_idx'] % len(SPIN_SAMPLES)]
                idx = _GAME['spin_idx'] % len(SPIN_SAMPLES)
                _GAME['spin_idx'] += 1
            else:
                board, idx = SAMPLES.get(0, b''), 0
            board, rid = _bump_rid(board)   # 每把改寫 round_id 為嚴格遞增(重播同局才不會第二把卡死)
            _GAME['after_spin'] = True
        _replay_spin_print(idx, board, rid)   # 印完整機率介面(同 capture 格式)
        return 0, board, 0, f'spin[{idx}]' + (f' rid={rid}' if rid else '')
    with _SEQ_LOCK:
        pos = _GAME['init_pos']
        post_hs = INIT_SEQ[1:]               # init responses after the handshake/config
        if pos < len(post_hs):
            _GAME['init_pos'] += 1
            t, ret, raw = post_hs[pos]
            return t, raw, ret, f'init[{pos+1}]'
        after = _GAME['after_spin']
    if kind == 'poll':
        return 2, (BAL_POST if after else BAL_PRE), 0, 'poll' + ('*' if after else '')
    if STEADY_ACK in SAMPLES:
        return STEADY_ACK, SAMPLES[STEADY_ACK], 0, kind
    return 0, b'', 0, kind


# ─── static file serving ─────────────────────────────────────────────────────

def resolve_static(path):
    rel = path.lstrip('/')
    for root in (STATIC_ROOT, SHARED_ROOT):
        fp = os.path.abspath(os.path.join(root, rel))
        if not fp.startswith(root):        # path traversal guard
            continue
        if os.path.isdir(fp):
            fp = os.path.join(fp, 'index.html')
        if os.path.isfile(fp):
            return fp
    return None


def origin_fetch_and_cache(path):
    """Mirror gap-filler. A `/fg5/` (or astarte2/smallicon) static asset that is missing
    locally — most commonly a texture in a compressed format THIS browser wants but our
    mirror only captured another (ASTC on Apple GPUs vs WebP on Windows/others) — is
    fetched from the REAL asset origin and cached into the mirror, so the Cocos loader
    doesn't wedge on a 404. Returns (bytes, ctype) or None.

    Requires the origin to be reachable (webcapture: split /etc/hosts so the CDN/gs host
    is the REAL server over the BR VPN; the doc host stays local for shim injection).
    Origin defaults to the gs/CDN host (GS_HOST); override with ASSET_ORIGIN=host[:port].
    Turn the whole thing off with ASSET_FALLBACK=0.
    """
    if os.environ.get('ASSET_FALLBACK', '0') != '1':
        return None                                   # opt-in (ASSET_FALLBACK=1); off by default
    rel = path.lstrip('/')
    if not (rel.startswith('fg5/') or rel.startswith('astarte2/') or rel.startswith('smallicon/')):
        return None                                   # never proxy api/telemetry/etc.
    import urllib.request
    # try each candidate origin in order; first 200 wins. ASSET_ORIGIN (if set) first,
    # then the gs/CDN host (real in a split-hosts capture).
    origins = [o for o in (os.environ.get('ASSET_ORIGIN'), GS_HOST) if o]
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for origin in origins:
        url = f'https://{origin}/{rel}'
        try:
            req = urllib.request.Request(url, headers={'X-Mock-Fallback': '1',
                                                       'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
                if getattr(r, 'status', 200) != 200:
                    continue
                data = r.read()
        except Exception as e:
            print(f'  ⚠ [asset-fallback] {url} -> {e!r}')
            continue
        try:                                          # cache into the mirror (offline next time)
            dest = os.path.abspath(os.path.join(STATIC_ROOT, rel))
            if dest.startswith(STATIC_ROOT):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, 'wb') as f:
                    f.write(data)
        except Exception as e:
            print(f'  ⚠ [asset-fallback] cache write failed: {e!r}')
        ctype = mimetypes.guess_type(rel)[0] or 'application/octet-stream'
        if rel.endswith('.wasm'):
            ctype = 'application/wasm'
        print(f'  ↩ [asset-fallback] {len(data)}B from {origin} -> cached {rel}')
        return data, ctype
    return None


def reverse(s):
    return s[::-1]


def display_host():
    """Host[:port] for the entry URL; omit the port when it is the scheme default
    (so location.host is the bare domain the Jscrambler domain-lock expects)."""
    if (TLS and PORT == 443) or (not TLS and PORT == 80):
        return URL_HOST
    return f'{URL_HOST}:{PORT}'


# Real JILI hosts. The front-end un-reverses these params to build the API URLs, so
# they must be the REAL hostnames (no port!) — map them all to 127.0.0.1 in /etc/hosts
# and serve on 443. Using the reversed *localhost:port* instead injects a ':' the
# client's URL builder chokes on -> "cannot connect to server (MSG 199.5)".
DOC_HOST  = os.environ.get('DOC_HOST',  'uat-wbgame.jlfafafa3.com')        # document / static
BE_HOST   = os.environ.get('BE_HOST',   'uat-wbwebapi.jlfafafa2.com')      # sso-login.api
GS_HOST   = os.environ.get('GS_HOST',   'uat-wbslot-fd.jlfafafa1.com')     # /fg5/req
PLAT_HOST = os.environ.get('PLAT_HOST', 'uat-wbslot-platform.jlfafafa3.com')  # platform/telemetry
DOMAIN_GS = os.environ.get('DOMAIN_GS', 'jlfafafa1')
API_HOSTS = [DOC_HOST, BE_HOST, GS_HOST, PLAT_HOST]


def entry_url(_host_with_port=None):
    scheme = 'https' if TLS else 'http'
    port = '' if ((TLS and PORT == 443) or (not TLS and PORT == 80)) else f':{PORT}'
    return (f'{scheme}://{DOC_HOST}{port}{GAME_PATH}'
            f'?ssoKey=local-mock-token&lang=zh-CN&apiId=1778'
            f'&be={reverse(BE_HOST)}&domain_gs={reverse(DOMAIN_GS)}'
            f'&domain_platform={reverse(PLAT_HOST)}&gameID=696&gs={reverse(GS_HOST)}'
            f'&iu=true&legalLang=true&skin=0')


SSO_JSON = {
    'homeUrl': '', 'linecode': 0,
    'profile': {'id': '', 'aid': 1661835, 'apiId': 1778, 'transactionMode': 1,
                'subAgentCode': 1, 'isLobbyOpen': False,
                'meta': {'agentAccount': 'MOCK@api-1778.game'}, 'platform': '', 'lobbyMode': 0,
                'switchOffs': [26, 27, 44, 70], 'wallets': None, 'nickname': 'mockplayer',
                'newNickname': '', 'siteId': 91996886, 'account': 'mock@api-1778.game',
                'coin': 0, 'isJPEnabled': 0, 'linecode': 0, 'prefix': '', 'betLevel': -1,
                'betValue': 0, 'license': 0, 'isGiftCodeOpen': False, 'freeSpinBetValue': 0,
                'apiType': 0, 'walletType': 2, 'liveId': '', 'liveSourceUrls': {}},
    'token': '9492e028bf32eb2fa98e0d20d73b6b89d9318584',
    'response': {'error': 0, 'message': '', 'time': 1787842828},
    'platformVersion': 'uat.2.0.254', 'lobbyMode': 0, 'disableFullScreen': 0,
    'country': 'Brazil', 'certId': 0, 'certArea': 0, 'isnewplayer': 0,
    'clientApiParam': {}, 'itaAuthId': '', 'thousandthMode': '', 'eventBannerId': 0,
    'subDivision': 'Sao Paulo',
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass  # we log ourselves

    def _send(self, code, body=b'', ctype='application/octet-stream', extra=None):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body and self.command != 'HEAD':
            self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204)

    def _read_body(self):
        n = int(self.headers.get('Content-Length', '0') or '0')
        return self.rfile.read(n) if n else b''

    def _serve_websocket(self, path):
        """Handshake + keepalive for /lifeservice/ws2 (see WS_GUID note above)."""
        key = self.headers.get('Sec-WebSocket-Key')
        if not key:
            self._send(400, b'missing Sec-WebSocket-Key\n', 'text/plain')
            return
        accept = base64.b64encode(
            hashlib.sha1((key + WS_GUID).encode()).digest()).decode()
        # 101 upgrade. We deliberately do NOT echo Sec-WebSocket-Extensions, so
        # permessage-deflate is declined and every frame is uncompressed.
        self.wfile.write(
            ('HTTP/1.1 101 Switching Protocols\r\n'
             'Upgrade: websocket\r\nConnection: Upgrade\r\n'
             f'Sec-WebSocket-Accept: {accept}\r\n\r\n').encode())
        self.wfile.flush()
        self.close_connection = True
        print(f'[ws]   101 upgrade {path} — awaiting handshake frame')
        greeted = False
        try:
            while True:
                fr = ws_recv_frame(self.rfile)
                if fr is None:
                    break
                opcode, data = fr
                if opcode == 0x8:                     # close
                    ws_send_frame(self.wfile, 0x8)
                    break
                if opcode == 0x9:                     # ping -> pong
                    ws_send_frame(self.wfile, 0xA, data)
                    continue
                if opcode == 0xA:                     # pong
                    continue
                # text(0x1)/binary(0x2): the first data frame is the protobuf
                # handshake -> reply once with {"error":0}; the rest are heartbeats
                # the real server never answers, so we just drain them.
                if not greeted:
                    ws_send_frame(self.wfile, 0x1, b'{"error":0}')
                    greeted = True
                    print(f'[ws]   handshake ({"bin" if opcode == 0x2 else "txt"} '
                          f'{len(data)}B) -> sent {{"error":0}}')
                elif VERBOSE:
                    print(f'[ws]   heartbeat {data[:64]!r} (drained)')
        except (ConnectionError, OSError):
            pass
        print(f'[ws]   {path} closed')

    def do_GET(self):
        path = urlparse(self.path).path
        # WebSocket upgrade (keepalive /lifeservice/ws2) — must be handled before any
        # static/telemetry routing, which would otherwise 404 it and trip MSG 999.1.
        if self.headers.get('Upgrade', '').lower() == 'websocket':
            self._serve_websocket(path)
            return
        # wasm-keypatch shim beacon — lets us see the patch result in THIS log without
        # opening DevTools (which trips Jscrambler's anti-debug and wedges the loader).
        if path.startswith('/__wasmpatch__/'):
            from urllib.parse import unquote
            msg = unquote(path[len('/__wasmpatch__/'):])
            print(f'  ★★★ [shim-report] {msg}')
            m = re.search(r'capture seq=(\d+)', msg)
            if m:
                _seq_reported[0] = max(_seq_reported[0], int(m.group(1)))
                gap = _seq_reported[0] - _seq_received[0]
                if gap >= 3:
                    print(f'  ⚠⚠⚠ [capture] shim 說抓到 seq={_seq_reported[0]},但只收到 {_seq_received[0]}'
                          f' —— 落後 {gap} 筆,這幾局的資料【沒有進來】。'
                          f'\n      看上面有沒有 BEACON-FAIL;有的話重開 webcapture.sh 讓新版 shim 生效。')
            self._send(200, b'ok', 'text/plain')
            return
        if VERBOSE:
            print(f'[GET]  {path}')
        if path == '/' or path == '':
            url = entry_url(self.headers.get('Host', f'{HOST}:{PORT}'))
            self._send(302, b'', 'text/plain', {'Location': url})
            return

        # Intercept the crypto wasm -> serve our patched copy (baked pubs = ours).
        # It is fetched from a remote URL and is NOT in the static mirror, so any *.wasm
        # that either matches CRYPTO_WASM or has no local file is the crypto wasm.
        if path.endswith('.wasm') and PATCHED_WASM is not None and not CAPTURE:
            if CRYPTO_WASM_MARK in path or resolve_static(path) is None:
                print(f'[wasm] serve patched crypto.wasm for {path} ({len(PATCHED_WASM)}B)')
                self._send(200, PATCHED_WASM, 'application/wasm')
                return

        fp = resolve_static(path)
        if fp:
            with open(fp, 'rb') as f:
                data = f.read()
            # Safety net: if a served file *is* the original crypto.wasm (present in the
            # tree under some name), swap it for the patched bytes.
            if PATCHED_WASM is not None and ORIG_WASM is not None and data == ORIG_WASM and not CAPTURE:
                print(f'[wasm] static file {path} == original crypto.wasm -> serving patched')
                data = PATCHED_WASM
            ctype = mimetypes.guess_type(fp)[0] or 'application/octet-stream'
            if fp.endswith('.wasm'):
                ctype = 'application/wasm'
            # Bundle-prepend mode: put the shim INSIDE an existing JS bundle (no new <script>,
            # HTML byte-identical). Tests whether "modify existing carrier" evades the check that
            # kills any newly-injected <script> element.
            if WASM_SHIM and INJECT_BUNDLE and fp.endswith('.js') and BUNDLE_TARGET in path:
                js = data.decode('utf-8', 'replace')
                data = (WASM_SHIM + '\n;\n' + js).encode('utf-8')
                ctype = 'application/javascript'
                print(f'[shim] prepended shim into bundle {path} ({len(WASM_SHIM)}B)')
            # CANARY:往指定 bundle(如 index.22de5)前面塞一句無害 beacon,測「改它內容會不會自毀」。
            if CANARY_TARGET and fp.endswith('.js') and CANARY_TARGET in path:
                js = data.decode('utf-8', 'replace')
                canary = ("try{(new Image()).src='/__wasmpatch__/'+encodeURIComponent('CANARY %s ran');}catch(e){}\n;\n" % CANARY_TARGET)
                data = (canary + js).encode('utf-8')
                ctype = 'application/javascript'
                print(f'[canary] ★ prepended inert beacon into {path} (target={CANARY_TARGET!r}) — 測 22de5 可不可改')
            # HTML <head> inject mode (only when NOT bundle mode) — runs before any wasm loads.
            elif WASM_SHIM and not INJECT_BUNDLE and fp.endswith(('.html', '.htm')):
                html = data.decode('utf-8', 'replace')
                tag = f'<script>{WASM_SHIM}</script>'
                low = html.lower()
                idx = low.find('<head')
                if idx >= 0:
                    end = html.find('>', idx)
                    html = html[:end+1] + tag + html[end+1:] if end >= 0 else tag + html
                else:
                    html = tag + html
                data = html.encode('utf-8')
                ctype = 'text/html'
                print(f'[shim] injected wasm-keypatch into {path}')
            self._send(200, data, ctype)
        elif '/webservice/' in path or '/event/' in path or '/log' in path:
            # platform telemetry / loading-progress pings — answer 200 so the
            # loader's state machine doesn't wedge on a 404.
            if VERBOSE:
                print(f'[tele] GET {path} -> 200 {{}}')
            self._send(200, b'{"code":0}', 'application/json')
        else:
            # Mirror gap-filler: pull a missing static asset from the real origin and
            # cache it (fixes cross-platform texture-format 404s, e.g. Windows wants
            # .webp where the mirror only has .astc). Guard against self-recursion when
            # an origin host is mapped back to us (the fetch carries X-Mock-Fallback).
            if not self.headers.get('X-Mock-Fallback'):
                got = origin_fetch_and_cache(path)
                if got:
                    self._send(200, got[0], got[1])
                    return
            print(f'[404]  {path}   (missing asset? or the crypto wasm — set CRYPTO_WASM '
                  f'to a substring of this path)')
            self._send(404, b'not found\n', 'text/plain')

    do_HEAD = do_GET

    def do_POST(self):
        global _cap_count
        path = urlparse(self.path).path
        body = self._read_body()
        # CAPTURE side-channel: the capture shim POSTs {seq, req_body_hex, resp_body_hex, key?}
        # here for each real /fg5/req. Append to the exchanges jsonl + stash the AES key once.
        if path == '/__err__':
            try:
                e = json.loads(body.decode('utf-8'))
            except Exception:
                e = {}
            k = e.get('kind'); m = e.get('msg'); x = e.get('extra') or ''
            if k == 'alive':
                print('[errprobe] ★ shim 已在頁面裡啟動,之後的 JS 錯誤會印在這裡')
            else:
                print(f'[jserr] ★{k}★ {m}')
                for ln in str(x).splitlines()[:12]:
                    print(f'        {ln}')
            self._send(200, b'ok', 'text/plain')
            return
        if CAPTURE and path == '/__capture__':
            try:
                rec = json.loads(body.decode('utf-8'))
            except Exception:
                rec = None
            if isinstance(rec, dict):
                k = rec.get('key')
                if k:
                    try:
                        json.dump({'key': k, 'f4': rec.get('f4', '')}, open(GRAB_PATH, 'w'))
                        _chown_back(GRAB_PATH)
                        _set_cap_key(k)          # ★不要等某筆同時帶 key+resp 才啟用即時解碼
                    except Exception as e:
                        print(f'  ⚠ [capture] key write failed: {e!r}')
                g = rec.get('grv')
                if g and g not in _grv_seen:            # ephemeral-priv candidates (getRandomValues outputs)
                    _grv_seen.add(g)
                    try: _cap_grv.append(bytes.fromhex(g)[:32])
                    except Exception: pass
                    with _cap_lock:
                        with open(GRV_PATH, 'a') as f:
                            f.write(json.dumps({'out': g}) + '\n')
                    _chown_back(GRV_PATH)
                    print(f'  ★ [capture] getRandomValues candidate #{len(_grv_seen)} {g[:16]}…')
                rh = rec.get('resp_body_hex') or ''
                if rh:
                    with _cap_lock:
                        with open(CAP_EXCH_PATH, 'a') as f:
                            f.write(json.dumps({'req_body_hex': rec.get('req_body_hex', ''),
                                                'resp_body_hex': rh,
                                                'req_body_len': len(rec.get('req_body_hex', '')) // 2,
                                                'seq': rec.get('seq')}) + '\n')
                        _cap_count += 1
                        n = _cap_count
                    try:
                        _seq_received[0] = max(_seq_received[0], int(rec.get('seq') or 0))
                    except Exception:
                        pass
                    _chown_back(CAP_EXCH_PATH)
                    print(f'  ★ [capture] seq={rec.get("seq")} resp={len(rh)//2}B'
                          f'{" +KEY" if k else ""}  (total {n})')
                    if LIVE_DECODE:
                        try:
                            _msg = _live_decode(rec)
                        except Exception as e:
                            _msg = '  ⚠ [decode] 例外: %r' % (e,)
                        if _msg:
                            print(_msg)
                        elif not k:
                            print('  … [decode] key 還沒撈到，先存原始封包；等某筆帶 +KEY 之後就會即時解出。')
            self._send(200, b'ok', 'text/plain')
            return
        if path.endswith('/sso-login.api') or path.endswith('/sso-login'):
            if CAPTURE:
                print('  ⚠ [capture] sso-login hit the LOCAL server — /etc/hosts is NOT split. '
                      'The be host must resolve to the REAL server (VPN), not 127.0.0.1. Fix hosts + restart.')
                self._send(502, b'', 'application/json'); return
            if SSO_DELAY:
                print(f'[sso]  ⏳ stalling {SSO_DELAY}s so patchwasm can patch the fresh wasm '
                      f'BEFORE the handshake derives its shared key…')
                time.sleep(SSO_DELAY)
            SSO_JSON['response']['time'] = int(time.time())   # fresh, matches fg5 f1 clock
            data = json.dumps(SSO_JSON).encode()
            print(f'[sso]  {path} -> token {SSO_JSON["token"][:8]}...')
            self._send(200, data, 'application/json')
            return
        if path.endswith('/fg5/req') or path.endswith('/req'):
            if CAPTURE:
                print('  ⚠ [capture] /fg5/req hit the LOCAL server — /etc/hosts is NOT split. '
                      'The gs host must resolve to the REAL server (VPN), not 127.0.0.1, or you are '
                      'capturing the MOCK not the real game. Fix hosts + restart.')
                self._send(502, b'', 'application/octet-stream'); return
            try:
                req = CRYPTO.parse_request(body)
                if req['client_pub']:
                    # Publish the correct shared for patchwasm's FIX_SHARED overwrite. Done BEFORE any
                    # stall so the patcher can fix @1108480 during the response-stall window.
                    try:
                        with open(SHARED_HEX_PATH, 'w') as _f:
                            _f.write(CRYPTO.shared_key(req['client_pub']).hex())
                    except Exception:
                        pass
                mtype, pdata, ret, kind = pick_response(req)
                if HS_DELAY and kind == 'handshake':
                    print(f'[fg5]  ⏳ stalling handshake response {HS_DELAY}s (patchwasm window)…')
                    time.sleep(HS_DELAY)
                resp = CRYPTO.make_response(req['client_pub'], mtype, data=pdata, ret=ret)
                cp = bytes(req['client_pub'])[:4].hex()
                print(f'[fg5]  seq={req["seq"]:<4} reqlen={len(body):<4} cp={cp} kind={kind:<10} '
                      f'-> type={mtype} ret={ret} data={len(pdata)}B resp={len(resp)}B')
                if kind == 'handshake' and req['client_pub']:
                    # The shared the game MUST derive for this response to decrypt. patchwasm reads
                    # the game's actual shared@1108480; equal => game used mock pub (patch won),
                    # different+nonzero => game used real pub (patch too late -> fallback).
                    try:
                        exp = CRYPTO.shared_key(req['client_pub']).hex()
                        print(f'[fg5]  expected shared (game must derive) = {exp[:16]}…  full={exp}')
                    except Exception as e:
                        print(f'[fg5]  expected-shared calc failed: {e!r}')
                self._send(200, resp, 'application/octet-stream')
            except Exception as e:
                print(f'[fg5]  ERROR: {e!r}  body={body.hex()[:80]}')
                self._send(500, b'', 'application/octet-stream')
            return
        # any other POST — platform/lobby API, telemetry, etc. Log it (so we can see
        # what the launcher calls) and answer a generic success.
        print(f'[post?] {path}  ({len(body)}B) {body[:80].hex()}')
        self._send(200, b'{"code":0,"data":{},"message":""}', 'application/json')


def make_cert():
    """Auto-generate a self-signed cert for HTTPS if none supplied."""
    cert = os.environ.get('CERT'); key = os.environ.get('KEY')
    if cert and key:
        return cert, key
    cert = os.path.join(HERE, 'server.crt'); key = os.path.join(HERE, 'server.key')
    if os.path.exists(cert) and os.path.exists(key):
        return cert, key
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, HOST)])
    san = x509.SubjectAlternativeName([x509.DNSName(HOST), x509.DNSName('localhost')])
    now = datetime.datetime.utcnow()
    crt = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
           .public_key(k.public_key()).serial_number(x509.random_serial_number())
           .not_valid_before(now - datetime.timedelta(days=1))
           .not_valid_after(now + datetime.timedelta(days=3650))
           .add_extension(san, critical=False).sign(k, hashes.SHA256()))
    open(key, 'wb').write(k.private_bytes(serialization.Encoding.PEM,
                                          serialization.PrivateFormat.TraditionalOpenSSL,
                                          serialization.NoEncryption()))
    open(cert, 'wb').write(crt.public_bytes(serialization.Encoding.PEM))
    print(f'[tls] generated self-signed cert -> {cert}')
    return cert, key


def main():
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    scheme = 'http'
    if TLS:
        cert, key = make_cert()
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert, key)
        srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
        scheme = 'https'
    print('═' * 60)
    print('  JILI Route X mock server (game 696)')
    print(f'  static : {STATIC_ROOT}')
    print(f'  keys   : x25519_pub {KEYS["x25519_pub"][:16]}...  ed25519_pub {KEYS["ed25519_pub"][:16]}...')
    print(f'  listen : {scheme}://{HOST}:{PORT}')
    if PORT != 443 and TLS:
        print('  ⚠ serve on 443 (real hosts use no port) — see /etc/hosts line below')
    print('  /etc/hosts (map all game hosts to us):')
    print(f'      127.0.0.1 {" ".join(API_HOSTS)}')
    print(f'  open   : {entry_url()}')
    print('═' * 60)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\n[stop]')


if __name__ == '__main__':
    main()
