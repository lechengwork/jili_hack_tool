#!/usr/bin/env python3
"""Restore missing 9926e native assets using the identical captured payload."""
import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_SHA256 = '6a7340a324579cd3735145aa5c72d0cce9902ce87332edb99ba04c46037e5c82'
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
BUNDLES = (
    ('fg5/assets/game', 'config.af198.json'),
    ('astarte2/3.6/web-mobile/assets/extra', 'config.b2aed.json'),
)


def expand_uuid(value):
    if len(value) == 36:
        return value
    if len(value) != 22:
        raise ValueError('Unsupported Cocos UUID')
    digits = value[:2] + ''.join(
        f'{(ALPHABET.index(value[i]) << 6) | ALPHABET.index(value[i + 1]):03x}'
        for i in range(2, 22, 2)
    )
    return '-'.join((digits[:8], digits[8:12], digits[12:16], digits[16:20], digits[20:]))


def asset_records(value):
    if isinstance(value, list):
        if (len(value) >= 3 and isinstance(value[0], int)
                and isinstance(value[1], str) and isinstance(value[2], str)
                and re.fullmatch(r'\.[a-z0-9]{9,13}', value[2])):
            yield value[1], value[2]
        for item in value:
            yield from asset_records(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from asset_records(item)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--static-root', type=Path,
                        default=ROOT / 'game_site_backup/uat-wbgame.jlfafafa3.com')
    args = parser.parse_args()
    source = (args.static_root / 'fg5/assets/game/native/45/'
              '456888e5-c417-4f6c-b4cb-80a274bd089d.9926e.whykq8935c')
    payload = source.read_bytes()
    if hashlib.sha256(payload).hexdigest() != PAYLOAD_SHA256:
        raise ValueError('Captured source payload differs; refusing to restore assets')
    if not hashlib.md5(payload).hexdigest().startswith('9926e'):
        raise ValueError('Payload does not match the native version')

    pending = []
    counts = {}
    for relative, config_name in BUNDLES:
        folder = args.static_root / relative
        config = json.loads((folder / config_name).read_text())
        targets = {value[0]: int(key) for key, value in config['paths'].items()
                   if config['types'][value[1]] == 'cc.Asset'
                   and re.fullmatch(r'[a-z0-9]{9,13}', value[0])}
        records = {}
        for path in (folder / 'import').rglob('*.json'):
            for name, extension in asset_records(json.loads(path.read_text())):
                if name in targets:
                    if name in records and records[name] != extension:
                        raise ValueError(f'Conflicting native extension: {name}')
                    records[name] = extension
        if set(records) != set(targets):
            raise ValueError(f'Incomplete native metadata: {relative}')
        raw_versions = config['versions']['native']
        versions = {int(raw_versions[i]): raw_versions[i + 1]
                    for i in range(0, len(raw_versions), 2)}
        counts[relative] = {'restored': 0, 'existing': 0}
        for name, extension in records.items():
            index = targets[name]
            if versions.get(index) != '9926e':
                raise ValueError(f'Unexpected native version: {relative}/{name}')
            uuid = expand_uuid(config['uuids'][index])
            destination = folder / 'native' / uuid[:2] / f'{uuid}.9926e{extension}'
            if destination.exists():
                if destination.read_bytes() != payload:
                    raise ValueError(f'Existing asset differs: {destination}')
                counts[relative]['existing'] += 1
            else:
                pending.append((relative, destination))

    # Finish inspecting every manifest and existing file before writing any asset.
    for relative, destination in pending:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        counts[relative]['restored'] += 1
    for relative, count in counts.items():
        print(f'{relative}: restored={count["restored"]}, existing={count["existing"]}')
    print(f'Restored {len(pending)} missing native assets from the captured 746-byte payload.')


if __name__ == '__main__':
    main()
