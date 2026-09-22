#!/usr/bin/env python3
"""watch4.py — 盯真站擷取,專等【饋贈 index4「重轉一軸」】那一局。

    ./.venv/bin/python3 watch4.py              # 持續盯,抓到 index4 就印完整欄位樹並 exit 0
    ./.venv/bin/python3 watch4.py --once       # 只算一次目前狀態(不等)
    SEED_REPORT=1 ./.venv/bin/python3 watch4.py --once   # 連既有的 834 局一起報(自我驗證用)

設計同 WATCH_PATTERN.md:只讀檔不寫檔,每行 stdout = 一則通知,達標就退出。
起跑時先把「現有局號」記成基準線,之後只對【新進來的局】發聲。

會叫的事:
  ★ index4 命中        ← 目標。印出整棵欄位樹(含未知欄位的 raw hex)→ 那就是缺的伴隨欄位
  ★ index0 命中        ← 另一個沒樣本的槽位,也很值錢
  ● index1/2/3 命中    ← 進度訊號
  ✗ 出現 schema 沒有的 protobuf 欄位   ← 伴隨欄位最可能從這裡現形
  ✗ 倍率規則反例
  ✗ slot3「交換說」反例  ← 2026-09-21 新定的規則,讓新資料每局替它考試
  ⚠ 側錄斷線 / … 心跳
"""
import json, glob, os, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'routex'))
import math_adapter as ma

GID      = os.environ.get('GID', '696')
INTERVAL = int(os.environ.get('INTERVAL', '30'))
STALL    = int(os.environ.get('STALL', '300'))
SPIN_STALL = int(os.environ.get('SPIN_STALL', '300'))   # 幾秒沒有【新的一局】就當 autoplay 停了
HB       = int(os.environ.get('HB', '200'))
SEED     = os.environ.get('SEED_REPORT') == '1'
ONCE     = '--once' in sys.argv

SPINS = os.path.join(ROOT, 'games', GID, 'webcap', 'backend_raw', 'spins')
CAP   = os.path.join(ROOT, 'games', GID, 'webcap_exchanges.jsonl')
GRAB  = os.environ.get('GRAB', '/tmp/jili_grab.json')

VAL  = {9:1, 10:2, 11:3, 12:5, 13:10, 14:15, 15:20, 16:25, 17:50, 18:100, 19:500, 20:0}
SWAP = {1:0, 2:1, 3:3, 4:4}          # slot3 值 → 交換的格號(2026-09-21 定案)
KNOWN = {'SpinResult':{1,2,3,6,20,23}, 'BoardDetail':{1,2,3,4,5,6,7,8,10,12,13,15,18,19},
         'Reel':{1}, 'SymbolWindow':{1}, 'LineWin':{1,2,3,4}, 'PostNudge':{1,2},
         'BetInfo':{1,25,26}, 'Ante':{1}}
SUB = {('SpinResult',1):'BoardDetail', ('SpinResult',23):'BetInfo',
       ('BoardDetail',1):'Reel', ('BoardDetail',2):'SymbolWindow',
       ('BoardDetail',6):'LineWin', ('BoardDetail',19):'PostNudge', ('BetInfo',26):'Ante'}


def walk(buf, msg, out, depth=0, path=''):
    """走完整棵欄位樹;schema 沒有的欄位連 raw hex 一起記下來。"""
    for f, w, v in ma._fields(bytes(buf)):
        p = f'{path}.f{f}'
        known = f in KNOWN.get(msg, set())
        if not known:
            out.append((p, msg, f, w, bytes(v) if isinstance(v, (bytes, bytearray)) else v))
            continue
        sub = SUB.get((msg, f))
        if sub and w == 2:
            walk(v, sub, out, depth+1, p)


def dump(buf, msg='SpinResult', ind='    '):
    lines = []
    def rec(b, m, d):
        for f, w, v in ma._fields(bytes(b)):
            sub = SUB.get((m, f))
            mark = '' if f in KNOWN.get(m, set()) else '   ←★schema 沒有這個欄位★'
            if sub and w == 2:
                lines.append(f'{ind}{"  "*d}{m}.f{f} ({sub}){mark}')
                rec(v, sub, d+1)
            else:
                s = v.hex() if isinstance(v, (bytes, bytearray)) else v
                if isinstance(s, str) and len(s) > 80: s = s[:80] + '…'
                lines.append(f'{ind}{"  "*d}{m}.f{f} = {s}{mark}')
    rec(buf, msg, 0)
    return '\n'.join(lines)


_KEYS = []          # 這一場看過的 session key(擷取重開會換一把,都留著試)
SRV_ERR = []        # 伺服器回的 ret!=0(每輪重算,由 main 比對新增)


def _keys():
    """session key 從 shim 抓的 grab 檔讀;擷取重開會換,所以每輪都重讀。"""
    try:
        k = bytes.fromhex(json.load(open(GRAB, encoding='utf-8'))['key'])
        if k not in _KEYS:
            _KEYS.append(k)
    except Exception:
        pass
    return _KEYS


def load():
    del SRV_ERR[:]
    """→ {round_id: (board_dict, payload_bytes)}

    兩個來源都吃:
      (a) backend_raw/spins/*.json —— server 即時解碼的產物(2026-09-21 前有 bug,可能是空的)
      (b) webcap_exchanges.jsonl + /tmp/jili_grab.json 的 key —— ★自己離線解★,不依賴 server
    只要 (b) 通,擷取就算沒即時解碼也照樣盯得到。
    """
    got = {}
    for fp in glob.glob(os.path.join(SPINS, '*.json')):
        try:
            d = json.load(open(fp, encoding='utf-8'))
        except Exception:
            continue                       # 可能正在被寫入
        if d.get('type') != 0 or not d.get('payload_hex'):
            continue
        raw = bytes.fromhex(d['payload_hex'])
        try:
            b = ma.wire_to_math(raw)['board']
        except Exception:
            continue
        got[str(d['round_id']).replace('-', '')] = (b, raw)   # 統一成無破折號,兩個來源才不會各算一次

    keys = _keys()
    if keys and os.path.exists(CAP):
        import decrypt_capture as dc, webcap_backend_raw as br
        try:
            rows = [json.loads(l) for l in open(CAP, encoding='utf-8') if l.strip()]
        except Exception:
            rows = []
        for r in rows:
            rh = r.get('resp_body_hex')
            if not rh:
                continue
            for k in keys:
                try:
                    d = dc.decrypt_response(bytes.fromhex(rh), k, verify_sig=False)
                except Exception:
                    continue
                try:
                    _, payload, typ, _r, _e, _t = br.split_envelope(bytes.fromhex(d['pt_hex']))
                    if _r:                     # ★伺服器自己回錯★ 例如 ret=304 single wallet process error
                        SRV_ERR.append((r.get('seq'), _r, _e))
                        break
                    if typ != 0 or not payload:
                        break
                    m = ma.wire_to_math(payload)
                    rid = m.get('round_id')
                    if rid:
                        got.setdefault(str(rid).replace('-', ''), (m['board'], payload))
                except Exception:
                    pass
                break
    return got


def check(rid, b, raw, unknown_seen):
    """回傳要印的行。"""
    ev = []
    np_ = b.get('nudge_pos') or [0]*5
    # ① 未知欄位
    found = []
    walk(raw, 'SpinResult', found)
    for p, msg, f, w, v in found:
        key = f'{msg}.f{f}'
        if key not in unknown_seen:
            unknown_seen.add(key)
            hx = v.hex() if isinstance(v, (bytes, bytearray)) else v
            ev.append(f'✗★出現 schema 沒有的欄位 {key}★ (wire={w}) 值={hx}  局 {rid}')
    # ② 倍率規則
    sl = b['window'][2:len(b['window'])-2]
    if all(x in VAL for x in sl) and abs(sum(VAL[x] for x in sl) - b['multiplier']) > 1e-9:
        ev.append(f'✗★倍率規則反例★ 局 {rid} window={b["window"]} 算出 {sum(VAL[x] for x in sl)} 實際 {b["multiplier"]}')
    # ③ slot3 交換說回歸
    if len(np_) > 3 and np_[3]:
        v3, w = np_[3], b['window']
        t = SWAP.get(v3)
        if t is None or w[t] >= w[2]:
            ev.append(f'✗★slot3 交換說反例★ 局 {rid} 值={v3} → idx{t}; window[:5]={w[:5]} '
                      f'(交換來源應該要比中間格低)')
    # ④ 命中
    if any(np_):
        slot = [i for i, x in enumerate(np_) if x][0]
        if slot == 4:
            ev.append(f'★★★命中 index4(重轉一軸)★★★ 局 {rid}  nudge_pos={np_}')
            ev.append(f'   reels={[r for r in b["reels"]]}  window={b["window"]}')
            ev.append(f'   post_nudge={[p for p in b["post_nudge"]]}  boost={b.get("boost_symbols")}')
            ev.append('   ── 完整欄位樹（★ 標記的就是伴隨欄位） ──')
            ev.append(dump(raw))
        elif slot == 0:
            ev.append(f'★★命中 index0(預兆)★★ 局 {rid}  nudge_pos={np_}  boost={b.get("boost_symbols")}')
            ev.append('   ── 完整欄位樹 ──')
            ev.append(dump(raw))
        else:
            ev.append(f'● 饋贈 index{slot}=值{np_[slot]}  局 {rid}')
    return ev


def main():
    seed = load()
    base = set() if SEED else set(seed)
    seen_err0 = set() if SEED else set(SRV_ERR)   # 啟動時就存在的伺服器錯誤,重掛不重報
    unknown_seen, hit = set(), {0:0, 1:0, 2:0, 3:0, 4:0}
    seen_err = seen_err0
    if not SEED:                       # 命中數從基準線起算,重掛後心跳才是【全場累計】而不是本次
        for rid in seed:
            np_ = seed[rid][0].get('nudge_pos') or [0]*5
            if any(np_):
                hit[[i for i, x in enumerate(np_) if x][0]] += 1
    print(f'[watch4] 基準線 {len(base)} 局(既有饋贈 idx0={hit[0]} idx1={hit[1]} idx2={hit[2]} '
          f'idx3={hit[3]} idx4={hit[4]})；等 index4(重轉一軸)。輪詢 {INTERVAL}s', flush=True)
    hb_mark, stalled = len(base), 0   # 心跳從基準線起算,重掛時不要立刻噴一次
    # ★側錄活著 ≠ 有在轉★ autoplay 跑完一批就會靜靜停掉。
    # 起跑點取「最新一局的檔案時間」,而且如果啟動當下就已經停著,直接記成 already-warned ——
    # 重掛時不要把同一件事再報一次,只在【真的恢復】或【從轉著變成停住】時才出聲。
    try:
        last_spin = max(os.path.getmtime(f) for f in glob.glob(os.path.join(SPINS, '*.json')))
    except ValueError:
        last_spin = time.time()
    spin_stalled = 1 if time.time() - last_spin > SPIN_STALL else 0
    while True:
        got = load()
        new = [r for r in sorted(got) if r not in base]
        for rid in new:
            b, raw = got[rid]
            for line in check(rid, b, raw, unknown_seen):
                print(line, flush=True)
            np_ = b.get('nudge_pos') or [0]*5
            if any(np_): hit[[i for i, x in enumerate(np_) if x][0]] += 1
            base.add(rid)
        if hit[4]:
            print(f'★★達成★★ 抓到 index4(重轉一軸)。本輪累計 {len(base)} 局，'
                  f'其餘命中 idx0={hit[0]} idx1={hit[1]} idx2={hit[2]} idx3={hit[3]}', flush=True)
            return 0
        for e in SRV_ERR:
            if e not in seen_err:
                seen_err.add(e)
                hint = ('  ←平台無縫錢包回呼失敗,遊戲會跳 MSG 304 要你重登;不是我們這端的問題'
                        if e[1] == 304 else '')
                print(f'✗★伺服器回錯 ret={e[1]}★ {e[2]!r} (seq={e[0]}){hint}', flush=True)
        # ★真正該防的洞:側錄流還在動(心跳/餘額輪詢),但已經沒有新的一局 = autoplay 停了
        if new:
            last_spin = time.time()
            if spin_stalled:
                print(f'● 轉軸恢復(累計 {len(base)} 局)', flush=True); spin_stalled = 0
        idle = int(time.time() - last_spin)
        if idle > SPIN_STALL and not spin_stalled:
            print(f'⚠★沒有新的一局了★ 已經 {idle//60} 分鐘沒進新局(累計 {len(base)}) —— '
                  f'autoplay 多半跑完一批停了,去把它再按下去', flush=True)
            spin_stalled = 1
        age = int(time.time() - os.path.getmtime(CAP)) if os.path.exists(CAP) else 99999
        if age > STALL and not stalled:
            print(f'⚠★側錄停了★ 最後一筆 {age//60} 分鐘前 —— 現在轉的都沒錄到', flush=True); stalled = 1
        elif age <= 90 and stalled:
            print('● 側錄恢復', flush=True); stalled = 0
        cnt = len(base)
        if cnt - hb_mark >= HB:
            print(f'… 已累計 {cnt} 局；饋贈命中 idx0={hit[0]} idx1={hit[1]} idx2={hit[2]} '
                  f'idx3={hit[3]} idx4={hit[4]}；側錄 {age}s 前', flush=True)
            hb_mark = cnt
        if ONCE:
            print(f'[watch4] --once：{cnt} 局，命中 {hit}，未知欄位 {sorted(unknown_seen) or "無"}', flush=True)
            return 0
        time.sleep(INTERVAL)


if __name__ == '__main__':
    sys.exit(main())
