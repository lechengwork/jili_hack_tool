// Independent check with the ORIGINAL extracted frontend codec, not Python's encoder.
const fs=require('fs'),vm=require('vm'),path=require('path');
const pb=require('../../545/runtime/node_modules/protobufjs');
const context=vm.createContext({Kn:null});
const factory=vm.runInContext('('+fs.readFileSync(__dirname+'/protocol.factory.js','utf8')+')',context,{timeout:1000});
const mod={exports:{}};
factory({},name=>{if(name!=='protobufjs/minimal')throw Error(name);return pb;},mod);
const original=mod.exports.protocol;
const roundType=pb.parse(fs.readFileSync(__dirname+'/../math_200.proto','utf8'),{keepCase:true}).root.lookupType('pappu_math_200.Round');
const vectors=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
for(const v of vectors){
  const outer=original.Command.decode(Buffer.from(v.hex,'hex'));
  if(outer.type!==18)throw Error('not RoomEnd');
  const d=original.RoomEnd.decode(outer.data);
  if(d.win!==v.win||d.postCoin!==v.balance||d.pic!==v.winner||d.isBonus!==false)throw Error('edited result mismatch');
  if(JSON.stringify(Object.keys(d.reward))!==JSON.stringify([String(v.winner)])||!d.reward[v.winner])throw Error('reward mismatch');
  if(JSON.stringify(Array.from(d.bonus))!==JSON.stringify([0,...v.odds]))throw Error('final gross odds mismatch');
  const dto=roundType.fromObject(v.round);
  const err=roundType.verify(dto);if(err)throw Error(err);
  const restored=roundType.toObject(roundType.decode(roundType.encode(dto).finish()),{longs:String});
  if(restored.round_id!==v.round.round_id)throw Error('uint64 round ID precision loss');
}
console.log('Original Pappu frontend codec + clean math proto: '+vectors.length+' edited responses verified');
