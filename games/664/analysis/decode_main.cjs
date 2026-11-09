const fs=require('fs'),acorn=require('../../../node_modules/acorn');
const source=fs.readFileSync(__dirname+'/../static/lj500/assets/main/index.e931c.js','utf8');
const strings=JSON.parse(fs.readFileSync(__dirname+'/main_strings.json','utf8'));const ast=acorn.parse(source,{ecmaVersion:'latest'}),edits=[];
function walk(n,fn){if(!n||typeof n!=='object')return;fn(n);for(const v of Object.values(n)){if(Array.isArray(v))v.forEach(x=>walk(x,fn));else if(v&&typeof v==='object')walk(v,fn)}}
walk(ast,n=>{if(n.type==='CallExpression'&&n.callee.type==='MemberExpression'&&['W14','V8B'].includes(n.callee.property.name)&&n.arguments.length===1&&n.arguments[0].type==='Literal'&&typeof n.arguments[0].value==='number'){
 const v=strings[n.arguments[0].value];if(typeof v==='string')edits.push([n.start,n.end,JSON.stringify(v)]);
}});
let s=source;for(const [a,b,v]of edits.sort((a,b)=>b[0]-a[0]))s=s.slice(0,a)+v+s.slice(b);
fs.writeFileSync(__dirname+'/main.decoded.js',s);console.log('replaced',edits.length);
const ast2=acorn.parse(s,{ecmaVersion:'latest'});let matches=[];
walk(ast2,n=>{if(n.type==='CallExpression'&&n.callee.type==='MemberExpression'&&(n.callee.property.value==='define'||n.callee.property.name==='define')){
 for(const arg of n.arguments){if(arg.type==='FunctionExpression'){
  const code=s.slice(arg.start,arg.end);if(code.includes('lj500Proto')&&code.includes('protobufjs/minimal'))matches.push(code);
 }}
}});
matches.sort((a,b)=>a.length-b.length);console.log('factories',matches.map(x=>x.length));if(matches.length)fs.writeFileSync(__dirname+'/lj500Proto.factory.js',matches[0]);
