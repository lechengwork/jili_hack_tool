const fs=require('fs'),assert=require('assert');
const codec=require('./load_codec.cjs');
const pb=require('../../545/runtime/node_modules/protobufjs/minimal');
const clean=v=>Array.isArray(v)?v.map(clean):v&&typeof v==='object'?Object.fromEntries(Object.entries(v).filter(([k])=>k!=='_wire').map(([k,x])=>[k,clean(x)])):v;
try {
 const obj=JSON.parse(fs.readFileSync(0,'utf8'));
 const r=pb.Reader.create(Buffer.from(obj._wire));let payload;
 while(r.pos<r.len){const tag=r.uint32();if(tag>>>3===1)payload=r.bytes();else r.skipType(tag&7);}
 assert(payload,'Missing game payload');
 const decoded=codec.SpinAck.decode(payload);
 assert.deepStrictEqual(JSON.parse(JSON.stringify(codec.SpinAck.toObject(decoded,{defaults:true,arrays:true}))),clean(obj.data));
 assert(Buffer.from(codec.SpinAck.encode(decoded).finish()).equals(payload),'Original pirate2Proto byte mismatch');
} catch(e) { console.error(e.message);process.exit(1); }
