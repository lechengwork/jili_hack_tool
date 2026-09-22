const fs = require('fs');
const vm = require('vm');
const writeFile = fs.writeFileSync.bind(fs);
const rawWrite = (s) => { try { fs.writeSync(2, s + "\n"); } catch(e){} };
const code = fs.readFileSync('main.js', 'utf8');

const decoded = [];
const diag = {setWrap:0, fnReturned:0, called:0, retTypes:{}, totalSet:0, totalGet:0, setKeys:[]};
const WRAP_KEYS=new Set(['192870','57123','168145','534367','В2Α']);
function wrapTable(obj){
  return new Proxy(obj, {
    get(t, k){
      const v = t[k];
      if (typeof v === 'function'){
        diag.fnReturned++;
        return function(){
          diag.called++;
          const r = v.apply(t, arguments);
          const tp = typeof r; diag.retTypes[tp]=(diag.retTypes[tp]||0)+1;
          if (tp === 'string' && r.length>0 && r.length<400) decoded.push(r);
          return r;
        };
      }
      return v;
    }
  });
}

const store = {};
const sandbox = {};
sandbox.P_feQ = new Proxy(store, {
  get(t,k){ diag.totalGet++; return t[k]; },
  set(t,k,v){ diag.totalSet++; if(diag.setKeys.length<30)diag.setKeys.push(String(k)); if (WRAP_KEYS.has(String(k)) && v && (typeof v==='object'||typeof v==='function')){ diag.setWrap++; try{ v=wrapTable(v);}catch(e){} } t[k]=v; return true; },
  has(t,k){ return k in t; },
});
sandbox.globalThis=sandbox; sandbox.window=sandbox; sandbox.self=sandbox; sandbox.global=sandbox;
sandbox.console={log(){},warn(){},error(){},info(){},debug(){}};
sandbox.navigator={userAgent:'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36',language:'zh-CN',platform:'MacIntel',languages:['zh-CN']};
sandbox.location={href:'https://uat-wbgame.jlfafafa3.com/fg5/',host:'uat-wbgame.jlfafafa3.com',protocol:'https:',search:'',hostname:'uat-wbgame.jlfafafa3.com'};
sandbox.setTimeout=()=>0;sandbox.setInterval=()=>0;sandbox.clearTimeout=()=>{};sandbox.clearInterval=()=>{};sandbox.requestAnimationFrame=()=>0;
sandbox.System={register(){},import(){return Promise.resolve({});}};
sandbox.performance={now:()=>0}; sandbox.Math=Math;
sandbox.crypto={getRandomValues:(a)=>{for(let i=0;i<(a&&a.length||0);i++)a[i]=i&255;return a;},subtle:{}};
sandbox.document={createElement:()=>({style:{},getContext:()=>({}),appendChild(){},setAttribute(){}}),getElementById:()=>null,documentElement:{style:{}},addEventListener(){},body:{appendChild(){}},head:{appendChild(){}}};

const ctx=vm.createContext(sandbox);
try{ vm.runInContext(code, ctx, {timeout:120000}); rawWrite('[eval] 完整跑完'); }
catch(e){ rawWrite('[eval] 錯誤: '+String(e)); rawWrite('[stack] '+String(e.stack).split(String.fromCharCode(10)).slice(0,6).join(' || ')); }
rawWrite('[diag] '+JSON.stringify(diag));
rawWrite('[decoded] 攔到解碼字串: '+decoded.length);
// 去重
const uniq=[...new Set(decoded)];
rawWrite('[decoded] 去重後: '+uniq.length);
try{ writeFile('decoded_strings.json', JSON.stringify(uniq)); rawWrite('[write] decoded_strings.json'); }catch(e){ rawWrite('[write err]'+String(e).slice(0,60)); }
