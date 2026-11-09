const fs=require('fs'),vm=require('vm');
const pb=require('../../545/runtime/node_modules/protobufjs/minimal');
const source=fs.readFileSync(__dirname+'/rcProto2.factory.js','utf8');
const context=vm.createContext({_0x300dd0(){},_0xdac0(){},_0x19da3c:null});
const factory=vm.runInContext('('+source+')',context,{timeout:1000});
const mod={exports:{}};
factory({},name=>{if(name!=='protobufjs/minimal')throw Error(name);return pb;},mod,{},{});
module.exports=mod.exports.rcProto2;
if(require.main===module)for(const [name,codec] of Object.entries(module.exports)){
 console.log(name,Object.keys(codec.prototype));
 fs.writeFileSync(__dirname+'/'+name+'.decode.js',codec.decode.toString());
}
