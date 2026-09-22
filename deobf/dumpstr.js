const fs = require('fs');
const vm = require('vm');
// eval 前先存好乾淨的原語（bundle 會污染 prototype）
const writeFile = fs.writeFileSync.bind(fs);
const rawWrite = (s) => { try { fs.writeSync(2, s + "\n"); } catch(e){} };
const code = fs.readFileSync('main.js', 'utf8');

const sandbox = {};
sandbox.P_feQ = {};
sandbox.globalThis = sandbox; sandbox.window = sandbox; sandbox.self = sandbox; sandbox.global = sandbox;
sandbox.console = { log(){}, warn(){}, error(){}, info(){}, debug(){} };
sandbox.navigator = { userAgent:'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36', language:'zh-CN', platform:'MacIntel', languages:['zh-CN'] };
sandbox.document = { createElement:()=>({style:{},getContext:()=>({})}), getElementById:()=>null, documentElement:{style:{}}, addEventListener(){}, location:{} };
sandbox.location = { href:'https://uat-wbgame.jlfafafa3.com/fg5/', host:'uat-wbgame.jlfafafa3.com', protocol:'https:', search:'' };
sandbox.setTimeout=()=>0; sandbox.setInterval=()=>0; sandbox.clearTimeout=()=>{}; sandbox.clearInterval=()=>{};
sandbox.System = { register(){}, import(){return Promise.resolve({});} };
sandbox.WebAssembly = { instantiate(){return Promise.resolve({});} };
sandbox.performance = { now:()=>0 };
sandbox.crypto = { getRandomValues:(a)=>a, subtle:{} };

const ctx = vm.createContext(sandbox);
try { vm.runInContext(code, ctx, { timeout: 90000 }); rawWrite('[eval] 完整跑完'); }
catch (e) { rawWrite('[eval] 中途拋錯（正常）: ' + String(e).slice(0,100)); }

const P = sandbox.P_feQ;
let methods=[]; try { methods = Object.keys(P).filter(k => typeof P[k]==='function'); } catch(e){}
rawWrite('[P_feQ] 方法數: ' + methods.length);

const out = {};
for (const m of methods) {
  const strs = [];
  for (let i = 0; i < 8000; i++) {
    try { const v = P[m](i); if (typeof v==='string' && v.length>0 && v.length<256) strs.push([i, v]); } catch(e){}
  }
  if (strs.length > 3) out[m] = strs;
}
let total=0; for (const m in out) total += out[m].length;
rawWrite('[dump] 字串總數: ' + total + '  方法: ' + Object.keys(out).join(','));
try { writeFile('strings.json', JSON.stringify(out)); rawWrite('[dump] 已寫 strings.json'); }
catch(e){ rawWrite('[write err] ' + String(e).slice(0,80)); }
