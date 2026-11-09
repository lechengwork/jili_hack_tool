const fs=require('fs'),acorn=require('../../../node_modules/acorn'),codec=require('./load_codec.cjs');
function walk(n,fn){if(!n||typeof n!=='object')return;fn(n);for(const v of Object.values(n)){if(Array.isArray(v))v.forEach(x=>walk(x,fn));else if(v&&typeof v==='object')walk(v,fn);}}
const prop=n=>n?.type==='MemberExpression'?(n.computed?n.property.value:n.property.name):undefined;
const schema={};
for(const [name,c] of Object.entries(codec)){
 const ast=acorn.parse('('+c.decode.toString()+')',{ecmaVersion:'latest'});let sw;walk(ast,n=>{if(n.type==='SwitchStatement')sw=n;});
 schema[name]=[];
 for(const cs of sw.cases){if(!cs.test)continue;
  let field,type;let repeated=false;
  walk(cs,n=>{
   if(n.type==='MemberExpression'&&Object.hasOwn(c.prototype,prop(n))&&prop(n)!=='toJSON')field??=prop(n);
   if(n.type==='CallExpression'){
    const p=prop(n.callee);
    if(p==='push')repeated=true;
    if(['int32','double','bool','string'].includes(p))type=p;
    if(p==='decode')type=prop(n.callee.object);
   }
  });
  if(!field||!type)throw Error('Unresolved '+name+'.'+cs.test.value);
  schema[name].push({number:cs.test.value,name:field,type,repeated});
 }
}
fs.writeFileSync(__dirname+'/../math_schema.json',JSON.stringify(schema,null,2)+'\n');
let proto='syntax = "proto3";\npackage rc2_573;\n// Extracted from the original frontend codec. No enum meanings inferred.\n';
for(const [name,fields]of Object.entries(schema)){proto+='\nmessage '+name+' {\n';for(const f of fields)proto+='  '+(f.repeated?'repeated ':'')+f.type+' '+f.name+' = '+f.number+';\n';proto+='}\n';}
fs.writeFileSync(__dirname+'/../rc2_573.proto',proto);console.log(schema);
