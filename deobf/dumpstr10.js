const fs=require('fs'), vm=require('vm');
const writeFile=fs.writeFileSync.bind(fs);
const rawWrite=(s)=>{try{fs.writeSync(2,s+"\n");}catch(e){}};
let code=fs.readFileSync('main.js','utf8');
// 源碼補丁：把 function P_feQ( 改名，消除 hoisting clobber
code = code.replace('function P_feQ(', 'function P_feQ_REAL(');

const setup = `
var __decoded=[]; var __diag={setWrap:0,bypass:0,calls:0};
var __WK={'192870':1,'57123':1,'168145':1,'534367':1,'ВА':1,'В2Α':1};
function __mkDummy(){ var f=function(){return D;}; var D=new Proxy(f,{get:function(t,k){ if(k===Symbol.toPrimitive)return function(){return 0;}; if(k==='toString')return function(){return '';}; if(k==='valueOf')return function(){return 0;}; if(k==='length')return 0; if(k===Symbol.iterator)return undefined; return D;},apply:function(){return D;},construct:function(){return D;},has:function(){return true;},set:function(){return true;}}); return D; }
function __wrapTable(obj){ return new Proxy(obj,{get:function(t,k){ var v=t[k]; if(typeof v==='function'){ return function(){ __diag.calls++; var r=v.apply(t,arguments); if(typeof r==='string'&&r.length>0&&r.length<400)__decoded.push(r); return r; }; } return v; }}); }
function __wrapReg(reg){ return new Proxy(reg,{
  get:function(t,k){ var ks=(''+k); var v=t[k];
    if(__WK[ks]&&v&&(typeof v==='object'||typeof v==='function'))return __wrapTable(v);
    if(v===undefined&&!(k in t)&&typeof k==='string'&&/^[^0-9]/.test(ks)&&ks.length<=4){ __diag.bypass++; return __mkDummy(); }
    return v; },
  set:function(t,k,v){ if(__WK[(''+k)])__diag.setWrap++; t[k]=v; return true; },
  has:function(){return true;},
  apply:function(t,thiz,args){ try{return Reflect.apply(t,thiz,args);}catch(e){return __mkDummy();} }
}); }
var P_feQ = __wrapReg(P_feQ_REAL);
`;

const sandbox={};
sandbox.String=String; sandbox.Object=Object; sandbox.Array=Array; sandbox.JSON=JSON;
sandbox.Proxy=Proxy; sandbox.Reflect=Reflect; sandbox.Symbol=Symbol; sandbox.Number=Number;
sandbox.Boolean=Boolean; sandbox.Function=Function; sandbox.Error=Error; sandbox.TypeError=TypeError;
sandbox.RegExp=RegExp; sandbox.Date=Date; sandbox.Promise=Promise; sandbox.parseInt=parseInt;
sandbox.parseFloat=parseFloat; sandbox.isNaN=isNaN; sandbox.encodeURIComponent=encodeURIComponent;
sandbox.decodeURIComponent=decodeURIComponent; sandbox.Map=Map; sandbox.Set=Set; sandbox.WeakMap=WeakMap;
sandbox.ArrayBuffer=ArrayBuffer; sandbox.Uint8Array=Uint8Array; sandbox.DataView=DataView;
sandbox.globalThis=sandbox;sandbox.window=sandbox;sandbox.self=sandbox;sandbox.global=sandbox;
sandbox.console={log(){},warn(){},error(){},info(){},debug(){}};
sandbox.navigator={userAgent:'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36',language:'zh-CN',platform:'MacIntel',languages:['zh-CN']};
sandbox.location={href:'https://uat-wbgame.jlfafafa3.com/fg5/?gameID=696',host:'uat-wbgame.jlfafafa3.com',protocol:'https:',search:'?gameID=696',hostname:'uat-wbgame.jlfafafa3.com'};
sandbox.setTimeout=()=>0;sandbox.setInterval=()=>0;sandbox.clearTimeout=()=>{};sandbox.clearInterval=()=>{};sandbox.requestAnimationFrame=()=>0;
sandbox.System={register(){},import(){return Promise.resolve({});}};
sandbox.performance={now:()=>0};sandbox.Math=Math;
sandbox.crypto={getRandomValues:(a)=>{for(let i=0;i<(a&&a.length||0);i++)a[i]=i&255;return a;},subtle:{}};
sandbox.document={createElement:()=>({style:{},getContext:()=>null,appendChild(){},setAttribute(){}}),getElementById:()=>null,documentElement:{style:{}},addEventListener(){},body:{appendChild(){}},head:{appendChild(){}}};
const ctx=vm.createContext(sandbox);
try{ vm.runInContext(setup+"\n;"+code, ctx, {timeout:120000}); rawWrite('[eval] 完整跑完'); }
catch(e){ rawWrite('[eval] 拋錯: '+String(e).slice(0,120)); }
rawWrite('[diag] '+JSON.stringify(sandbox.__diag||{}));
const dec=sandbox.__decoded||[]; const uniq=[...new Set(dec)];
rawWrite('[decoded] '+dec.length+' (uniq '+uniq.length+')');
try{ writeFile('decoded_strings.json', JSON.stringify(uniq)); }catch(e){}
