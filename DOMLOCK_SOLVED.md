# JILI Domain-Lock 白名單驗證 —— ★完全逆向 + 離線驗證★ (2026-09-04)

## 一句話
Jscrambler DomainLock 的白名單 = **301 項 salted hash**;每項 = `murmur3_x86_32(允許域名 ASCII, 該項6位seed)`。
離線完全重現、3 個真實域名獨立命中,並可為**任意域名偽造合法白名單項**。

## 結論(驗證邏輯)
- 白名單字串藏在 `bundle.24017.js`,由 **16 個字串片段**在 state-machine(`for(;С_Β!==96){switch(С_Β)}`)
  依 **68→27** 串接:`Ε6R ο6c V_q E3Κ Р8α о_Τ e1х с_ν A7ο А_V R$1 O7Α е1P α2j M_Α Z7T`。
  (片段切在**任意字元位置**,連 hash 都被切開,例:`ο6c` 尾 `5879410` + `V_q` 頭 `30` = hash `587941030`;
   使用者先前看到的開頭「30」不是計數,是被切開的 hash 尾 → 誤判為 count。)
- 組出的完整字串格式:`<<<n1,n2,n3,n4,n5,n6<HASH;<<<...`(`;` 分項,項內 `<` 分欄)。
  parser `Y9G`:`item.split('<')` → `[3]`=code(6 個負數 join `,`),`[4]`=HASH(有號十進位字串)。
- **★ code 解碼(`O4х`,關鍵、先前一直卡在這)**:每個負數 `n ∈ [-39,-30]` → 數字 **`n + 39`**。
  即 **`-30→9, -31→8, … , -39→0`**。6 個數字串起來 = **6 位十進位 seed**。
  (卡了很久是因為把方向猜反成 `-30→0`;真相是 `-30→9`。追 `O4х` state-machine 得
   `C1s += fromCharCode(A1К[i] - A8E + H2h)`,常數差使映射為 `n+39`。)
- **★ HASH = `MurmurHash3_x86_32(location.hostname 的 ASCII bytes, seed)`**,
  與 code-integrity 同一套常數:`c1=0xcc9e2d51 c2=0x1b873593 fmix=0x85ebca6b/0xc2b2ae35 mix=0xe6546b64`。
  輸入 = **原始 hostname、不做任何變形**(不加協定/斜線/大小寫/反轉)。
- **★ runtime 檢查**:對當前 `location.hostname` H,遍歷 301 項,
  只要 `murmur3(H, seed_i) === hash_i` 任一成立 → **放行**。seed 逐項不同(防預計算)。

## 已驗證命中(3 個真實域名,獨立中不同項 → 排除巧合)
| entry | hostname | seed | hash |
|---|---|---|---|
| #120 | `uat-wbgame.jlfafafa3.com`  | 255989 | `d3793411` |
| #77  | `wbgame.jlfafafa3.com`      | 157202 | `4c549366` |
| #123 | `test-wbgame.jlfafafa3.com` | 111230 | `9233be3f` |

## 工具
`routex/dl_domlock_solve.py`(自含,直接讀 `bundle.24017.js.orig`):
- `list` — dump 301 項 (index/seed/hash)
- `verify <hostname>` — 該域名是否在白名單、命中哪項
- `forge <hostname> [seed]` — 為任意域名產一筆合法 `<<<n1..n6<HASH`(seed 可自選;範例
  `mycasino.example.com seed=424242 → <<<-35,-37,-35,-37,-35,-37<454724720`)

## ★零改檔公開部署(路徑④,推薦)★
放行自有網域**完全不用改 bundle**——因為 DomainLock 讀**真** `location.hostname`,只要我們部署的
hostname 真的 murmur 撞到某個允許值即可。murmur3 對 input 也能代數反解(固定 `.base` 尾段、solve 出
label 首 4 字元、retry 到全 `[a-z0-9]`),**0.2 秒**就能為你控制的 base 域名生出撞中子網域:
```
dl_domlock_solve.py preimage myjili.example.com 4
  entry#0 seed=481498 hash=be5c6d5e => xkgywoa1ym2xb9syz.myjili.example.com  [OK]
  ...(murmur3(該子網域, seed_i) == hash_i,前向已驗)
```
固定漂亮前綴 + 短隨機尾:`dl_domlock_solve.py pretty <base> <prefix> [tail]`
```
dl_domlock_solve.py pretty dyson4092.com fortune
  ✓ fortune7gwmh1q6a.dyson4092.com  (撞中 entry#0)
```
一鍵本地跑:`./web_own.sh <base> [prefix]`(有前綴走 pretty)。
把遊戲(**未改動**的檔案)部署在該子網域下 → DomainLock 合法放行。
- **不觸 code-integrity / GameTampering**:一個 byte 都沒改。
- **不觸「unforgeable location」**:是**真域名**,不是 hook 偽造 location(那條才被守死)。
- ⇒ [[jili-domain-lock-analysis]] 判死的三路(輸入偽裝 / 改檔 / runtime hook)全部繞過;
  它把本路列為「反解 hash 表命中=週級深淵」只因當時雜湊未破,現在是十秒級。

### 部署前要實測的未驗風險
1. **伺服器端網域檢查?** DomainLock 的 POST 只是打 `/webservice/event/jscrambler`(telemetry/違規回報);
   但遊戲真正的 API(`LoginGame`/session)**是否在後端另檢 Origin/Referer 網域**尚未證。→ 部到撞中子網域、
   連真後端跑一次才知道。
2. **後端會話**:連真 operator 後端仍需合法 `ssoKey`(單次 game_url,見 [[jili-mock-server-pipeline]]);
   若只要自足 demo 則配 mock server + `INJECT_BUNDLE=1`(改的是 `polyfills.bundle`,**非** code-integrity
   檢查對象,故 OK,見 [[jili-patch-mechanism-solved]])。

## 備用路徑:就地 forge 清單項(需要時才用)
若哪天真要用「自訂/漂亮域名」而非撞中子網域,可 `forge <host> [seed]` 產等長 `<<<n1..n6<HASH` 項就地換掉
某現有項——但那會改 `bundle.24017.js` byte,需先確認 **code-integrity**(`О_O.toString()` 鏈式 murmur,
[[jili-integrity-murmur-re]])是否涵蓋清單 offset≈674061;若涵蓋還要併 hash-preserving forge(卡 `H_9`)。
路徑④ 不改檔,故**不需要**碰這關;此路備而不用。

## 待辦(僅備用路徑需要)
- [ ] runtime trace 定死 `m8ΚHyс9(...,О_O)` 的 `О_O` 是哪個函式、`toString()` source 是否含 offset 674061。
