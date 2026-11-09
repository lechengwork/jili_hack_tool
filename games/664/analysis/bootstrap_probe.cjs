const fs=require('fs'),vm=require('vm');
const s=fs.readFileSync(process.argv[2],'utf8'),pos=s.indexOf('var b4jkO$');
const acorn=require('../../../node_modules/acorn');const ast=acorn.parse(s,{ecmaVersion:'latest'});const hoist=ast.body.filter(n=>n.type==='FunctionDeclaration').map(n=>s.slice(n.start,n.end)).join(';');
const regs=[];const ctx=vm.createContext({console,System:{register(...a){regs.push(a)}},setTimeout(){},setInterval(){}});
try{vm.runInContext(s.slice(0,pos)+";"+hoist,ctx,{timeout:3000});console.log('prefix ready',pos);console.log(vm.runInContext('[45,40,256,94,314,281,155].map(n=>n6n4Q.Y51(n))',ctx));console.log(vm.runInContext('[87,183,194,198,73,99,167,214].map(n=>[n,n6n4Q.Y51(n)])',ctx));}catch(e){console.log(e.message)}
