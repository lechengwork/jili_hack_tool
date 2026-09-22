#!/usr/bin/env python3
"""
ws_replay_server.py — JILI 124 (7up7down / 7上7下) 本地離線回放 server。

7up7down 的 WS 協定是【明文 protobuf、無加密】(見 WS_PROTOCOL.md)，所以離線回放
不需要任何 crypto:直接把擷取到的 WS frame 依 cmd 配對回放即可。

一個 TLS(自簽) server 同時服務(靠 Host+path 路由):
  · 靜態站      static/<path>  (+ shared/<path> fallback)
  · sso-login   POST /sso-login.api            → mock/sso.json (錄到的真回應)
  · telemetry   /webservice/event/*            → 204
  · ranking     /rankingservice/*              → mock/ranking.json
  · subagent    /subagentservice/*             → 200 {}
  · WebSocket   /sudm/ws/*  (Upgrade)          → 依「錄音帶」回放 ws_session.jsonl

前端入口:用 chrome --host-resolver-rules="MAP * 127.0.0.1:<port>" 把所有 jili host
指到本機(保留 jili hostname → 過 Jscrambler domain-lock),見 run_124.sh。

env: PORT(預設8443) HOST(預設127.0.0.1) SESSION(預設ws_session.jsonl) VERBOSE(1=印每筆)
"""
import base64, hashlib, json, os, ssl, struct, subprocess, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get('PORT', '8443'))
HOST = os.environ.get('HOST', '127.0.0.1')
SESSION = os.environ.get('SESSION', os.path.join(HERE, 'ws_session.jsonl'))
VERBOSE = os.environ.get('VERBOSE', '0') != '0'
STATIC = os.path.join(HERE, 'static')
SHARED = os.path.join(HERE, 'shared')
MOCK = os.path.join(HERE, 'mock')
WS_GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
HB = bytes.fromhex('0832')      # 2-byte heartbeat frame (cmd 50)

CTYPE = {'.html':'text/html','.js':'application/javascript','.mjs':'application/javascript',
         '.json':'application/json','.css':'text/css','.png':'image/png','.jpg':'image/jpeg',
         '.jpeg':'image/jpeg','.webp':'image/webp','.gif':'image/gif','.svg':'image/svg+xml',
         '.avif':'image/avif','.wasm':'application/wasm','.bin':'application/octet-stream',
         '.zip':'application/zip','.astc':'application/octet-stream','.cconb':'application/octet-stream',
         '.ico':'image/x-icon','.mp3':'audio/mpeg','.ogg':'audio/ogg','.ttf':'font/ttf'}


# ── protobuf: 取 envelope 的 cmd (field1 varint) ──────────────────────────────
def _rv(b, i):
    s = 0; r = 0
    while True:
        x = b[i]; i += 1; r |= (x & 0x7f) << s
        if not x & 0x80: break
        s += 7
    return r, i

def cmd_of(b):
    try:
        key, i = _rv(b, 0)
        if (key >> 3) == 1 and (key & 7) == 0:
            v, _ = _rv(b, i); return v
    except Exception:
        pass
    return None


# ── 載入錄音帶 ────────────────────────────────────────────────────────────────
def load_tape(path):
    frames = []   # (dir, cmd, bytes) in time order
    for line in open(path, encoding='utf-8'):
        try: d = json.loads(line)
        except Exception: continue
        if d.get('kind') != 'ws_msg': continue
        h = d.get('hex')
        if not h: continue
        b = bytes.fromhex(h)
        frames.append((d['dir'], cmd_of(b), b))
    # 連線時要先推的 RECV(第一個 SEND 之前的所有 RECV,含 177B 歡迎幀)
    welcome = []
    for dr, c, b in frames:
        if dr == 'SEND': break
        if dr == 'RECV': welcome.append(b)
    # 依 cmd 分桶(只收 RECV、排除心跳 cmd50)
    by_cmd = {}
    for dr, c, b in frames:
        if dr != 'RECV' or c == 50 or c is None: continue
        by_cmd.setdefault(c, []).append(b)
    return welcome, by_cmd


WELCOME, BY_CMD = load_tape(SESSION)
print(f'[tape] welcome={len(WELCOME)} frames; response cmds=' +
      ', '.join(f'{c}:{len(v)}' for c, v in sorted(BY_CMD.items())))


class Cursor:
    """每個 WS 連線一份:依 cmd 取下一個回應;cmd22(遊戲)取完會循環。"""
    def __init__(self):
        self.pos = {c: 0 for c in BY_CMD}
        self.lock = threading.Lock()
    def next(self, cmd):
        with self.lock:
            q = BY_CMD.get(cmd)
            if not q: return None
            i = self.pos.get(cmd, 0)
            if i >= len(q):
                if cmd == 22:            # 遊戲局:循環重播
                    i = 0
                else:
                    return None
            self.pos[cmd] = i + 1
            return q[i]


# ── WS framing (沿用 696 server.py) ───────────────────────────────────────────
def ws_recv(rfile):
    hdr = rfile.read(2)
    if len(hdr) < 2: return None
    b1, b2 = hdr[0], hdr[1]
    op = b1 & 0x0f; masked = b2 & 0x80; ln = b2 & 0x7f
    if ln == 126: ln = int.from_bytes(rfile.read(2), 'big')
    elif ln == 127: ln = int.from_bytes(rfile.read(8), 'big')
    mask = rfile.read(4) if masked else b''
    data = rfile.read(ln) if ln else b''
    if masked: data = bytes(data[i] ^ mask[i % 4] for i in range(len(data)))
    return op, data

def ws_send(wfile, payload, op=0x2):
    b1 = 0x80 | op; n = len(payload)
    if n < 126: hdr = bytes([b1, n])
    elif n < 65536: hdr = bytes([b1, 126]) + n.to_bytes(2, 'big')
    else: hdr = bytes([b1, 127]) + n.to_bytes(8, 'big')
    wfile.write(hdr + payload); wfile.flush()


class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *a):
        if VERBOSE: sys.stderr.write('  ' + (a[0] % a[1:]) + '\n')

    # ---- helpers ----
    def _cors(self):
        o = self.headers.get('Origin', '*')
        self.send_header('Access-Control-Allow-Origin', o)
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers',
                         self.headers.get('Access-Control-Request-Headers', '*') or '*')

    def _send(self, code, body=b'', ctype='application/octet-stream'):
        if isinstance(body, str): body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self._cors()
        self.end_headers()
        if body and self.command != 'HEAD':
            try: self.wfile.write(body)
            except Exception: pass

    def _read_body(self):
        n = int(self.headers.get('Content-Length', '0') or '0')
        return self.rfile.read(n) if n else b''

    # ---- routing ----
    def _route_api(self, path):
        """回 True=已處理(是 API/telemetry);False=交給靜態。"""
        if path.startswith('/webservice/event'):
            self._send(204); return True
        if path.startswith('/rankingservice'):
            try: body = open(os.path.join(MOCK, 'ranking.json'), 'rb').read()
            except Exception: body = b'{}'
            self._send(200, body, 'application/json'); return True
        if path.startswith('/subagentservice'):
            self._send(200, b'{}', 'application/json'); return True
        if path.startswith('/sso-login') or path.endswith('/sso-login.api'):
            try: body = open(os.path.join(MOCK, 'sso.json'), 'rb').read()
            except Exception: body = b'{}'
            self._send(200, body, 'application/json'); return True
        if '/webservice/' in path or '/service/' in path.lower():
            self._send(200, b'{}', 'application/json'); return True
        return False

    def _serve_static(self, path):
        rel = unquote(path.split('?')[0]).lstrip('/')
        if rel == '' or rel.endswith('/'): rel += 'index.html'
        for root in (STATIC, SHARED):
            fp = os.path.abspath(os.path.join(root, rel))
            if not fp.startswith(os.path.abspath(root)): continue
            if os.path.isfile(fp):
                ext = os.path.splitext(fp)[1].lower()
                with open(fp, 'rb') as f: data = f.read()
                self._send(200, data, CTYPE.get(ext, 'application/octet-stream'))
                return
        if VERBOSE: sys.stderr.write(f'  [404] {rel}\n')
        self._send(404, b'not found\n', 'text/plain')

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.send_header('Content-Length', '0'); self.end_headers()

    def do_POST(self):
        path = urlsplit(self.path).path
        self._read_body()
        if not self._route_api(path):
            self._send(404, b'{}', 'application/json')

    def do_HEAD(self): self.do_GET()

    def do_GET(self):
        path = urlsplit(self.path).path
        if self.headers.get('Upgrade', '').lower() == 'websocket':
            self._serve_ws(path); return
        if self._route_api(path): return
        self._serve_static(path)

    # ---- WebSocket 回放 ----
    def _serve_ws(self, path):
        key = self.headers.get('Sec-WebSocket-Key')
        if not key:
            self._send(400, b'no ws key\n', 'text/plain'); return
        accept = base64.b64encode(hashlib.sha1((key + WS_GUID).encode()).digest()).decode()
        self.wfile.write(('HTTP/1.1 101 Switching Protocols\r\n'
                          'Upgrade: websocket\r\nConnection: Upgrade\r\n'
                          f'Sec-WebSocket-Accept: {accept}\r\n\r\n').encode())
        self.wfile.flush()
        print(f'[ws] connect {path}')
        cur = Cursor()
        # 連線先推歡迎幀(login-ack/帳號資訊)
        for b in WELCOME:
            ws_send(self.wfile, b)
        if VERBOSE: print(f'[ws] sent {len(WELCOME)} welcome frames')
        try:
            while True:
                fr = ws_recv(self.rfile)
                if fr is None: break
                op, data = fr
                if op == 0x8: break                      # close
                if op == 0x9: ws_send(self.wfile, data, 0xA); continue   # ping->pong
                if op == 0xA: continue                   # pong
                if not data: continue
                c = cmd_of(data)
                if c == 50:                               # 應用層心跳
                    ws_send(self.wfile, HB); continue
                resp = cur.next(c)
                if resp is not None:
                    ws_send(self.wfile, resp)
                    if VERBOSE: print(f'[ws] cmd={c} -> {len(resp)}B')
                elif VERBOSE:
                    print(f'[ws] cmd={c} (無錄音回應,略過)')
        except (ConnectionError, OSError):
            pass
        print(f'[ws] close {path}')


def ensure_cert():
    crt = os.path.join(HERE, 'cert.pem'); key = os.path.join(HERE, 'key.pem')
    if os.path.isfile(crt) and os.path.isfile(key): return crt, key
    print('[tls] 產生自簽憑證…')
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                    '-keyout', key, '-out', crt, '-days', '3650',
                    '-subj', '/CN=jili-replay'], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return crt, key


def main():
    crt, key = ensure_cert()
    httpd = ThreadingHTTPServer((HOST, PORT), H)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(crt, key)
    try: ctx.set_alpn_protocols(['http/1.1'])   # 逼 http/1.1,stdlib 不支援 h2
    except Exception: pass
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    print('═' * 58)
    print(f'  JILI 124 (7up7down) 本地回放 server')
    print(f'  https://{HOST}:{PORT}   (TLS 自簽)')
    print(f'  static={STATIC}')
    print(f'  用 run_124.sh 開遊戲(host-resolver-rules 指向本機)')
    print('═' * 58)
    try: httpd.serve_forever()
    except KeyboardInterrupt: print('\n[stop]')


if __name__ == '__main__':
    main()
