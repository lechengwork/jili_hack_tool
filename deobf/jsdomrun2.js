const fs = require('fs');
const { JSDOM } = require('jsdom');
const rawWrite = (s) => { try { fs.writeSync(2, s + "\n"); } catch(e){} };
const bundle = fs.readFileSync('main.js', 'utf8');

// setup 與 bundle 合併：P_feQ 用 var 宣告成 bundle 作用域的全域
const setup = `
var __decoded = []; var __diag = {setWrap:0, called:0};
window.__decoded = __decoded; window.__diag = __diag;
var __WK = ['192870','57123','168145','534367','ВА'];
function __wrap(obj){ return new Proxy(obj,{get:function(t,k){var v=t[k];
  if(typeof v==='function')return function(){var r=v.apply(t,arguments);__diag.called++;
    if(typeof r==='string'&&r.length>0&&r.length<400)__decoded.push(r);return r;};return v;}});}
var __store={};
var P_feQ = new Proxy(__store,{get:function(t,k){return t[k];},
  set:function(t,k,v){ if(__WK.indexOf(String(k))>=0&&v&&(typeof v==='object'||typeof v==='function')){__diag.setWrap++;try{v=__wrap(v);}catch(e){}} t[k]=v;return true;},
  has:function(t,k){return true;}});
window.P_feQ = P_feQ;
`;
const html = `<!DOCTYPE html><html><head></head><body><canvas id="GameCanvas"></canvas></body></html>`;
const dom = new JSDOM(html, { runScripts:'outside-only', pretendToBeVisual:true,
  url:'https://uat-wbgame.jlfafafa3.com/fg5/?ssoKey=x&gameID=696&domain_platform=x&gs=x' });
const win = dom.window;
// 補缺 API
win.crypto = win.crypto || { getRandomValues:(a)=>{for(let i=0;i<(a&&a.length||0);i++)a[i]=i&255;return a;}, subtle:{} };
win.requestAnimationFrame=()=>0; win.cancelAnimationFrame=()=>{};
win.performance = win.performance||{now:()=>0};
win.WebGLRenderingContext=function(){};
try{ if(win.HTMLCanvasElement) win.HTMLCanvasElement.prototype.getContext=()=>({getExtension:()=>null,getParameter:()=>0,createBuffer:()=>({}),viewport(){},clear(){},enable(){},bindBuffer(){}}); }catch(e){}

try { win.eval(setup + "\n;" + bundle); rawWrite('[bundle] 完整跑完'); }
catch(e){ rawWrite('[bundle] 拋錯: '+String(e).slice(0,150)); }
const dec = win.__decoded||[]; 
rawWrite('[diag] '+JSON.stringify(win.__diag||{}));
rawWrite('[decoded] '+dec.length);
const uniq=[...new Set(dec)];
fs.writeFileSync('decoded_strings.json', JSON.stringify(uniq));
rawWrite('[uniq] '+uniq.length);
