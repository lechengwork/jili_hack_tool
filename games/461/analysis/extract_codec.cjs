const fs=require('fs'),acorn=require('../../../node_modules/acorn');
const source=fs.readFileSync(__dirname+'/game.fca3c.js.decoded.js','utf8');
const ast=acorn.parse(source,{ecmaVersion:'latest'});let factory;
function visit(n){
 if(!n||typeof n!=='object')return;
 if(n.type==='CallExpression'&&n.callee.type==='MemberExpression'&&n.callee.property.value==='define'&&n.arguments[1]?.type==='FunctionExpression'){
  const f=n.arguments[1],s=source.slice(f.start,f.end);
  if(s.includes('pirate2Proto')&&s.includes('protobufjs/minimal'))factory=s;
 }
 for(const value of Object.values(n)){if(Array.isArray(value))value.forEach(visit);else if(value&&typeof value==='object')visit(value);}
}
visit(ast);if(!factory)throw Error('pirate2Proto module factory not found');
fs.writeFileSync(__dirname+'/pirate2Proto.factory.js',factory+'\n');
console.log('Extracted pirate2Proto factory '+factory.length+' bytes');
