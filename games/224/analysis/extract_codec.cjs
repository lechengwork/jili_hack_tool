const fs=require('fs'),acorn=require('../../../node_modules/acorn'),vm=require('vm');
const src=fs.readFileSync(__dirname+'/../static/aviator/assets/Game224/index.95fb8.js','utf8');
const ast=acorn.parse(src,{ecmaVersion:'latest'});
function walk(n,fn){if(!n||typeof n!=='object')return;fn(n);for(const v of Object.values(n)){if(Array.isArray(v))v.forEach(x=>walk(x,fn));else if(v&&typeof v==='object')walk(v,fn);}}
const found={};
walk(ast,n=>{if(n.type==='CallExpression'&&n.callee.type==='MemberExpression'&&n.callee.property.name==='define'){
 const f=n.arguments[1]; if(!f||f.type!=='FunctionExpression')return;
 const text=src.slice(f.start,f.end);
 for(const name of ['aviatorProto','fastProto'])if(text.includes('.'+name+'='))found[name]=text;
}});
for(const [name,text]of Object.entries(found)){
 fs.writeFileSync(__dirname+'/'+name+'.factory.js',text);
 const pb=require('../../545/runtime/node_modules/protobufjs/minimal');
 const factory=vm.runInNewContext('('+text+')',{});const mod={exports:{}};
 factory({},n=>{if(n!=='protobufjs/minimal')throw Error(n);return pb},mod);
 const codec=mod.exports[name];
 console.log(name,Object.keys(codec));
 for(const [k,v]of Object.entries(codec)){if(typeof v.decode==='function')fs.writeFileSync(__dirname+'/'+k+'.decode.js',v.decode.toString());else fs.writeFileSync(__dirname+'/'+k+'.json',JSON.stringify(v,null,2)||String(v));}
}
