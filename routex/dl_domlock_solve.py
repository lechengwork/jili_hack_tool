#!/usr/bin/env python3
# dl_domlock_solve.py — ★SOLVED★ JILI domain-lock 白名單驗證,完全逆向 + 離線驗證 + 偽造。
#
# 破解結論(2026-09-04,3 個真實域名獨立命中,排除巧合):
#   白名單 = 301 項,存在 bundle.24017.js 內、由 16 個字串片段在 state-machine(switch С_Β)
#   依序 68→27 串接:Ε6R ο6c V_q E3Κ Р8α о_Τ e1х с_ν A7ο А_V R$1 O7Α е1P α2j M_Α Z7T。
#   組出字串格式:  <<<n1,n2,n3,n4,n5,n6<HASH ; <<<... (以 ";" 分隔項,項內 "<" 分欄)
#   parser(Y9G): item.split('<')[3]=code(6 個負數 join ','),[4]=HASH(有號十進位字串)。
#   ★ code 解碼(O4х,關鍵!): 每個負數 n∈[-39,-30] → 數字 (n+39)。即 -30→9, -31→8 … -39→0。
#      (先前一直卡住是因為把方向猜反成 -30→0;真相是 -30→9。)
#      6 個數字串起來 = 6 位十進位 seed。
#   ★ HASH = MurmurHash3_x86_32( location.hostname 的 ASCII bytes, seed )。
#      同一套 murmur 常數:c1=0xcc9e2d51 c2=0x1b873593 fmix=0x85ebca6b/0xc2b2ae35 mix=0xe6546b64。
#   ★ runtime 檢查:對當前 location.hostname H,遍歷 301 項,若 murmur3(H, seed_i)===hash_i 任一成立 → 放行。
#      (每項是「某個允許域名在其 seed 下的 salted hash」;seed 逐項不同以防預計算。)
#
# 已驗證命中:
#   #120 uat-wbgame.jlfafafa3.com   seed=255989 hash=d3793411
#   #77  wbgame.jlfafafa3.com       seed=157202 hash=4c549366
#   #123 test-wbgame.jlfafafa3.com  seed=111230 hash=9233be3f
#
# 用法:
#   ./dl_domlock_solve.py list                      # dump 301 項(index/seed/hash)
#   ./dl_domlock_solve.py verify <hostname>         # 該域名是否在白名單(命中哪項)
#   ./dl_domlock_solve.py forge <hostname> [seed]   # 為任意域名產生一筆合法 <<<...<HASH 項(可指定 seed)
#
# 部署備註:驗證邏輯已完全解;要讓自有公開域名過關,只需清單裡有一筆 murmur3(ourhost,seed)==hash。
#   就地把某現有項換成 forge 出來的等長項即可,唯一剩餘關卡 = bundle 的 code-integrity(О_O.toString()
#   鏈式 murmur,見 [[jili-integrity-murmur-re]])是否涵蓋清單位元組(offset≈674061);若涵蓋需同時
#   做 hash-preserving forge,若不涵蓋則直接改。內部用 jlfafafa-hosts 部署(呈現已白名單的 hostname)則零改檔。
import sys, os, re

_CHUNKS = os.path.join(os.path.dirname(__file__), "..", "game_site_backup",
    "uat-wbgame.jlfafafa3.com", "astarte2", "3.6", "web-mobile", "src", "chunks")
# 優先 .orig(開發樹乾淨備份);交接包通常只帶 .js(未改過,白名單相同)-> 退回 .js。可用 DL_BUNDLE 覆寫。
_ORIG = os.path.join(_CHUNKS, "bundle.24017.js.orig")
BUNDLE = os.environ.get("DL_BUNDLE") or (_ORIG if os.path.exists(_ORIG)
                                         else os.path.join(_CHUNKS, "bundle.24017.js"))
FRAG_ORDER = ["Ε6R","ο6c","V_q","E3Κ","Р8α","о_Τ","e1х","с_ν","A7ο","А_V",
              "R$1","O7Α","е1P","α2j","M_Α","Z7T"]
M = 0xffffffff

def murmur3(data, seed):
    c1=0xcc9e2d51; c2=0x1b873593
    rotl=lambda x,r: ((x<<r)|(x>>(32-r)))&M
    mul =lambda a,b: (a*b)&M
    h1=seed&M; n=len(data); nb=n//4
    for b in range(nb):
        i=b*4
        k1=(data[i]|data[i+1]<<8|data[i+2]<<16|data[i+3]<<24)&M
        k1=mul(k1,c1); k1=rotl(k1,15); k1=mul(k1,c2)
        h1^=k1; h1=rotl(h1,13); h1=(mul(h1,5)+0xe6546b64)&M
    tail=nb*4; rem=n&3; k1=0
    if rem==3: k1^=data[tail+2]<<16
    if rem>=2: k1^=data[tail+1]<<8
    if rem>=1:
        k1^=data[tail]; k1=mul(k1,c1); k1=rotl(k1,15); k1=mul(k1,c2); h1^=k1
    h1^=n
    h1^=h1>>16; h1=mul(h1,0x85ebca6b); h1^=h1>>13; h1=mul(h1,0xc2b2ae35); h1^=h1>>16
    return h1&M

def load_list():
    s=open(BUNDLE, encoding="utf-8").read()
    def getval(name):
        esc=re.escape(name); best=None
        for m in re.finditer(esc+r'=(["\'])((?:(?!\1)[^\\]|\\.)*)\1', s):
            v=m.group(2)
            if best is None or len(v)>len(best): best=v
        return best
    full="".join(getval(n) for n in FRAG_ORDER)
    assert full.startswith("<<<"), "組裝失敗(不以 <<< 開頭)"
    entries=[]
    for it in full[3:].split(";<<<"):
        code_s,hash_s=it.rsplit("<",1)
        neg=[int(x) for x in code_s.split(",")]
        assert len(neg)==6 and all(-39<=n<=-30 for n in neg), it
        seed=int("".join(str(n+39) for n in neg))    # ★ n+39
        entries.append((neg, seed, int(hash_s)&M))
    return entries

def seed_to_negs(seed):
    ds=str(seed).zfill(6)
    assert len(ds)==6, "seed 必須 <= 6 位(0..999999)"
    return [int(d)-39 for d in ds]                    # 反解:digit → n=digit-39

def to_signed(h): return h-(1<<32) if h>=(1<<31) else h

# ───────── preimage:為「自有 base 域名」構造會撞中白名單的 <label>.<base> hostname ─────────
# 用 murmur 可逆性代數構造(非暴力):固定尾段(.base)+ solve 出 label 首 4 字元,retry 到全 [a-z0-9]。
# => DomainLock 讀真 location.hostname 就撞中允許值,合法放行,零 bundle 改動。
import random as _rnd, string as _str
_C=0xe6546b64; _INV5=pow(5,-1,1<<32); _IC1=pow(0xcc9e2d51,-1,1<<32); _IC2=pow(0x1b873593,-1,1<<32)
_IA=pow(0x85ebca6b,-1,1<<32); _IB=pow(0xc2b2ae35,-1,1<<32)
_LBL=_str.ascii_lowercase+_str.digits
def _rl(x,r): return ((x<<r)|(x>>(32-r)))&M
def _rr(x,r): return ((x>>r)|(x<<(32-r)))&M
def _ml(a,b): return (a*b)&M
def _ixsr(y,s):
    x=0
    for i in range(31,-1,-1):
        xi=(y>>i)&1
        if i+s<32: xi^=(x>>(i+s))&1
        x|=(xi<<i)
    return x
def _fmix_inv(h):
    h=_ixsr(h,16); h=_ml(h,_IB); h=_ixsr(h,13); h=_ml(h,_IA); h=_ixsr(h,16); return h&M
def _km(w): return _ml(_rl(_ml(w,0xcc9e2d51),15),0x1b873593)
def _km_inv(km): return _ml(_rr(_ml(km,_IC2),15),_IC1)
def _blk_inv(ha,km): return (_rr(_ml((ha-_C)&M,_INV5),13)^km)&M
def _blk_fwd(h,km):  return (_ml(_rl((h^km)&M,13),5)+_C)&M
def _word(bs,i): return (bs[i]|bs[i+1]<<8|bs[i+2]<<16|bs[i+3]<<24)&M
def _tailmix(bs):
    n=len(bs); rem=n&3; t=(n//4)*4
    if rem==0: return 0
    k=0
    if rem==3: k^=bs[t+2]<<16
    if rem>=2: k^=bs[t+1]<<8
    if rem>=1: k^=bs[t]
    return _km(k)

def make_preimage(base, seed, target_hash, label_len=16, tries=500000):
    suffix="."+base; suf=list(suffix.encode())
    if label_len<8: label_len=8
    N=label_len+len(suffix); label_len+=(4-N%4)%4; N=label_len+len(suffix)
    m=N//4; T=_fmix_inv(target_hash)^N
    for _ in range(tries):
        filler=[ord(_rnd.choice(_LBL)) for _ in range(label_len-4)]
        full=[0,0,0,0]+filler+suf
        h=T
        for b in range(m-1,0,-1): h=_blk_inv(h,_km(_word(full,b*4)))
        km0=(seed ^ _rr(_ml((h-_C)&M,_INV5),13))&M
        w0=_km_inv(km0); b0=[(w0>>(8*k))&0xff for k in range(4)]
        if all(chr(x) in _LBL for x in b0):
            host=bytes(b0+filler).decode()+suffix
            assert murmur3(list(host.encode()),seed)==target_hash
            return host
    return None

def make_preimage_pretty(base, prefix, seed, target_hash, min_tail=3, tries=500000):
    """label = <prefix><短隨機尾>,使 murmur3(label.base, seed)==target_hash。
    prefix 固定漂亮;隨機尾 = filler + 4 個 solve 字元(全 [a-z0-9])。"""
    prefix="".join(c for c in prefix.lower() if c in _LBL)     # 前綴淨化成 DNS 合法
    suffix="."+base; suf=list(suffix.encode()); pre=list(prefix.encode())
    p=len(pre); f=max(min_tail,0)
    while (p+f)%4!=0: f+=1                                     # 對齊:solve 區塊落在 4-邊界
    sb=(p+f)//4                                                # solve 區塊 index
    for _ in range(tries):
        filler=[ord(_rnd.choice(_LBL)) for _ in range(f)]
        full=pre+filler+[0,0,0,0]+suf
        N=len(full); nb=N//4
        T=(_fmix_inv(target_hash)^N^_tailmix(full))&M         # h_afterblocks
        for b in range(nb-1, sb, -1):                         # 反推 solve 之後的固定 block → Hs
            T=_blk_inv(T,_km(_word(full,b*4)))
        A=seed&M                                              # 正推 solve 之前(prefix+filler)→ A
        for b in range(0, sb):
            A=_blk_fwd(A,_km(_word(full,b*4)))
        km=(A ^ _rr(_ml((T-_C)&M,_INV5),13))&M                # 解 solve block
        w=_km_inv(km); b4=[(w>>(8*k))&0xff for k in range(4)]
        if all(chr(x) in _LBL for x in b4):
            host=bytes(pre+filler+b4).decode()+suffix
            assert murmur3(list(host.encode()),seed)==target_hash
            return host
    return None

def main():
    cmd=sys.argv[1] if len(sys.argv)>1 else "list"
    entries=load_list()
    if cmd=="list":
        print(f"# {len(entries)} 項")
        for i,(neg,seed,h) in enumerate(entries):
            print(f"{i:3d}  seed={seed:06d}  hash={h:08x} ({to_signed(h)})  negs={neg}")
    elif cmd=="verify":
        host=sys.argv[2]; b=list(host.encode("latin-1"))
        hit=[(i,seed,h) for i,(neg,seed,h) in enumerate(entries) if murmur3(b,seed)==h]
        if hit:
            for i,seed,h in hit:
                print(f"✓ WHITELISTED  {host}  -> entry#{i} seed={seed:06d} hash={h:08x}")
        else:
            print(f"✗ NOT in whitelist: {host}")
    elif cmd=="forge":
        host=sys.argv[2]; b=list(host.encode("latin-1"))
        if len(sys.argv)>3:
            seed=int(sys.argv[3]); h=murmur3(b,seed)
        else:
            seed=0; h=murmur3(b,0)
        negs=seed_to_negs(seed)
        item="<<<"+",".join(str(n) for n in negs)+"<"+str(to_signed(h))
        print(f"# forge whitelist entry for {host}")
        print(f"#   seed={seed:06d}  hash={h:08x} (signed {to_signed(h)})")
        print(f"#   驗證: murmur3('{host}'.ascii, {seed}) == 0x{h:08x}")
        print(f"item_string = {item!r}")
        print(f"#   插入清單即放行該域名(需處理 code-integrity,見檔頭部署備註)")
    elif cmd=="preimage":
        # ★零改檔部署★:為自有 base 域名構造會撞中白名單的子網域(DomainLock 合法過,不動 bundle)
        base=sys.argv[2]; n=int(sys.argv[3]) if len(sys.argv)>3 else 5
        print(f"# base(你控制的域名)= {base}")
        print(f"# 構造 {n} 個會撞中白名單的子網域(部署遊戲於其上 → DomainLock 讀真 hostname 就過,零 bundle 改動):")
        for i,(neg,seed,h) in enumerate(entries):
            if i>=n: break
            host=make_preimage(base, seed, h)
            ok = host and murmur3(list(host.encode()),seed)==h
            print(f"  entry#{i:3d} seed={seed:06d} hash={h:08x}  =>  {host}   [{'OK' if ok else 'FAIL'}]")
    elif cmd=="pretty":
        # ★固定漂亮前綴 + 短隨機尾★:preimage <base> <prefix> [tail_len]
        base=sys.argv[2]; prefix=sys.argv[3]; tail=int(sys.argv[4]) if len(sys.argv)>4 else 3
        print(f"# base={base}  prefix='{prefix}'  隨機尾長≈{tail}+4")
        for i,(neg,seed,h) in enumerate(entries):
            host=make_preimage_pretty(base, prefix, seed, h, min_tail=tail)
            if host and murmur3(list(host.encode()),seed)==h:
                print(f"  ✓ {host}   (撞中 entry#{i} seed={seed:06d} hash={h:08x})")
                break
        else:
            print("  ✗ 找不到(試試加長 tail_len 或換 prefix)")
    else:
        print(__doc__)

if __name__=="__main__":
    main()
