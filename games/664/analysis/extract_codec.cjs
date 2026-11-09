const fs=require('fs'),acorn=require('../../../node_modules/acorn');const s=fs.readFileSync(__dirname+'/main.decoded.js','utf8');const ast=acorn.parse(s,{ecmaVersion:'latest'});
function walk(n,fn,parents=[]){if(!n||typeof n!=='object')return;fn(n,parents);for(const v of Object.values(n)){if(Array.isArray(v))v.forEach(x=>walk(x,fn,[...parents,n]));else if(v&&typeof v==='object')walk(v,fn,[...parents,n]);}}
let target,outer;walk(ast,(n,p)=>{if(n.type==='CallExpression'&&n.arguments[1]?.type==='FunctionExpression'&&s.slice(n.arguments[1].start,n.arguments[1].end).includes('.lj500Proto.Column.Row: array expected')){if(!target||n.arguments[1].end-n.arguments[1].start<target.end-target.start){target=n.arguments[1];outer=[...p].reverse().find(x=>x.type==='FunctionExpression');}}});
if(!target)throw Error('factory missing');
const vals={},conflicts=new Set();
function scan(n){if(!n||typeof n!=='object'||n===target)return;if(n.type==='AssignmentExpression'&&n.operator==='='&&n.left.type==='Identifier'&&n.right.type==='Literal'){
 const k=n.left.name,v=n.right.value;if(k in vals&&vals[k]!==v)conflicts.add(k);else vals[k]=v;
}for(const v of Object.values(n)){if(Array.isArray(v))v.forEach(scan);else if(v&&typeof v==='object')scan(v);}}
// Only outer bindings: do not collect other nested functions.
function scanOuter(n){if(!n||typeof n!=='object')return;if(n!==outer&&['FunctionExpression','FunctionDeclaration','ArrowFunctionExpression'].includes(n.type))return;
if(n.type==='AssignmentExpression'&&n.operator==='='&&n.left.type==='Identifier'&&n.right.type==='Literal'){const k=n.left.name,v=n.right.value;if(k in vals&&vals[k]!==v)conflicts.add(k);else vals[k]=v;}
for(const v of Object.values(n)){if(Array.isArray(v))v.forEach(scanOuter);else if(v&&typeof v==='object')scanOuter(v);}}
scanOuter(outer);for(const k of conflicts)delete vals[k];
fs.writeFileSync(__dirname+'/lj500Proto.factory.js',s.slice(target.start,target.end));fs.writeFileSync(__dirname+'/outer_constants.json',JSON.stringify(vals,null,2));
console.log('factory',target.end-target.start,'outer constants',Object.keys(vals).length,'conflicts',conflicts.size);
// Free identifiers (over-approximate, excluding properties and object keys).
const declared=new Set(target.params.map(x=>x.name));walk(target,n=>{if(n.type==='VariableDeclarator'&&n.id.type==='Identifier')declared.add(n.id.name);if(n.type==='FunctionDeclaration'&&n.id)declared.add(n.id.name);if(n.type==='FunctionExpression'&&n.id)declared.add(n.id.name);if(['FunctionExpression','FunctionDeclaration'].includes(n.type))n.params.forEach(x=>declared.add(x.name));});
const free=new Set();walk(target,(n,p)=>{if(n.type!=='Identifier'||declared.has(n.name)||n.name in vals)return;const par=p.at(-1);if(par?.type==='MemberExpression'&&par.property===n&&!par.computed)return;if(par?.type==='Property'&&par.key===n&&!par.computed)return;free.add(n.name)});console.log('unresolved',Array.from(free));
