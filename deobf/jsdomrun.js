const fs = require('fs');
const { JSDOM } = require('jsdom');
const rawWrite = (s) => { try { fs.writeSync(2, s + "\n"); } catch(e){} };

// 在 jsdom realm 內先跑的 setup script：安裝 P_feQ Proxy + 解碼捕捉
const setup = `
window.__decoded = [];
window.__diag = {setWrap:0, called:0};
var WRAP_KEYS = ['192870','57123','168145','534367','В2Α'];
function wrapTable(obj){
  return new Proxy(obj, { get:function(t,k){ var v=t[k];
    if (typeof v==='function'){ return function(){ var r=v.apply(t,arguments); window.__diag.called++;
      if (typeof r==='string' && r.length>0 && r.length<400) window.__decoded.push(r); return r; }; }
    return v; } });
}
var __store = {};
window.P_feQ = new Proxy(__store, {
  get:function(t,k){ return t[k]; },
  set:function(t,k,v){ if (WRAP_KEYS.indexOf(String(k))>=0 && v && (typeof v==='object'||typeof v==='function')){ window.__diag.setWrap++; try{v=wrapTable(v);}catch(e){} } t[k]=v; return true; },
  has:function(t,k){ return k in t; }
});
`;

const bundle = fs.readFileSync('main.js', 'utf8');
const html = `<!DOCTYPE html><html><head></head><body><canvas id="GameCanvas"></canvas></body></html>`;

const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'https://uat-wbgame.jlfafafa3.com/fg5/?ssoKey=x&gameID=696&domain_platform=x&gs=x',
  beforeParse(window) {
    // 補 jsdom 缺的 API
    window.WebGLRenderingContext = function(){};
    window.crypto = window.crypto || { getRandomValues:(a)=>{for(let i=0;i<(a&&a.length||0);i++)a[i]=i&255;return a;}, subtle:{} };
    window.requestAnimationFrame = ()=>0; window.cancelAnimationFrame=()=>{};
    window.performance = window.performance || { now:()=>0 };
    window.System = { register(){}, import(){return Promise.resolve({});} };
    const c = window.HTMLCanvasElement && window.HTMLCanvasElement.prototype;
    if (c) c.getContext = ()=>({ getExtension:()=>null, getParameter:()=>0, createBuffer:()=>({}), viewport(){}, clear(){} });
  }
});
const win = dom.window;
try { win.eval(setup); rawWrite('[setup] P_feQ proxy 安裝'); } catch(e){ rawWrite('[setup err] '+e); }
try { win.eval(bundle); rawWrite('[bundle] 完整跑完'); }
catch(e){ rawWrite('[bundle] 拋錯: '+String(e).slice(0,140)); }

const dec = win.__decoded || [];
const diag = win.__diag || {};
rawWrite('[diag] '+JSON.stringify(diag));
rawWrite('[decoded] '+dec.length);
const uniq = [...new Set(dec)];
fs.writeFileSync('decoded_strings.json', JSON.stringify(uniq));
rawWrite('[uniq] '+uniq.length+' 寫入 decoded_strings.json');
