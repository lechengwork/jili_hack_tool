import json,struct,sys

def rv(b,i):
    s=0;r=0
    while True:
        x=b[i];i+=1;r|=(x&0x7f)<<s
        if not x&0x80:break
        s+=7
    return r,i

def parse(b,depth=0):
    """generic protobuf → list of (field, wtype, value)"""
    i=0;out=[]
    while i<len(b):
        try:
            key,i=rv(b,i)
        except IndexError:break
        f=key>>3; wt=key&7
        if wt==0:
            v,i=rv(b,i); out.append((f,'varint',v))
        elif wt==1:
            raw=b[i:i+8];i+=8
            d=struct.unpack('<d',raw)[0] if len(raw)==8 else None
            out.append((f,'f64',d))
        elif wt==2:
            ln,i=rv(b,i); sub=b[i:i+ln];i+=ln
            # try nested; if it looks like text keep text
            txt=None
            try:
                t=sub.decode('utf-8')
                if all(32<=ord(c)<127 or c in '\t' for c in t) and t: txt=t
            except:pass
            nested=None
            if not txt:
                try: nested=parse(sub,depth+1)
                except:nested=None
            out.append((f,'len',{'raw_len':ln,'text':txt,'nested':nested,'hex':sub.hex()[:40]}))
        elif wt==5:
            raw=b[i:i+4];i+=4; out.append((f,'f32',struct.unpack('<f',raw)[0]))
        else:
            break
    return out

def show(fields,ind=0):
    for f,t,v in fields:
        pad='  '*ind
        if t=='len' and isinstance(v,dict):
            if v['text'] is not None:
                print(f"{pad}f{f} str = {v['text']!r}")
            elif v['nested']:
                print(f"{pad}f{f} msg({v['raw_len']}):")
                show(v['nested'],ind+1)
            else:
                print(f"{pad}f{f} bytes({v['raw_len']}) = {v['hex']}")
        else:
            print(f"{pad}f{f} {t} = {v}")

rows=[]
for l in open('games/124/ws_session1.jsonl'):
    try:d=json.loads(l)
    except:continue
    if d.get('kind')=='ws_msg':
        h=d.get('hex') or ''
        if len(h)//2>2: rows.append((d['ts'],d['dir'],bytes.fromhex(h)))
rows.sort()
# Focus: cmd 22 game frames
n=0
for ts,dr,b in rows:
    f=parse(b)
    cmd=None
    for fl,t,v in f:
        if fl==1 and t=='varint': cmd=v
    if cmd==22:
        n+=1
        if n>14: break
        print(f"\n===== {dr}  cmd={cmd}  ({len(b)}B) =====")
        show(f)
