const fs=require('fs'),path=require('path'),assert=require('assert');
const codecs=require('./load_codec.cjs'),pb=require('../runtime/node_modules/protobufjs/minimal');
function clean(v){if(Array.isArray(v))return v.map(clean);if(v&&typeof v==='object')return Object.fromEntries(Object.entries(v).filter(([k])=>k!=='_wire').map(([k,x])=>[k,clean(x)]));return v;}
const dir=path.join(__dirname,'../math');let count=0;
try{
for(const file of fs.readdirSync(dir).filter(n=>/^\d+\.json$/.test(n))){
 const obj=JSON.parse(fs.readFileSync(path.join(dir,file)));
 const r=pb.Reader.create(Buffer.from(obj._wire));let payload;
 while(r.pos<r.len){const tag=r.uint32();if(tag>>>3===1)payload=r.bytes();else r.skipType(tag&7);}
 const decoded=codecs.SpinAck.decode(payload);
 assert.deepStrictEqual(JSON.parse(JSON.stringify(codecs.SpinAck.toObject(decoded,{defaults:true,arrays:true}))),clean(obj.data));
 assert(Buffer.from(codecs.SpinAck.encode(decoded).finish()).equals(payload));count++;
}
assert(count>0);console.log(JSON.stringify({original_frontend_codec_verified:count}));
}catch(e){console.error(e.message);process.exit(1)}
