#!/usr/bin/env python3
"""dl_dump.py — 定位 Jscrambler Domain Lock 檢查點(sudo,遊戲需卡在 myslot.test 的 lock 上)。

用 Frida 在 renderer 記憶體 scan 關鍵字,只撈命中點周圍的上下文(在 JS 端就轉成可讀字串再回傳,
避免巢狀 ArrayBuffer 序列化問題)。違規 session 裡 "DomainLock"、檢查/反制函式 source、允許網域清單
都會被解進記憶體。輸出印螢幕 + 存 /tmp/dl_hits.txt。

用法:先 ./dl_session.sh(CfT 開 myslot.test、等卡住)→ sudo ./.venv/bin/python dl_dump.py
"""
import frida, subprocess, sys, os, re, json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

NEEDLES = ['DomainLock', 'SendJscramblerLog', 'ClientDomain', 'ParentDomain',
           'hostname', 'location', 'ancestorOrigins']
CTX_BEFORE = 9000
CTX_AFTER  = 9000
MAX_HITS_PER_NEEDLE = 4

def hexpat(s, twobyte=False):
    b = s.encode('utf-16-le') if twobyte else s.encode('latin-1')
    return ' '.join('%02x' % c for c in b)

JS = r'''
var NEEDLES = %s;                 // [[label, hexpattern], ...]
var CB=%d, CA=%d, MAXH=%d;
function bufToStr(buf){           // ArrayBuffer -> 可讀字串(非可列印 -> '.')
  var u8 = new Uint8Array(buf), s = '';
  for (var k=0;k<u8.length;k++){ var c=u8[k]; s += (c>=32 && c<127) ? String.fromCharCode(c) : '.'; }
  return s;
}
rpc.exports.scan = function () {
  var out = [];
  var ranges = Process.enumerateRanges('rw-');
  NEEDLES.forEach(function (nd) {
    var label = nd[0], pat = nd[1], found = 0;
    for (var i = 0; i < ranges.length && found < MAXH; i++) {
      var r = ranges[i];
      if (r.file) continue;
      var matches;
      try { matches = Memory.scanSync(r.base, r.size, pat); } catch (e) { continue; }
      for (var j = 0; j < matches.length && found < MAXH; j++) {
        var a = matches[j].address;
        try {
          var start = a.sub(CB); if (start.compare(r.base) < 0) start = r.base;
          var buf = start.readByteArray(CB + CA);
          out.push({ label: label, addr: a.toString(), text: bufToStr(buf) });
          found++;
        } catch (e) {}
      }
    }
  });
  return out;
};
'''

KEEP = re.compile(r'DomainLock|Jscrambler|jscrambler|location|hostname|\.host|href|referrer|origin|'
                  r'jlfafafa|myslot|function|indexOf|test\(|match\(|split\(|===|!==|return|domain', re.I)

def renderers():
    o = subprocess.check_output(['ps', 'aux']).decode()
    rs = []
    for l in o.splitlines():
        if 'type=renderer' in l and ('chrome-mac-arm64' in l or 'Chrome for Testing' in l):
            p = l.split()
            try: rs.append((int(p[1]), int(p[5])))
            except (ValueError, IndexError): pass
    return sorted(rs, key=lambda x: -x[1])

def main():
    rs = renderers()
    if not rs:
        sys.exit('[!] 找不到 CfT renderer — 先 ./dl_session.sh 開遊戲、等卡住,再跑本 script(sudo)')
    needles = []
    for s in NEEDLES:
        needles.append([s + '(1b)', hexpat(s, False)])
        needles.append([s + '(2b)', hexpat(s, True)])
    jssrc = JS % (json.dumps(needles), CTX_BEFORE, CTX_AFTER, MAX_HITS_PER_NEEDLE)

    outf = open('/tmp/dl_hits.txt', 'w')
    total = 0
    for pid, rss in rs[:3]:
        try:
            se = frida.attach(pid)
            sc = se.create_script(jssrc); sc.load()
            hits = sc.exports_sync.scan()
        except Exception as e:
            print(f'[pid {pid}] attach/scan FAIL {e!r}'); continue
        print(f'[pid {pid} {rss//1024}MB] {len(hits)} 命中')
        for h in hits:
            try:
                total += 1
                head = f'\n===== {h["label"]} @ {h["addr"]} (pid {pid}) ====='
                print(head); outf.write(head + '\n')
                # 印命中點周圍所有「可讀字串片段」(>=5 連續、非幾乎全點),不過濾——
                # 讓允許網域 / 它讀的屬性(hostname/host/href) / 其他解碼字串一起浮出來。
                txt = h.get('text', '')
                seen_fr = set(); shown = 0
                for fr in re.findall(r'[\x20-\x7e]{5,}', txt):
                    if fr.count('.') > len(fr) * 0.8:          # 跳過幾乎全點(=二進位)
                        continue
                    key = fr[:60]
                    if key in seen_fr:
                        continue
                    seen_fr.add(key)
                    tag = ' <<<KEEP' if KEEP.search(fr) else ''
                    print('  ' + fr[:200] + tag); outf.write('  ' + fr[:200] + tag + '\n')
                    shown += 1
                    if shown >= 40:
                        break
            except Exception as e:
                outf.write(f'  (hit render err {e!r})\n')
        try: se.detach()
        except Exception: pass
    outf.close()
    print(f'\n[done] {total} 命中,完整存 /tmp/dl_hits.txt。把 DomainLock/SendJscramblerLog 附近那幾段貼給 Claude。')

if __name__ == '__main__':
    main()
