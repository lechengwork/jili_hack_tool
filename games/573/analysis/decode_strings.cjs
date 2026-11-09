// String-table inspection only; System.register declarations are not executed.
const fs=require('fs'),vm=require('vm'),acorn=require('../../../node_modules/acorn');
const path=require('path');
const file=process.argv[2];
if(!file)throw Error('Provide a local bundle path');
const source=fs.readFileSync(file,'utf8');
const ast=acorn.parse(source,{ecmaVersion:'latest'});
const ctx=vm.createContext({System:{register(){}}});
vm.runInContext(source,ctx,{timeout:3000});
const names=new Set();
for(const match of source.matchAll(/(_0x[\da-f]+)\s*=\s*(_0x[\da-f]+)\s*[,;]/g)) {
 try {if(vm.runInContext('typeof '+match[2],ctx)==='function')names.add(match[1]);}catch{}
}
for(const item of ast.body)if(item.type==='FunctionDeclaration')names.add(item.id.name);
let added=true;
while(added){added=false;for(const m of source.matchAll(/(_0x[\da-f]+)\s*=\s*(_0x[\da-f]+)\s*[,;]/g)){if(names.has(m[2])&&!names.has(m[1])){names.add(m[1]);added=true;}}}
const replacements=[];
function visit(n){
 if(!n||typeof n!=='object')return;
 if(n.type==='CallExpression'&&n.callee.type==='Identifier'&&names.has(n.callee.name)&&n.arguments.length===1&&n.arguments[0].type==='Literal'&&typeof n.arguments[0].value==='number'){
  // local aliases resolve to the primary string mapper in this obfuscator family
  const candidates=[n.callee.name,...names];
  for(const candidate of candidates){try{
   const value=vm.runInContext(candidate+'('+n.arguments[0].value+')',ctx,{timeout:30});
   if(typeof value==='string'){replacements.push([n.start,n.end,JSON.stringify(value)]);break;}
  }catch{}}
 }
 for(const value of Object.values(n)){if(Array.isArray(value))value.forEach(visit);else if(value&&typeof value==='object')visit(value);}
}
visit(ast);
let result=source;
for(const [start,end,value] of replacements.sort((a,b)=>b[0]-a[0]))result=result.slice(0,start)+value+result.slice(end);
const out=path.join(__dirname,path.basename(file)+'.decoded.js');fs.writeFileSync(out,result);
console.log(JSON.stringify({file,out,replacements:replacements.length}));
