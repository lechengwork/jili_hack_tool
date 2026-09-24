#!/usr/bin/env python3
"""
ws_capture_server.py — JILI 124 (7up7down) 【實時擷取】本機 server。

抓封包用 jili host + hosts 導本機:機率團隊的 hosts 把 doc host
`uat-wbgame.jlfafafa3.com` → 127.0.0.1，其餘 host(sso-login=uat-wbwebapi、
遊戲 WS=uat-fish)不導 → 照常走真站(BR VPN)。所以:
  · location.hostname 仍是 jili host → 過 Jscrambler domain-lock(不用任何 bypass)。
  · 這支 server 只服務【doc host】上的東西:靜態站 + 側錄收集點。
  · 遊戲的 WebSocket 直連真站(uat-fish)不經本機 → 用【頁面內 hook】側錄(ws_capture_shim.js)。

這支 server 做四件事:
  1) 靜態站         static/<path>          從 dist124/static 服務(缺檔→404 並印出)
  2) 注入 shim      serve system.bundle 時 prepend ws_capture_shim.js(乾淨載體)
  3) 收側錄         POST /__wscap          → append 到 OUT(每行一個 ws_msg，明文 hex)
  4) 收診斷         GET  /__wsreport__/<m> → 印出 shim 的診斷訊息
  另外 telemetry(/webservice/event/*)若打到 doc host → 204(避免卡)。
★不處理 WebSocket Upgrade★:遊戲 WS 走真站，不該連到本機;若有連到=hosts 設錯。

env: PORT(預設 8443；Windows 擷取用 443) HOST(預設 127.0.0.1)
     OUT(側錄輸出，預設 games/124/webcap_ws.jsonl)
     STATIC(靜態根，預設 dist124/static)  SHIM(預設 ws_capture_shim.js)
     CERT/KEY(TLS，預設 dist124/cert.pem, dist124/key.pem)  TLS(1=開，預設 1)
     VERBOSE(1=印每個請求)
"""
import json, os, ssl, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get('PORT', '8443'))
HOST = os.environ.get('HOST', '127.0.0.1')
STATIC = os.environ.get('STATIC', os.path.join(HERE, 'dist124', 'static'))
SHIM_PATH = os.environ.get('SHIM', os.path.join(HERE, 'ws_capture_shim.js'))
OUT = os.environ.get('OUT', os.path.join(HERE, 'games', '124', 'webcap_ws.jsonl'))
CERT = os.environ.get('CERT', os.path.join(HERE, 'dist124', 'cert.pem'))
KEY = os.environ.get('KEY', os.path.join(HERE, 'dist124', 'key.pem'))
TLS = os.environ.get('TLS', '1') != '0'
VERBOSE = os.environ.get('VERBOSE', '0') != '0'

CTYPE = {'.html':'text/html','.js':'application/javascript','.mjs':'application/javascript',
         '.json':'application/json','.css':'text/css','.png':'image/png','.jpg':'image/jpeg',
         '.jpeg':'image/jpeg','.webp':'image/webp','.gif':'image/gif','.svg':'image/svg+xml',
         '.avif':'image/avif','.wasm':'application/wasm','.bin':'application/octet-stream',
         '.zip':'application/zip','.astc':'application/octet-stream','.cconb':'application/octet-stream',
         '.ico':'image/x-icon','.mp3':'audio/mpeg','.ogg':'audio/ogg','.ttf':'font/ttf','.txt':'text/plain'}

_lock = threading.Lock()
_stats = {'frames': 0, 'send': 0, 'recv': 0, 'assets': 0, 'miss': 0}

with open(SHIM_PATH, 'r', encoding='utf-8') as f:
    SHIM_SRC = f.read()


def is_system_bundle(path):
    """index.html 唯一直接載的 script = sudm/src/system.bundle.<hash>.js。
    用檔名前綴判斷(hash 變也命中)。"""
    base = os.path.basename(path)
    return base.startswith('system.bundle') and base.endswith('.js')


def safe_static(path):
    """把 URL path 解析成 static 底下的實體檔，擋 .. 逃逸。"""
    rel = unquote(path.split('?', 1)[0]).lstrip('/')
    full = os.path.normpath(os.path.join(STATIC, rel))
    root = os.path.normpath(STATIC)
    if full != root and not full.startswith(root + os.sep):
        return None
    return full


class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        if VERBOSE:
            sys.stderr.write('  ' + (a[0] % a[1:]) + '\n')

    def _send(self, code, body=b'', ctype='text/plain', extra=None):
        if isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        # 同源即可，但補 CORS 保險(shim POST 一定同源)
        self.send_header('Access-Control-Allow-Origin', self.headers.get('Origin', '*'))
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def do_OPTIONS(self):
        self._send(204)

    def do_GET(self):
        p = urlsplit(self.path).path

        # 診斷:shim 用 Image().src='/__wsreport__/<msg>' 回報
        if p.startswith('/__wsreport__/'):
            msg = unquote(p[len('/__wsreport__/'):])
            print('  [shim] ' + msg, flush=True)
            self._send(200, b'', 'image/gif')
            return

        # telemetry(若打到 doc host)→ 204
        if p.startswith('/webservice/event') or p.startswith('/rankingservice') \
                or p.startswith('/subagentservice') or p.startswith('/favoriteservice'):
            self._send(204)
            return

        if p == '/' or p == '':
            p = '/sudm/index.html'

        full = safe_static(p)
        if not full or not os.path.isfile(full):
            with _lock:
                _stats['miss'] += 1
            if VERBOSE:
                print('  [404] ' + p, flush=True)
            self._send(404, 'not found: ' + p)
            return

        with open(full, 'rb') as f:
            data = f.read()
        ext = os.path.splitext(full)[1].lower()
        ctype = CTYPE.get(ext, 'application/octet-stream')

        # ★注入點:system.bundle → prepend shim(乾淨載體，不加 <script>、不改既有源碼)
        if is_system_bundle(full):
            data = (SHIM_SRC + '\n;').encode('utf-8') + data
            print('  [inject] ws-capture-shim → ' + os.path.basename(full)
                  + ' (+%d bytes)' % (len(SHIM_SRC) + 2), flush=True)

        with _lock:
            _stats['assets'] += 1
        self._send(200, data, ctype)

    def do_POST(self):
        p = urlsplit(self.path).path

        # ● 側錄收集點:shim 每個 WS frame POST 一筆 ws_msg
        if p == '/__wscap':
            n = int(self.headers.get('Content-Length', '0') or '0')
            raw = self.rfile.read(n) if n else b''
            try:
                rec = json.loads(raw.decode('utf-8'))
            except Exception as e:
                self._send(400, 'bad json: %s' % e)
                return
            with _lock:
                with open(OUT, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                _stats['frames'] += 1
                d = rec.get('dir')
                if d == 'SEND':
                    _stats['send'] += 1
                elif d == 'RECV':
                    _stats['recv'] += 1
                tot, s, r = _stats['frames'], _stats['send'], _stats['recv']
            hexlen = len(rec.get('hex', '')) // 2
            print('  [ws] %-4s %4dB  (total=%d send=%d recv=%d)'
                  % (rec.get('dir', '?'), hexlen, tot, s, r), flush=True)
            self._send(200, b'ok')
            return

        # 其餘 POST(sso-login 等)理論上打真站、不會到這;到這就 204 免卡
        self._send(204)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    httpd = ThreadingHTTPServer((HOST, PORT), H)
    scheme = 'https'
    if TLS:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(CERT, KEY)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    else:
        scheme = 'http'
    print('── JILI 124 實時擷取 server ──', flush=True)
    print('  listen   %s://%s:%d' % (scheme, HOST, PORT), flush=True)
    print('  static   %s' % STATIC, flush=True)
    print('  shim     %s (%d bytes) → 注入 system.bundle' % (SHIM_PATH, len(SHIM_SRC)), flush=True)
    print('  側錄輸出  %s' % OUT, flush=True)
    print('  等頁面連進來…(玩遊戲→看 [ws] 逐筆進來；收工 Ctrl+C，再跑 wscapture_finish)', flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n收工。側錄 %d 筆(send=%d recv=%d) → %s'
              % (_stats['frames'], _stats['send'], _stats['recv'], OUT), flush=True)


if __name__ == '__main__':
    main()
