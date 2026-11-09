const fs=require('fs'),acorn=require('../../../node_modules/acorn');
const source=fs.readFileSync(__dirname+'/index.ade01.js.decoded.js','utf8');
const ast=acorn.parse(source,{ecmaVersion:'latest'});let factory;
function visit(n){
 if(!n||typeof n!=='object')return;
 if(n.type==='CallExpression'&&n.callee.type==='MemberExpression'&&n.callee.property.value==='define'&&n.arguments[1]?.type==='FunctionExpression'){
  const f=n.arguments[1],s=source.slice(f.start,f.end);
  if(s.includes('rcProto2')&&s.includes('protobufjs/minimal'))factory=s;
 }
 for(const value of Object.values(n)){if(Array.isArray(value))value.forEach(visit);else if(value&&typeof value==='object')visit(value);}
}
visit(ast);if(!factory)throw Error('rcProto2 module factory not found');
fs.writeFileSync(__dirname+'/rcProto2.factory.js',factory+'\n');
console.log('Extracted rcProto2 factory '+factory.length+' bytes');
