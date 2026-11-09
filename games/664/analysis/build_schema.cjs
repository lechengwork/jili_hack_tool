const fs=require('fs'),acorn=require('../../../node_modules/acorn'),codec=require('./load_codec.cjs');
const vals=JSON.parse(fs.readFileSync(__dirname+'/outer_constants.json','utf8'));const fsrc=fs.readFileSync(__dirname+'/lj500Proto.factory.js','utf8');
function walk(n,fn){if(!n||typeof n!=='object')return;fn(n);for(const v of Object.values(n)){if(Array.isArray(v))v.forEach(x=>walk(x,fn));else if(v&&typeof v==='object')walk(v,fn)}}
const fact=acorn.parse('('+fsrc+')',{ecmaVersion:'latest'}).body[0].expression;
function local(n){if(!n||typeof n!=='object'||['FunctionExpression','FunctionDeclaration','ArrowFunctionExpression'].includes(n.type))return;
if(n.type==='AssignmentExpression'&&n.left.type==='Identifier'&&n.right.type==='Literal'&&typeof n.right.value==='string')vals[n.left.name]=n.right.value;
for(const v of Object.values(n)){if(Array.isArray(v))v.forEach(local);else if(v&&typeof v==='object')local(v)}}
local(fact.body);
const strings={},conflict=new Set();walk(fact,n=>{if(n.type==='AssignmentExpression'&&n.left.type==='Identifier'&&n.right.type==='Literal'&&typeof n.right.value==='string'){const k=n.left.name,v=n.right.value;if(k in strings&&strings[k]!==v)conflict.add(k);else strings[k]=v}});for(const [k,v]of Object.entries(strings))if(!conflict.has(k))vals[k]=v;

const prop=n=>n?.type==='MemberExpression'?(n.computed?(n.property.type==='Literal'?n.property.value:vals[n.property.name]):n.property.name):undefined;
const schema={};
for(const [name,c]of Object.entries(codec)){
 const ast=acorn.parse('('+c.decode.toString()+')',{ecmaVersion:'latest'});let sw;walk(ast,n=>{if(n.type==='SwitchStatement')sw=n});schema[name]=[];
 for(const cs of sw.cases){if(!cs.test)continue;let field,type;let repeated=false;
 walk(cs,n=>{if(n.type==='MemberExpression'&&Object.hasOwn(c.prototype,prop(n))&&prop(n)!=='toJSON')field??=prop(n);
 if(n.type==='CallExpression'){const p=prop(n.callee);if(p==='push')repeated=true;if(['int32','double','bool','string','uint64'].includes(p))type=p;if(p==='decode')type=prop(n.callee.object)}});
 if(!field||!type)throw Error('Unresolved '+name+'.'+cs.test.value+' '+field+' '+type);schema[name].push({number:cs.test.value,name:field,type,repeated});}
}
fs.writeFileSync(__dirname+'/../math_schema.json',JSON.stringify(schema,null,2)+'\n');
let proto='syntax = "proto3";\npackage lj500_664;\n// Fields derived from this game original lj500Proto. No enum meanings inferred.\n';
for(const [name,fields]of Object.entries(schema)){proto+='\nmessage '+name+' {\n';for(const f of fields)proto+='  '+(f.repeated?'repeated ':'')+f.type+' '+f.name+' = '+f.number+';\n';proto+='}\n'}fs.writeFileSync(__dirname+'/../lj500_664.proto',proto);console.log(schema);
