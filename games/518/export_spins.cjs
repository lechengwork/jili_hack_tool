// Decode with the actual recovered frontend codec; verify by re-encoding every payload.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

class Reader {
  constructor(buf) { this.buf = Buffer.from(buf); this.pos = 0; this.len = this.buf.length; }
  static create(buf) { return new Reader(buf); }
  varint() {
    let value = 0n;
    for (let shift = 0n; shift < 70n; shift += 7n) {
      if (this.pos >= this.len) throw Error('Truncated varint');
      const byte = this.buf[this.pos++];
      value |= BigInt(byte & 127) << shift;
      if (!(byte & 128)) return value;
    }
    throw Error('Oversized varint');
  }
  uint32() { return Number(this.varint() & 0xffffffffn); }
  int32() { return this.uint32() | 0; }
  bool() { return this.varint() !== 0n; }
  double() {
    const value = this.buf.readDoubleLE(this.pos); this.pos += 8; return value;
  }
  bytes() {
    const size = this.uint32(), end = this.pos + size;
    if (end > this.len) throw Error('Truncated bytes');
    const value = this.buf.subarray(this.pos, end); this.pos = end; return value;
  }
  skipType(wire) {
    if (wire === 0) this.varint();
    else if (wire === 1) this.pos += 8;
    else if (wire === 2) this.bytes();
    else if (wire === 5) this.pos += 4;
    else throw Error('Unsupported wire type ' + wire);
    if (this.pos > this.len) throw Error('Truncated field');
  }
}

class Writer {
  constructor() { this.parts = []; this.stack = []; }
  static create() { return new Writer(); }
  varint(value) {
    let v = BigInt(value); const bytes = [];
    do { let b = Number(v & 127n); v >>= 7n; bytes.push(b | (v ? 128 : 0)); } while (v);
    this.parts.push(Buffer.from(bytes)); return this;
  }
  uint32(v) { return this.varint(v >>> 0); }
  int32(v) { return this.varint(v < 0 ? BigInt.asUintN(64, BigInt(v)) : BigInt(v)); }
  bool(v) { return this.uint32(v ? 1 : 0); }
  double(v) { const b = Buffer.alloc(8); b.writeDoubleLE(v); this.parts.push(b); return this; }
  fork() { this.stack.push(this.parts); this.parts = []; return this; }
  ldelim() {
    const b = this.finish(); this.parts = this.stack.pop();
    if (!this.parts) throw Error('Unmatched ldelim');
    this.uint32(b.length); this.parts.push(b); return this;
  }
  finish() { return Buffer.concat(this.parts); }
}

function fields(buf) {
  const r = new Reader(buf), result = new Map();
  while (r.pos < r.len) {
    const tag = r.uint32(), no = tag >>> 3, wire = tag & 7;
    if (!no || result.has(no)) throw Error('Unexpected duplicate/zero envelope field ' + no);
    let value;
    if (wire === 0) value = r.varint();
    else if (wire === 1) value = r.double();
    else if (wire === 2) value = r.bytes();
    else throw Error('Unexpected envelope wire type ' + wire);
    result.set(no, value);
  }
  return result;
}

const here = __dirname;
const session = process.argv[2] || fs.readFileSync(path.join(here, 'current_session.txt'), 'utf8').trim();
const context = vm.createContext({ Reader, Writer });
vm.runInContext(`
var _0x38dce6={}, _0x3fea8a, _0x523530=Reader, _0x2d28b2=Writer;
var _0x1fb4d5={emptyArray:[],isInteger:Number.isInteger};
var _0x19b91f={util:{toJSONOptions:{}}};
var _0x45af6b=function(){}, _0x3054=function(){};
` + fs.readFileSync(path.join(here, 'analysis/cjProto.expression.js'), 'utf8'), context, {timeout:1000});
const codec = context._0x38dce6.cjProto.SpinAck;
const rows = fs.readFileSync(path.join(session, 'export/exchanges_ordered.jsonl'), 'utf8')
  .trim().split('\n').map(JSON.parse).filter(r => r.type === 0 && r.ret === 0);
const stats = {spins:rows.length, byte_roundtrips:0, winning_spins:0, cascade_spins:0,
  free_feature_spins:0, buy_types:{}, ack_types:{}, bets:{}, special_fields:{}, max_stages:0};
const named = [], metadata = [];
for (const row of rows) {
  const envelope = fields(row.raw), payload = envelope.get(1);
  assert(Buffer.isBuffer(payload), 'Missing SpinAck');
  const message = codec.decode(payload);
  const encoded = Buffer.from(codec.encode(message).finish());
  assert(encoded.equals(payload), 'Frontend byte round-trip failed at seq=' + row.idx);
  stats.byte_roundtrips++;
  const data = codec.toObject(message, {defaults:true, arrays:true});
  const bet = fields(envelope.get(23));
  const special = {};
  for (const [no,value] of bet) if (no !== 1 && !(no === 25 && value.length === 0)) {
    special['f' + no + (Buffer.isBuffer(value) ? '_hex' : '')] = Buffer.isBuffer(value) ? value.toString('hex') : String(value);
    stats.special_fields[no] = (stats.special_fields[no] || 0) + 1;
  }
  assert(envelope.get(2).length === 0, 'Nonempty service requires a schema');
  assert.strictEqual(envelope.get(3) || 0, data.TotalWin, 'Envelope TotalWin mismatch');
  const id = String(envelope.get(20));
  assert(id.endsWith('518'), 'Unexpected round ID');
  const value = {data, service:{}, postMoney:envelope.get(6), roundIndexV2:id,
    spinReq:{bet:bet.get(1), special}};
  named.push([id,value]);
  metadata.push({idx:row.idx,roundIndexV2:id,payload_hex:payload.toString('hex'),
    response_payload_hex:Buffer.from(row.raw).toString('hex')});
  if (data.TotalWin > 0) stats.winning_spins++;
  if (data.RoundQueue.some(r => r.ComboStageData.length > 1)) stats.cascade_spins++;
  if (data.FreeTotalWin > 0 || data.RoundQueue.some(r => r.FreeRemainRound || r.FreeTotalRound || r.AddRounds)) stats.free_feature_spins++;
  for (const [bucket,key] of [['buy_types',data.BuyType],['ack_types',data.AckType],['bets',bet.get(1)]])
    stats[bucket][key] = (stats[bucket][key] || 0) + 1;
  stats.max_stages = Math.max(stats.max_stages, ...data.RoundQueue.map(r => r.ComboStageData.length));
}
assert.strictEqual(new Set(named.map(([id]) => id)).size, named.length, 'Duplicate round IDs');
const out = path.join(session, 'export/spins_named'); fs.mkdirSync(out, {recursive:true});
for (const [id,value] of named) fs.writeFileSync(path.join(out,id+'.json'), JSON.stringify(value,null,2)+'\n');
fs.writeFileSync(path.join(out,'all.jsonl'), named.map(([,v])=>JSON.stringify(v)+'\n').join(''));
fs.writeFileSync(path.join(session,'export/spin_wire_vectors.jsonl'), metadata.map(v=>JSON.stringify(v)+'\n').join(''));
fs.writeFileSync(path.join(session,'export/spin_summary.json'), JSON.stringify(stats,null,2)+'\n');
console.log(JSON.stringify(stats));
console.log('Named spins: '+out);
