const fs=require('fs'),vm=require('vm'),acorn=require('../../../node_modules/acorn');
const s=fs.readFileSync(__dirname+'/../static/fg1000/assets/main/index.668c9.js','utf8');
const ast=acorn.parse(s,{ecmaVersion:'latest'}), start=ast.body.find(n=>n.type==='IfStatement').start;
const sandbox={console:{log(){},warn(){},error(){},info(){},debug(){}},navigator:{userAgent:'Mozilla/5.0 Chrome/156.0.0.0 Safari/537.36',language:'zh-CN',platform:'MacIntel'},location:{href:'https://uat-wbgame.jlfafafa3.com/fg1000/?gameID=807',host:'uat-wbgame.jlfafafa3.com',hostname:'uat-wbgame.jlfafafa3.com',protocol:'https:',search:'?gameID=807'},setTimeout(){return 0},setInterval(){return 0},clearTimeout(){},clearInterval(){},performance:{now(){return 0}}};

const ctx=vm.createContext(sandbox);vm.runInContext('window=globalThis;self=globalThis',ctx);
try{vm.runInContext(s.slice(0,226965)+';'+ast.body.filter(n=>n.type==='FunctionDeclaration').map(n=>s.slice(n.start,n.end)).join(';'),ctx,{timeout:5000});console.log('bootstrap OK',typeof sandbox.Y3fAA,Object.keys(sandbox.Y3fAA||{}));}catch(e){console.log('bootstrap error',String(e),e.stack?.split('\n').filter(x=>x.length<250).slice(0,8).join('\n'));}
try{console.log('simple',vm.runInContext('Y3fAA.D5n(146)',ctx,{timeout:1000}));console.log('test',vm.runInContext('Y3fAA.D5n(Y3fAA.c0V(343610,424192,Y3fAA.B9()[58](),58))',ctx,{timeout:1000}));}catch(e){console.log('decode error',String(e));}
