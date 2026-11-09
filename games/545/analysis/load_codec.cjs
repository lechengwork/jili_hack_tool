const fs=require('fs'),vm=require('vm');
const pb=require('../runtime/node_modules/protobufjs/minimal');
const source=fs.readFileSync(__dirname+'/cc3x3Proto.factory.js','utf8');
const context=vm.createContext({_0xa130af(){},_0x2bfa(){},_0x44a436:null});
const factory=vm.runInContext('('+source+')',context,{timeout:1000});
const mod={exports:{}};
factory({},name=>{if(name!=='protobufjs/minimal')throw Error(name);return pb;},mod,{},{});
module.exports=mod.exports.cc3x3Proto;
if(require.main===module)for(const [name,codec] of Object.entries(module.exports)){
 console.log(name,Object.keys(codec.prototype));
 fs.writeFileSync(__dirname+'/'+name+'.decode.js',codec.decode.toString());
}
