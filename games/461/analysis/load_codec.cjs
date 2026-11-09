const fs=require('fs'),vm=require('vm');
const pb=require('../../545/runtime/node_modules/protobufjs/minimal');
const source=fs.readFileSync(__dirname+'/pirate2Proto.factory.js','utf8');
const context=vm.createContext({_0x259107(){},_0x46b7(){},_0x173367:null});
const factory=vm.runInContext('('+source+')',context,{timeout:1000});
const mod={exports:{}};
factory({},name=>{if(name!=='protobufjs/minimal')throw Error(name);return pb;},mod,{},{});
module.exports=mod.exports.pirate2Proto;
if(require.main===module)for(const [name,codec] of Object.entries(module.exports)){
 console.log(name,Object.keys(codec.prototype));
 fs.writeFileSync(__dirname+'/'+name+'.decode.js',codec.decode.toString());
}
