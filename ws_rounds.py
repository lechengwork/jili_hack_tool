import json,struct

def rv(b,i):
    s=0;r=0
    while True:
        x=b[i];i+=1;r|=(x&0x7f)<<s
        if not x&0x80:break
        s+=7
    return r,i

def fields(b):
    i=0;out=[]
    while i<len(b):
        try:key,i=rv(b,i)
        except IndexError:break
        f=key>>3;wt=key&7
        if wt==0:
            v,i=rv(b,i);out.append((f,0,v))
        elif wt==1:
            out.append((f,1,struct.unpack('<d',b[i:i+8])[0]));i+=8
        elif wt==2:
            ln,i=rv(b,i);out.append((f,2,b[i:i+ln]));i+=ln
        elif wt==5:
            out.append((f,5,struct.unpack('<f',b[i:i+4])[0]));i+=4
        else:break
    return out

def get(fs,fn,wt=None):
    for f,t,v in fs:
        if f==fn and (wt is None or t==wt):return v
    return None

def packed_doubles(bs):
    return [struct.unpack('<d',bs[i:i+8])[0] for i in range(0,len(bs)-7,8)]

rows=[]
for l in open('games/124/ws_session1.jsonl'):
    try:d=json.loads(l)
    except:continue
    if d.get('kind')=='ws_msg':
        h=d.get('hex') or ''
        if len(h)//2>2: rows.append((d['ts'],d['dir'],bytes.fromhex(h)))
rows.sort()

print("time-ordered cmd22 rounds (balance-delta corrected)\n")
prev_bal=None
for ts,dr,b in rows:
    fs=fields(b)
    if get(fs,1,0)!=22: continue
    body=get(fs,2,2)
    if not body: continue
    bf=fields(body)
    if dr=='SEND':
        inner=get(bf,1,2)
        if inner:
            ib=fields(inner)
            amt=get(ib,1,1); pos=get(ib,2,0)
            print(f"SEND bet   amount={amt} position={pos}  (f2={get(bf,2,0)} f3={get(bf,3,0)})")
        else:
            print(f"SEND roll  (f2={get(bf,2,0)} f3={get(bf,3,0)})  [{len(b)}B no-bet]")
    else:
        bal=get(bf,3,1); rid=get(bf,4,0)
        res=get(bf,1,2)
        rf=fields(res) if res else []
        win=get(rf,1,1)           # sometimes present
        a=get(rf,2,0); c=get(rf,3,0)
        arr=get(rf,5,2)
        arrd=packed_doubles(arr) if arr else None
        echo=get(bf,5,2)
        echo_s=''
        if echo:
            ef=fields(echo); echo_s=f"echo(amt={get(ef,1,1)},pos={get(ef,2,0)})"
        delta = (bal-prev_bal) if (bal is not None and prev_bal is not None) else None
        prev_bal=bal
        ds=f"{delta:+.3f}" if delta is not None else "?"
        print(f"RECV result bal={bal} Δ={ds} rid={rid} | res.f1(win?)={win} res.f2={a} res.f3={c} | {echo_s}")
        if arrd and len(arrd)<=13:
            print(f"           arr[{len(arrd)}]={[round(x,2) for x in arrd]}")

print("\n\n########## GameConfig(767B) 與 multibet(152/165B) ##########")
def deep(bs,ind=0,maxlen=0):
    for f,t,v in fields(bs):
        pad='  '*ind
        if t==2:
            # try text
            txt=None
            try:
                s=v.decode('utf-8')
                if s and all(32<=ord(c)<127 for c in s): txt=s
            except:pass
            if txt: print(f"{pad}f{f} str={txt!r}")
            elif len(v)%8==0 and len(v)>=8 and len(v)<=200:
                print(f"{pad}f{f} dbl[{len(v)//8}]={[round(x,3) for x in packed_doubles(v)]}")
            elif len(v)<=64 and ind<4:
                print(f"{pad}f{f} msg({len(v)}):"); deep(v,ind+1)
            else:
                print(f"{pad}f{f} bytes({len(v)})={v.hex()[:60]}")
        else:
            print(f"{pad}f{f} {'i' if t==0 else 'd'}={v}")

for ts,dr,b in rows:
    fs=fields(b); 
    if get(fs,1,0)!=22: continue
    body=get(fs,2,2); 
    if not body: continue
    if len(b) in (767,165,152,301,290):
        print(f"\n----- {dr} {len(b)}B -----")
        deep(body)
