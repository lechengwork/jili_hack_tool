#!/usr/bin/env python3
"""Restore manifest-declared 9926e native assets for 545 using the verified original shared payload.

The game requests these random-extension clips during play; a 404 makes the frontend close the window.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / 'routex'))
from restore_native_assets import PAYLOAD_SHA256, asset_records, expand_uuid

SOURCE = ROOT / ('game_site_backup/uat-wbgame.jlfafafa3.com/fg5/assets/game/native/45/'
                 '456888e5-c417-4f6c-b4cb-80a274bd089d.9926e.whykq8935c')


def main():
    payload = SOURCE.read_bytes()
    if hashlib.sha256(payload).hexdigest() != PAYLOAD_SHA256 or not hashlib.md5(payload).hexdigest().startswith('9926e'):
        raise ValueError('Original shared payload changed; do not guess replacement bytes')
    static = HERE / 'static'
    pending, existing, unmatched = [], 0, []
    for config_path in sorted(static.rglob('config.*.json')):
        folder = config_path.parent
        config = json.loads(config_path.read_text(encoding='utf-8'))
        if 'versions' not in config or 'paths' not in config:
            continue
        raw = config['versions'].get('native', [])
        versions = dict(zip(raw[::2], raw[1::2]))
        targets = {v[0]: int(k) for k, v in config['paths'].items()
                   if versions.get(int(k)) == '9926e' and re.fullmatch(r'[a-z0-9]{9,13}', v[0])}
        if not targets:
            continue
        found = {}
        for path in (folder / 'import').rglob('*.json'):
            for name, extension in asset_records(json.loads(path.read_text(encoding='utf-8'))):
                if name in targets:
                    if found.get(name, extension) != extension:
                        raise ValueError('Conflicting native extension: ' + name)
                    found[name] = extension
        unmatched += [folder.relative_to(static).as_posix() + '/' + n for n in sorted(set(targets) - set(found))]
        for name, extension in found.items():
            uuid = expand_uuid(config['uuids'][targets[name]])
            target = folder / 'native' / uuid[:2] / f'{uuid}.9926e{extension}'
            if target.exists():
                if target.read_bytes() != payload:
                    raise ValueError('Existing native asset differs: ' + str(target))
                existing += 1
            else:
                pending.append(target)
    for target in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    print('restored=%d existing=%d unmatched=%d' % (len(pending), existing, len(unmatched)))
    for name in unmatched:
        print('  no extension found (not fabricated): ' + name)


if __name__ == '__main__':
    main()
