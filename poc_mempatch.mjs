import fs from 'fs';
const wasmBytes = fs.readFileSync('games/696/crypto.wasm');
const REPLS = JSON.parse(fs.readFileSync('routex/wasm_pub_patches.json'));  // [{orig,new}]

// ── ① toString-preserving shim on WebAssembly.instantiate ──
const orig = WebAssembly.instantiate;
let captured = null;
const shim = function instantiate(...a){
  const r = orig.apply(this, a);
  return Promise.resolve(r).then(res => { captured = res.instance || res; return res; });
};
// 讓 .toString() 仍回原生字串(Jscrambler 靠這偵測)
Object.defineProperty(shim, 'toString', { value: orig.toString.bind(orig) });
WebAssembly.instantiate = shim;
console.log('[shim] instantiate.toString() =', String(WebAssembly.instantiate).slice(0,60).replace(/\n/g,' '));
console.log('[shim] 看得出被包裝嗎?', /native code/.test(String(WebAssembly.instantiate)) ? '否(顯示 native code)✓' : '是(露餡)✗');

// ── ② 用 catch-all stub imports 實例化(只為拿 instance+memory,不跑 login) ──
const stub = () => 0;
const imports = new Proxy({}, { get: () => new Proxy({}, { get: () => stub }) });
let instance;
try {
  const res = await WebAssembly.instantiate(wasmBytes, imports);
  instance = res.instance;
} catch(e){ console.log('[!] instantiate 失敗:', e.message); process.exit(1); }

// ── ③ 拿 exports.memory,讀 linear memory ──
const mem = instance.exports.memory;
console.log('[mem] instance.exports.memory 存在?', !!mem, mem ? `(${mem.buffer.byteLength} bytes = ${mem.buffer.byteLength/65536} pages)` : '');
if(!mem){ console.log('[!] 沒 export memory,此路不通'); process.exit(1); }
const u8 = new Uint8Array(mem.buffer);

// ── ④ 在 +1048576 找 8 個 orig chunk,改成 new,讀回驗證 ──
const PUB_OFF = 1048576;
function find(sub, from, span=16384){
  for(let i=from;i<from+span-sub.length;i++){ let ok=true; for(let j=0;j<sub.length;j++) if(u8[i+j]!==sub[j]){ok=false;break;} if(ok) return i; }
  return -1;
}
let patched=0, notfound=0, verified=0;
for(const r of REPLS){
  const oa=[...Buffer.from(r.orig,'hex')], na=[...Buffer.from(r.new,'hex')];
  const at=find(oa, PUB_OFF);
  if(at<0){ notfound++; continue; }
  u8.set(na, at);                       // ★ 純 JS 定點改記憶體
  // 讀回
  let ok=true; for(let j=0;j<na.length;j++) if(u8[at+j]!==na[j]){ok=false;break;}
  if(ok){ patched++; verified++; }
}
console.log(`[patch] 8 chunk: 找到並改+讀回成功=${verified}  找不到=${notfound}`);
console.log(verified===REPLS.length
  ? '\n★ PoC 成功:純 JS 拿到 instance.exports.memory、在 +1048576 定點改掉 8 個 pub chunk 並讀回確認。Frida 可拿掉(卡點只剩「真遊戲裡怎麼捕獲 instance」)。'
  : `\n△ 部分:改了 ${verified}/${REPLS.length}(可能 data segment 在此本地實例的偏移不同,但機制成立)`);
