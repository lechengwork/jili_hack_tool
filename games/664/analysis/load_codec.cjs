const fs=require('fs'),vm=require('vm');const pb=require('../../545/runtime/node_modules/protobufjs/minimal');
const constants=JSON.parse(fs.readFileSync(__dirname+'/outer_constants.json','utf8'));
const guards={F5f:()=>false,T05:()=>false,D2D:()=>true,e78:()=>true};
const context=vm.createContext({...constants,W$v:guards,j4OEdZ:Array,r1L0xG:TypeError,v8DQF6:Object,S_ejLb:Number,f0DWRc:isFinite,M_fmrK:String,K54S7D:Boolean,A_L:null});
const factory=vm.runInContext('('+fs.readFileSync(__dirname+'/lj500Proto.factory.js','utf8')+')',context,{timeout:1000});
const m={exports:{}};factory({},name=>{if(name!=='protobufjs/minimal')throw Error(name);return pb;},m,{},{});
module.exports=m.exports.lj500Proto;
if(require.main===module)for(const [name,c]of Object.entries(module.exports)){console.log(name,Object.keys(c.prototype));fs.writeFileSync(__dirname+'/'+name+'.decode.js',c.decode.toString());}
