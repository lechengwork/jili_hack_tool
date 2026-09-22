const fs = require('fs');
const vm = require('vm');
const writeFile = fs.writeFileSync.bind(fs);
const rawWrite = (s) => { try { fs.writeSync(2, s + "\n"); } catch(e){} };
const code = fs.readFileSync('main.js', 'utf8');

// 萬用 proxy：任何 get 回傳自己、可呼叫回傳自己、數字/字串索引皆可
function mkProxy(name){
  const f = function(){ return P; };
  const P = new Proxy(f, {
    get(t,k){
      if (k===Symbol.toPrimitive) return ()=>0;
      if (k==='toString') return ()=>'';
      if (k==='valueOf') return ()=>0;
      if (k===Symbol.iterator) return undefined;
      if (k==='length') return 0;
      return P;
    },
    apply(){ return P; },
    construct(){ return P; },
    has(){ return true; },
    set(){ return true; },
  });
  return P;
}

const sandbox = {};
sandbox.P_feQ = {};
sandbox.globalThis = sandbox; sandbox.window = sandbox; sandbox.self = sandbox; sandbox.global = sandbox;
sandbox.console = { log(){}, warn(){}, error(){}, info(){}, debug(){} };
sandbox.navigator = { userAgent:'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36', language:'zh-CN', platform:'MacIntel', languages:['zh-CN'], appVersion:'5.0' };
sandbox.location = { href:'https://uat-wbgame.jlfafafa3.com/fg5/', host:'uat-wbgame.jlfafafa3.com', protocol:'https:', search:'', hostname:'uat-wbgame.jlfafafa3.com' };
sandbox.setTimeout=()=>0; sandbox.setInterval=()=>0; sandbox.clearTimeout=()=>{}; sandbox.clearInterval=()=>{}; sandbox.requestAnimationFrame=()=>0;
sandbox.System = { register(){}, import(){return Promise.resolve({});} };
sandbox.performance = { now:()=>0 };
sandbox.crypto = { getRandomValues:(a)=>{for(let i=0;i<(a&&a.length||0);i++)a[i]=i&255; return a;}, subtle:{} };
sandbox.Math = Math;
// document/cc 等未定義的，用萬用 proxy 兜底
sandbox.document = mkProxy('document');
sandbox.cc = mkProxy('cc');
sandbox.__proxyFallback = mkProxy('g');

const ctx = vm.createContext(sandbox);
// 攔全域未定義變數：用 with + Proxy 讓任何未定義的讀取回傳 proxy
const wrapped = 'with(__gp){' + code + '}';
sandbox.__gp = new Proxy(sandbox, {
  has(){ return true; },
  get(t,k){ if (k in t) return t[k]; if (typeof k==='string' && (k==='undefined')) return undefined; return sandbox.__proxyFallback; },
});
try { vm.runInContext(wrapped, ctx, { timeout: 90000 }); rawWrite('[eval] 完整跑完'); }
catch (e) { rawWrite('[eval] 拋錯: ' + String(e).slice(0,120)); }

const P = sandbox.P_feQ;
let dataKeys=[]; try { dataKeys = Object.keys(P).filter(k=>Array.isArray(P[k])||typeof P[k]==='string'||(P[k]&&P[k].length>50)); } catch(e){}
rawWrite('[P_feQ] data-like keys: ' + dataKeys.slice(0,10).join(','));
let methods=[]; try{ methods = Object.keys(P).filter(k=>typeof P[k]==='function'); }catch(e){}
const out={};
for (const m of methods){ const strs=[]; for(let i=0;i<8000;i++){ try{const v=P[m](i); if(typeof v==='string'&&v.length>0&&v.length<256)strs.push([i,v]); }catch(e){} } if(strs.length>3)out[m]=strs; }
let total=0; for(const m in out)total+=out[m].length;
rawWrite('[dump] 字串總數: ' + total);
try{ writeFile('strings.json', JSON.stringify(out)); rawWrite('[dump] 已寫 strings.json'); }catch(e){ rawWrite('[write err]'+String(e).slice(0,60)); }
