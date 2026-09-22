const fs = require('fs');
const vm = require('vm');
const writeFile = fs.writeFileSync.bind(fs);
const rawWrite = (s) => { try { fs.writeSync(2, s + "\n"); } catch(e){} };
const code = fs.readFileSync('main.js', 'utf8');

const decoded = [];
const diag = { setterFired:0, tablesWrapped:0, bypassed:0, decoderCalls:0 };
const WRAP_KEYS = new Set(['192870','57123','168145','534367','ВА','В2Α']);

// 萬用 dummy：可呼叫、可索引、永遠自我延續（給查不到的模組硬撐用）
function mkDummy(){
  const f = function(){ return D; };
  const D = new Proxy(f, {
    get(t,k){ if(k===Symbol.toPrimitive)return ()=>0; if(k==='toString')return ()=>''; if(k==='valueOf')return ()=>0; if(k==='length')return 0; if(k===Symbol.iterator)return undefined; return D; },
    apply(){ return D; }, construct(){ return D; }, has(){ return true; }, set(){ return true; }
  });
  return D;
}

// 包解碼表：攔函式，記錄字串輸出
function wrapTable(obj){
  return new Proxy(obj, { get(t,k){ const v=t[k];
    if (typeof v==='function'){ return function(){ diag.decoderCalls++; const r=v.apply(t,arguments);
      if (typeof r==='string' && r.length>0 && r.length<400) decoded.push(r); return r; }; }
    return v; } });
}

// 包整個 P_feQ 登記表（hoisting 塞進來的 function）
function wrapRegistry(reg){
  return new Proxy(reg, {
    get(t,k){
      const ks = String(k);
      let v = t[k];
      if (v === undefined && /^[^0-9]/.test(ks) && ks.length<=3 && !(k in t)){
        // 疑似模組 id 查不到 → 硬撐給 dummy
        diag.bypassed++; return mkDummy();
      }
      if (WRAP_KEYS.has(ks) && v && (typeof v==='object'||typeof v==='function')){
        // 惰性包裝解碼表
        return wrapTable(v);
      }
      return v;
    },
    set(t,k,v){ t[k]=v; return true; },
    has(){ return true; },
    apply(t,thiz,args){ return Reflect.apply(t,thiz,args); }
  });
}

const sandbox = {};
let realP = undefined;
Object.defineProperty(sandbox, 'P_feQ', {
  configurable: false,
  get(){ return realP; },
  set(v){ diag.setterFired++; try{ realP = (v && (typeof v==='function'||typeof v==='object')) ? wrapRegistry(v) : v; }catch(e){ realP=v; } }
});
sandbox.globalThis=sandbox; sandbox.window=sandbox; sandbox.self=sandbox; sandbox.global=sandbox;
sandbox.console={log(){},warn(){},error(){},info(){},debug(){}};
sandbox.navigator={userAgent:'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36',language:'zh-CN',platform:'MacIntel',languages:['zh-CN']};
sandbox.location={href:'https://uat-wbgame.jlfafafa3.com/fg5/?ssoKey=x&gameID=696',host:'uat-wbgame.jlfafafa3.com',protocol:'https:',search:'?gameID=696',hostname:'uat-wbgame.jlfafafa3.com'};
sandbox.setTimeout=()=>0; sandbox.setInterval=()=>0; sandbox.clearTimeout=()=>{}; sandbox.clearInterval=()=>{}; sandbox.requestAnimationFrame=()=>0;
sandbox.System={register(){}, import(){return Promise.resolve({});}};
sandbox.performance={now:()=>0}; sandbox.Math=Math;
sandbox.crypto={getRandomValues:(a)=>{for(let i=0;i<(a&&a.length||0);i++)a[i]=i&255;return a;}, subtle:{}};
sandbox.document={createElement:()=>mkDummy(), getElementById:()=>null, documentElement:mkDummy(), addEventListener(){}, body:mkDummy(), head:mkDummy()};

const ctx = vm.createContext(sandbox);
try { vm.runInContext(code, ctx, {timeout:120000}); rawWrite('[eval] 完整跑完'); }
catch(e){ rawWrite('[eval] 拋錯: '+String(e).slice(0,120)); }
rawWrite('[diag] '+JSON.stringify(diag));
const uniq=[...new Set(decoded)];
rawWrite('[decoded] '+decoded.length+' (去重 '+uniq.length+')');
try{ writeFile('decoded_strings.json', JSON.stringify(uniq)); }catch(e){}
