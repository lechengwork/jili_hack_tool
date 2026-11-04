#!/usr/bin/env python3
"""Zero-dependency 518 math JSON <-> decrypted game payload adapter."""
import argparse
import json
import math
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
SCHEMA = json.loads((HERE / 'math_schema.json').read_text())


def varint(value):
    value &= (1 << 64) - 1
    out = bytearray()
    while value > 127:
        out.append((value & 127) | 128); value >>= 7
    out.append(value)
    return bytes(out)


def read_varint(buf, pos):
    value = 0
    for shift in range(0, 70, 7):
        if pos >= len(buf):
            raise ValueError('Truncated varint')
        byte = buf[pos]; pos += 1; value |= (byte & 127) << shift
        if byte < 128:
            return value, pos
    raise ValueError('Oversized varint')


def wire_fields(buf):
    pos = 0
    while pos < len(buf):
        tag, pos = read_varint(buf, pos)
        number, wire = tag >> 3, tag & 7
        if not number:
            raise ValueError('Invalid zero field')
        if wire == 0:
            value, pos = read_varint(buf, pos)
        elif wire in (1, 5):
            end = pos + (8 if wire == 1 else 4)
            if end > len(buf):
                raise ValueError('Truncated fixed field')
            value = buf[pos:end]; pos = end
        elif wire == 2:
            size, pos = read_varint(buf, pos); end = pos + size
            if end > len(buf):
                raise ValueError('Truncated bytes field')
            value = buf[pos:end]; pos = end
        else:
            raise ValueError('Unsupported wire type %s' % wire)
        yield number, wire, value


def fields(buf):
    result = {}
    for number, wire, value in wire_fields(buf):
        if number in result:
            raise ValueError('Duplicate envelope field %s' % number)
        result[number] = (wire, value)
    return result


def field(number, wire, value):
    return varint(number * 8 + wire) + (varint(len(value)) + value if wire == 2 else value)


def default(f):
    if f['repeated']:
        return []
    return False if f['type'] == 'bool' else 0


def decode_message(buf, name='SpinAck'):
    schema = {f['number']: f for f in SCHEMA[name]}
    result = {f['name']: default(f) for f in schema.values()}
    seen = set()
    for no, wire, value in wire_fields(buf):
        if no not in schema:
            raise ValueError('Unknown %s field %s; update the schema' % (name, no))
        f = schema[no]; typ = f['type']; key = f['name']
        if no in seen and not f['repeated']:
            raise ValueError('Duplicate scalar %s.%s' % (name, key))
        seen.add(no)
        if typ in SCHEMA:
            if wire != 2:
                raise ValueError('Expected message wire type')
            decoded = decode_message(value, typ)
        elif f['repeated'] and wire == 2:
            packed = []; pos = 0
            while pos < len(value):
                v, pos = read_varint(value, pos)
                packed.append((v & 0xffffffff) - (1 << 32) if v & (1 << 31) else v)
            result[key].extend(packed)
            continue
        elif typ == 'double':
            if wire != 1:
                raise ValueError('Expected double wire type')
            decoded = struct.unpack('<d', value)[0]
        else:
            if wire != 0:
                raise ValueError('Expected integer wire type')
            decoded = bool(value) if typ == 'bool' else ((value & 0xffffffff) - (1 << 32) if value & (1 << 31) else value)
        if f['repeated']:
            result[key].append(decoded)
        else:
            result[key] = decoded
    return result


def scalar(value, typ):
    if typ == 'bool':
        if type(value) is not bool:
            raise ValueError('Expected bool')
        return varint(int(value))
    if typ == 'int32':
        if type(value) is not int or not -(1 << 31) <= value < (1 << 31):
            raise ValueError('Expected int32')
        return varint(value)
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('Expected finite number')
    return struct.pack('<d', value)


def encode_message(obj, name='SpinAck'):
    schema = SCHEMA[name]
    if not isinstance(obj, dict) or set(obj) != {f['name'] for f in schema}:
        raise ValueError('%s requires exactly its documented fields' % name)
    out = bytearray()
    for f in sorted(schema, key=lambda f: f['number']):
        value = obj[f['name']]; typ = f['type']; no = f['number']
        if f['repeated']:
            if not isinstance(value, list):
                raise ValueError('%s.%s must be an array' % (name, f['name']))
            if typ in SCHEMA:
                for item in value:
                    out.extend(field(no, 2, encode_message(item, typ)))
            elif value:
                out.extend(field(no, 2, b''.join(scalar(v, typ) for v in value)))
        elif typ in SCHEMA:
            out.extend(field(no, 2, encode_message(value, typ)))
        else:
            encoded = scalar(value, typ)
            if value:
                out.extend(field(no, 1 if typ == 'double' else 0, encoded))
    return bytes(out)


def number(value, label):
    if type(value) not in (float, int) or not math.isfinite(value):
        raise ValueError('%s must be finite' % label)
    return value


def validate(env):
    if set(env) != {'data', 'service', 'postMoney', 'roundIndexV2', 'spinReq'}:
        raise ValueError('Expected the five-field math envelope')
    encode_message(env['data'])
    if env['service'] != {}:
        raise ValueError('Nonempty service has no verified schema')
    number(env['postMoney'], 'postMoney')
    rid = env['roundIndexV2']
    if not isinstance(rid, str) or not rid.isdigit() or not rid.endswith('518') or int(rid) >= 1 << 64:
        raise ValueError('roundIndexV2 must be a uint64 string ending in 518')
    req = env['spinReq']
    if set(req) != {'bet', 'special'} or number(req['bet'], 'bet') <= 0:
        raise ValueError('Expected positive bet and special')
    if not isinstance(req['special'], dict) or set(req['special']) - {'context23'}:
        raise ValueError('Unknown special field')
    if 'context23' in req['special']:
        encode_message(req['special']['context23'], 'Context23')
    data = env['data']
    if not data['RoundQueue']:
        raise ValueError('RoundQueue must contain at least one round')
    def same(a, b, label):
        if not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-8):
            raise ValueError('%s does not add up: %s != %s' % (label, a, b))
    for q in data['RoundQueue']:
        if not q['ComboStageData']:
            raise ValueError('Every round needs at least one stage')
        for stage in q['ComboStageData']:
            if [len(c['Col']) for c in stage['ComboStageSymbol']] != [3, 4, 5, 5, 4, 3]:
                raise ValueError('Keep the verified six-column board dimensions')
            same(sum(a['Win'] for a in stage['AwardDataVec']), stage['ComboStageWin'], 'stage award sum')
            if stage['ComboStageWin'] < 0 or any(a['Win'] < 0 for a in stage['AwardDataVec']):
                raise ValueError('Win amounts must be nonnegative')
        same(sum(c['ComboStageWin'] for c in q['ComboStageData']), q['RoundWin'], 'round stage sum')
    same(sum(q['RoundWin'] for q in data['RoundQueue']), data['TotalWin'], 'TotalWin')


def wire_to_math(buf):
    outer = fields(buf)
    if set(outer) - {1, 2, 3, 6, 20, 23}:
        raise ValueError('Unknown outer response field')
    def get(table, no, wire):
        w, value = table[no]
        if w != wire:
            raise ValueError('Wrong wire type at field %s' % no)
        return value
    data = decode_message(get(outer, 1, 2))
    if get(outer, 2, 2):
        raise ValueError('Nonempty service')
    bet = fields(get(outer, 23, 2))
    if set(bet) - {1, 23, 25} or get(bet, 25, 2):
        raise ValueError('Unknown bet information')
    special = {}
    if 23 in bet:
        special['context23'] = decode_message(get(bet, 23, 2), 'Context23')
    if 3 in outer and struct.unpack('<d', get(outer, 3, 1))[0] != data['TotalWin']:
        raise ValueError('Duplicated TotalWin differs')
    env = {'data': data, 'service': {}, 'postMoney': struct.unpack('<d', get(outer, 6, 1))[0],
           'roundIndexV2': str(get(outer, 20, 0)),
           'spinReq': {'bet': struct.unpack('<d', get(bet, 1, 1))[0], 'special': special}}
    validate(env)
    return env


def math_to_wire(env):
    validate(env)
    data = encode_message(env['data'])
    bet = field(1, 1, struct.pack('<d', env['spinReq']['bet']))
    if 'context23' in env['spinReq']['special']:
        bet += field(23, 2, encode_message(env['spinReq']['special']['context23'], 'Context23'))
    bet += field(25, 2, b'')
    out = field(1, 2, data) + field(2, 2, b'')
    if env['data']['TotalWin']:
        out += field(3, 1, struct.pack('<d', env['data']['TotalWin']))
    out += field(6, 1, struct.pack('<d', env['postMoney']))
    out += field(20, 0, varint(int(env['roundIndexV2']))) + field(23, 2, bet)
    return out


def selftest(directory=None):
    directory = Path(directory or HERE / 'math')
    vectors = [json.loads(l) for l in (directory / 'roundtrip_vectors.jsonl').read_text().splitlines() if l]
    for v in vectors:
        wire = bytes.fromhex(v['response_payload_hex'])
        env = wire_to_math(wire)
        if math_to_wire(env) != wire or encode_message(env['data']).hex() != v['payload_hex']:
            raise ValueError('Round-trip mismatch: ' + env['roundIndexV2'])
        sample = json.loads((directory / (env['roundIndexV2'] + '.json')).read_text())
        validate(sample)
    print('PASS: %s original payload and full-envelope byte round-trips; math JSON samples valid' % len(vectors))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--math-dir')
    ap.add_argument('--encode', help='Math JSON input; output is the decrypted game payload')
    ap.add_argument('--decode', help='Decrypted game payload input')
    ap.add_argument('--out')
    args = ap.parse_args()
    if args.selftest:
        selftest(args.math_dir)
    elif args.encode and args.out:
        Path(args.out).write_bytes(math_to_wire(json.loads(Path(args.encode).read_text())))
    elif args.decode and args.out:
        Path(args.out).write_text(json.dumps(wire_to_math(Path(args.decode).read_bytes()), indent=2) + '\n')
    else:
        ap.error('Use --selftest, or --encode/--decode with --out')
