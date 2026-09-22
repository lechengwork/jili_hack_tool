#!/usr/bin/env python3
"""watch_state.py — 吐【一行】機器可讀的狀態,給 watch.sh 輪詢用。

格式:total|gift|rulebad|unknown|capage|giftvals
  total    已擷取的 spin 局數
  gift     nudge_pos 非零(饋贈)的局數      ← 目前的目標指標
  rulebad  倍率規則算不出來的局數          ← 壞消息
  unknown  封包裡沒解到的 protobuf 欄位種類 ← 壞消息
  capage   側錄串流幾秒沒更新              ← 斷線偵測
  giftvals 饋贈樣本明細(round_id:nudge_pos,分號分隔)

★設計要點★ 只做「讀檔 + 算」,不寫任何檔、不碰網路,所以可以高頻輪詢而不影響擷取。
實測 640 局約 0.08 秒。
"""
import json, glob, os, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'routex'))
import math_adapter as ma

GID = os.environ.get('GID', '696')
VAL = {9:1, 10:2, 11:3, 12:5, 13:10, 14:15, 15:20, 16:25, 17:50, 18:100, 19:500, 20:0}
KNOWN = {'SpinResult':{1,2,3,6,20,23}, 'BoardDetail':{1,2,3,4,5,6,7,8,10,12,13,15,18,19},
         'Reel':{1}, 'SymbolWindow':{1}, 'LineWin':{1,2,3,4}, 'PostNudge':{1,2},
         'BetInfo':{1,25,26}, 'Ante':{1}}
SUB = {('SpinResult',1):'BoardDetail', ('SpinResult',23):'BetInfo',
       ('BoardDetail',1):'Reel', ('BoardDetail',2):'SymbolWindow',
       ('BoardDetail',6):'LineWin', ('BoardDetail',19):'PostNudge',
       ('BetInfo',26):'Ante'}
unknown = set()


def scan(buf, msg):
    """忠實走過每個 protobuf 欄位,記下 schema 沒有的 —— 罕見狀態才會冒出的欄位
    就是靠這個抓到的(f4 連鎖、f10 饋贈加權符號都是這樣現形的)。"""
    for f, w, v in ma._fields(bytes(buf)):
        if f not in KNOWN.get(msg, set()):
            unknown.add(f'{msg}.f{f}')
            continue
        sub = SUB.get((msg, f))
        if sub and w == 2:
            scan(v, sub)


gift, bad, total = [], 0, 0
for fp in glob.glob(os.path.join(ROOT, 'games', GID, 'webcap/backend_raw/spins/*.json')):
    try:
        d = json.load(open(fp, encoding='utf-8'))
    except Exception:
        continue                      # 可能正在被 server 寫入,下一輪再算
    if d.get('type') != 0 or not d.get('payload_hex'):
        continue
    total += 1
    raw = bytes.fromhex(d['payload_hex'])
    scan(raw, 'SpinResult')
    b = ma.wire_to_math(raw)['board']
    if any(b['nudge_pos']):
        gift.append(f"{d['round_id']}:{b['nudge_pos']}")
    sl = b['window'][2:len(b['window']) - 2]
    if not any(x not in VAL for x in sl) and abs(sum(VAL[x] for x in sl) - b['multiplier']) > 1e-9:
        bad += 1

cap = os.path.join(ROOT, 'games', GID, 'webcap_exchanges.jsonl')
age = int(time.time() - os.path.getmtime(cap)) if os.path.exists(cap) else 99999
print(f"{total}|{len(gift)}|{bad}|{len(unknown)}|{age}|{';'.join(sorted(gift))}")
