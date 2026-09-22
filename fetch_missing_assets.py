#!/usr/bin/env python3
"""fetch_missing_assets.py — 跨平台補齊 mirror 缺的 /fg5 靜態資產(Windows/Mac 皆可)。

為什麼會缺:game_site_backup 是在某台機器抓的,壓縮貼圖只存了那台 GPU 用的格式
(Apple=.astc);換一台(Windows 一般 GPU)Cocos 會改要 .webp,本機 mirror 沒有 → 404 →
loader 卡在 JILI splash。這支把缺的檔從【真站 uat-wbgame】抓回來、存進 mirror。

★關鍵:用 DoH 查真站 IP、再用 IP+SNI 直連,所以【就算 /etc/hosts(或 Windows hosts)
  已經把 uat-wbgame 指到 127.0.0.1(webcapture 狀態)也能抓真站】,不用你手動改 hosts。
  DoH 不通時,自動退回「一般連線」(需 hosts 沒 remap 才有效)。
兩者都需要 VPN=巴西(BR)。

用法(在解壓後的 jili/ 目錄):
  python fetch_missing_assets.py                 # 整批:補所有 .astc 對應的 .webp
  python fetch_missing_assets.py --list          # 只列出要補什麼,不下載
  python fetch_missing_assets.py /fg5/assets/main/native/xx/yy.webp  [更多路徑…]
                                                 # 精準補:貼 server 視窗 404 的那幾條路徑
  python fetch_missing_assets.py --force ...      # 已存在也重抓
"""
import os, sys, json, socket, ssl, urllib.request

HOST = os.environ.get('DOC_HOST', 'uat-wbgame.jlfafafa3.com')
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, 'game_site_backup', HOST)   # mirror root for the doc host

_UNVERIFIED = ssl.create_default_context()
_UNVERIFIED.check_hostname = False
_UNVERIFIED.verify_mode = ssl.CERT_NONE


def doh_ip(host):
    """Resolve host's real A record via DoH (bypasses the local hosts file)."""
    for res in ('https://1.1.1.1/dns-query', 'https://dns.google/resolve'):
        try:
            req = urllib.request.Request(f'{res}?name={host}&type=A',
                                         headers={'accept': 'application/dns-json'})
            with urllib.request.urlopen(req, timeout=8, context=_UNVERIFIED) as r:
                d = json.load(r)
            for a in d.get('Answer', []):
                ip = str(a.get('data', ''))
                if ip[:1].isdigit() and ':' not in ip:
                    return ip
        except Exception:
            continue
    return None


def _get_plain(rel):
    """Normal HTTPS GET (only reaches the real server if hosts is NOT remapped)."""
    try:
        req = urllib.request.Request(f'https://{HOST}/{rel}',
                                     headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=12, context=_UNVERIFIED) as r:
            return r.read() if getattr(r, 'status', 200) == 200 else None
    except Exception:
        return None


def _get_by_ip(ip, rel):
    """HTTPS GET to a specific IP with SNI/Host = HOST (bypasses hosts remap)."""
    raw = socket.create_connection((ip, 443), timeout=15)
    try:
        tls = _UNVERIFIED.wrap_socket(raw, server_hostname=HOST)
        tls.sendall((f'GET /{rel} HTTP/1.1\r\nHost: {HOST}\r\n'
                     f'User-Agent: Mozilla/5.0\r\nAccept: */*\r\n'
                     f'Connection: close\r\n\r\n').encode())
        buf = b''
        while True:
            chunk = tls.recv(65536)
            if not chunk:
                break
            buf += chunk
        tls.close()
    finally:
        try: raw.close()
        except Exception: pass
    head, _, body = buf.partition(b'\r\n\r\n')
    line = head.split(b'\r\n', 1)[0].decode('latin1')
    parts = line.split()
    if len(parts) >= 2 and parts[1] == '200' and body:
        # strip chunked encoding if present (Connection: close usually gives plain body)
        if b'transfer-encoding: chunked' in head.lower():
            body = _dechunk(body)
        return body
    return None


def _dechunk(b):
    out, i = b'', 0
    try:
        while i < len(b):
            j = b.find(b'\r\n', i)
            if j < 0: break
            n = int(b[i:j], 16)
            if n == 0: break
            out += b[j+2:j+2+n]; i = j+2+n+2
    except Exception:
        return b
    return out


_IP_CACHE = {}
def fetch(rel):
    data = _get_plain(rel)                 # 1) works when hosts is clean
    if data:
        return data
    if HOST not in _IP_CACHE:
        _IP_CACHE[HOST] = doh_ip(HOST)     # 2) DoH bypass (works with hosts remapped)
    ip = _IP_CACHE[HOST]
    if ip:
        try:
            return _get_by_ip(ip, rel)
        except Exception as e:
            print(f'    (by-ip {ip} err: {e!r})')
    return None


def targets_from_astc():
    """Every .astc in the mirror -> its .webp sibling (the cross-platform gap)."""
    rels = []
    root = os.path.join(BASE, 'fg5')
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            if fn.endswith('.astc'):
                full = os.path.join(dp, fn[:-5] + '.webp')
                rels.append(os.path.relpath(full, BASE).replace(os.sep, '/'))
    return sorted(set(rels))


def main():
    args = [a for a in sys.argv[1:]]
    force = '--force' in args;  args = [a for a in args if a != '--force']
    listonly = '--list' in args; args = [a for a in args if a != '--list']
    explicit = [a.lstrip('/') for a in args if not a.startswith('-')]

    if not os.path.isdir(os.path.join(BASE, 'fg5')):
        sys.exit(f'✗ 找不到 mirror: {os.path.join(BASE, "fg5")}\n'
                 f'  請在解壓後的 jili/ 目錄裡執行這支。')

    rels = explicit if explicit else targets_from_astc()
    print(f'目標 {len(rels)} 個檔  (host={HOST}, mode={"精準" if explicit else "整批 astc->webp"})')
    if listonly:
        for r in rels: print('  ', r)
        return

    ok = skip = miss = 0
    for rel in rels:
        dest = os.path.join(BASE, *rel.split('/'))
        if not force and os.path.isfile(dest):
            skip += 1; continue
        data = fetch(rel)
        if data:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'wb') as f:
                f.write(data)
            ok += 1; print(f'  ✓ {rel} ({len(data)}B)')
        else:
            miss += 1; print(f'  ✗ {rel}  (真站也沒有 / 連不到)')
    print(f'\n完成:新增 {ok} / 已存在略過 {skip} / 抓不到 {miss}')
    if miss:
        print('  抓不到的通常是:VPN 不在 BR、或該檔真站也沒有。確認 BR 再試。')


if __name__ == '__main__':
    main()
