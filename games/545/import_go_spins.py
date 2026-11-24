#!/usr/bin/env python3
"""Convert g1836 translator spin-*.json (Go JILI format) into 545 replay math JSON."""
import argparse
import json
from pathlib import Path
from math_adapter import SCHEMA, math_to_wire

HERE = Path(__file__).resolve().parent
GO_DIR = Path(r'C:\lechengwork\math-go\lc-game-math-slot\lib\slot\game\g1836')
REPEATED = {f['name'] for fields in SCHEMA.values() for f in fields if f['repeated']}
# Observed pairing in captured samples: f26 absent -> Extra 0, empty f26 -> Extra 1, f26.f1=1 -> Extra 2.
FEATURE_BY_EXTRA = {0: {}, 1: {'selector': 0}, 2: {'selector': 1}}


def null_lists(value):
    # Go marshals nil slices as null; the codec expects [] for repeated fields.
    if isinstance(value, dict):
        return {k: ([] if k in REPEATED and v is None else null_lists(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [null_lists(v) for v in value]
    return value


def has_ww_collect_with_jp(data):
    # JILI symbol 2 is JP; the frontend has crashed on boards where a WW collects while a JP sits on the board.
    return any(stage.get('CollectList') and any(2 in col['Col'] for col in stage['Symbol'])
               for stage in data.get('RoundInfo') or [])


def convert(go):
    extra = go['spinReq'].get('Extra', 0)
    if extra not in FEATURE_BY_EXTRA:
        raise ValueError('Unknown spinReq.Extra %r' % extra)
    return {'data': null_lists(go['data']), 'service': [], 'postMoney': go['postMoney'],
            'roundIndexV2': go['roundIndexV2'],
            'spinReq': {'bet': go['spinReq']['bet'], 'context': [], 'featureOption': FEATURE_BY_EXTRA[extra]}}


ap = argparse.ArgumentParser()
ap.add_argument('--src', default=str(GO_DIR))
ap.add_argument('--out', default=str(HERE / 'my_math'))
ap.add_argument('--only-ww-jp', action='store_true', help='keep only rounds with a WW collect and a JP on the board')
args = ap.parse_args()
out = Path(args.out)
converted = []
for path in sorted(Path(args.src).glob('spin-*.json')):
    obj = convert(json.loads(path.read_text(encoding='utf-8')))
    if args.only_ww_jp and not has_ww_collect_with_jp(obj['data']):
        continue
    try:
        math_to_wire(obj)
    except ValueError as error:
        raise SystemExit('%s: %s (replay folder left unchanged)' % (path.name, error))
    converted.append((path, obj))
if not converted:
    raise SystemExit('No matching spin-*.json found (replay folder left unchanged)')
out.mkdir(exist_ok=True)
for old in out.glob('*.json'):
    old.unlink()
for path, obj in converted:
    (out / (obj['roundIndexV2'] + '.json')).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    print('%s -> %s.json  bet=%s featureOption=%s TotalWin=%s' % (
        path.name, obj['roundIndexV2'], obj['spinReq']['bet'], obj['spinReq']['featureOption'], obj['data']['TotalWin']))
