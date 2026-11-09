const fs = require('fs'), vm = require('vm');
const acorn = require('../../../node_modules/acorn');
// Shared third-party protobuf runtime only; no other game's schema is loaded.
const pb = require('../../545/runtime/node_modules/protobufjs/minimal');
const source = fs.readFileSync(__dirname + '/protocol.factory.js', 'utf8');
const context = vm.createContext({Kn: null});
const factory = vm.runInContext('(' + source + ')', context, {timeout: 1000});
const mod = {exports: {}};
factory({}, name => {if(name !== 'protobufjs/minimal') throw Error(name); return pb;}, mod);
const codec = mod.exports.protocol;
const prop = n => n?.type === 'MemberExpression' ? n.computed ? n.property.value : n.property.name : null;
function walk(n, fn) {if(!n || typeof n !== 'object') return; fn(n); for(const v of Object.values(n)) {if(Array.isArray(v)) v.forEach(x=>walk(x,fn)); else if(v && typeof v === 'object') walk(v,fn);}}
const schema = {}, enums = {};
for(const [name, c] of Object.entries(codec)) {
  if(typeof c !== 'function') {enums[name] = c; continue;}
  const ast = acorn.parse('(' + c.decode.toString() + ')', {ecmaVersion: 'latest'});
  let sw;
  walk(ast, n => {if(!sw && n.type === 'SwitchStatement') sw = n;});
  schema[name] = [];
  for(const cs of sw.cases) {
    if(!cs.test) continue;
    let field, type, repeated = false;
    walk(cs, n => {
      if(n.type === 'MemberExpression' && Object.hasOwn(c.prototype, prop(n))) field ??= prop(n);
      if(n.type === 'CallExpression') {
        const p = prop(n.callee);
        if(p === 'push') repeated = true;
        if(['int32','uint32','uint64','double','bool','string','bytes'].includes(p) && !(type && typeof codec[type] === 'function')) type = p;
        if(p === 'decode') type = prop(n.callee.object);
      }
    });
    if(name === 'RoomEnd' && cs.test.value === 2) {type = 'RewardEntry'; repeated = true;}
    if(!field || !type) throw Error('Unresolved ' + name + '.' + cs.test.value);
    schema[name].push({number: cs.test.value, name: field, type: type === 'bytes' ? 'opaque' : type, repeated});
  }
}
schema.RewardEntry = [{number:1,name:'key',type:'int32',repeated:false},{number:2,name:'value',type:'bool',repeated:false}];
fs.writeFileSync(__dirname + '/../math_schema.json', JSON.stringify(schema,null,2)+'\n');
fs.writeFileSync(__dirname + '/enums.json', JSON.stringify(enums,null,2)+'\n');
let proto = 'syntax = "proto3";\npackage pappu_200;\n// From original Pappu frontend codec; reward map represented as repeated entries.\n';
for(const [name, fields] of Object.entries(schema)) {
  proto += '\nmessage ' + name + ' {\n';
  for(const f of fields) proto += '  '+(f.repeated?'repeated ':'')+(f.type==='opaque'?'bytes':f.type)+' '+f.name+' = '+f.number+';\n';
  proto += '}\n';
}
fs.writeFileSync(__dirname+'/../pappu_200.proto',proto);
// math_200.proto is the separate clean public DTO, maintained with the math module.
console.log('Pappu schema:',Object.keys(schema).length,'messages');
