#!/usr/bin/env python3
"""Audit Cocos ASTC/WebP variants; fetch exact public originals only on explicit --fetch.

Uses native UUID/version and packed ImageAsset metadata, including unopened UI bundles.
It never substitutes ASTC bytes, invents successful HTTP responses, or contacts game APIs.
"""
import argparse
import hashlib
import json
import os
import struct
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'


def expand_uuid(value):
    if len(value) != 22:
        return value
    digits = value[:2] + ''.join('%03x' % ((ALPHABET.index(value[i]) << 6) | ALPHABET.index(value[i+1])) for i in range(2, 22, 2))
    return '-'.join((digits[:8], digits[8:12], digits[12:16], digits[16:20], digits[20:]))


def image_records(value):
    if isinstance(value, dict):
        if 'fmt' in value and 'w' in value and 'h' in value:
            yield value
        for item in value.values():
            yield from image_records(item)
    elif isinstance(value, list):
        for item in value:
            yield from image_records(item)


def declared_webps(root):
    targets = {}
    missing_packs = []
    binary_packs = []
    for config_path in sorted(root.rglob('config.*.json')):
        config = json.loads(config_path.read_text())
        versions = config.get('versions', {}).get('native', [])
        versions = {int(index): version for index, version in zip(versions[::2], versions[1::2])}
        imports = config.get('versions', {}).get('import', [])
        imports = {int(index): version for index, version in zip(imports[::2], imports[1::2])}
        manifest_path = config_path.parent.parent / 'versions.json'
        selected = None
        active_version = None
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            active_version = manifest.get(config.get('name', config_path.parent.name))
            if active_version:
                selected = config_path.name == 'config.' + active_version + '.json'
        for pack, ids in config.get('packs', {}).items():
            pack_index = config.get('uuids', []).index(pack) if pack in config.get('uuids', []) else None
            pack_version = imports.get(pack_index)
            pattern = pack + '.' + pack_version + '.json' if pack_version else pack + '.*.json'
            files = list((config_path.parent / 'import' / pack[:2]).glob(pattern))
            if len(files) > 1:
                raise ValueError('Ambiguous import pack revision: ' + str(config_path) + ': ' + pack)
            if not files:
                binary = list((config_path.parent / 'import' / pack[:2]).glob(pack + '.*.bin'))
                if binary:
                    data = binary[0].read_bytes()
                    binary_packs.append({'path': str(binary[0].relative_to(root)),
                                         'image_asset_type_present': b'cc.ImageAsset' in data,
                                         'note': 'binary pack; not decoded by this texture audit'})
                else:
                    missing_packs.append(str((config_path.parent / 'import' / pack).relative_to(root)))
                continue
            data = json.loads(files[0].read_text())
            # Cocos exports both compact mixed packs and homogeneous typed packs.
            records = data['data'] if isinstance(data, dict) and 'type' in data else data[5]
            if len(records) != len(ids):
                raise ValueError('Pack UUID/record count mismatch: ' + str(files[0]))
            for uid_index, record in zip(ids, records):
                uid_index = int(uid_index)
                for image in image_records(record):
                    formats = [part.split('@')[0] for part in str(image['fmt']).split('_')]
                    if '7' not in formats or '4' not in formats:
                        continue
                    version = versions.get(uid_index)
                    if version is None:
                        raise ValueError('ImageAsset missing native version: ' + str(files[0]))
                    uid = expand_uuid(config['uuids'][uid_index])
                    target = config_path.parent / config.get('nativeBase', 'native') / uid[:2] / (uid + '.' + version + '.webp')
                    expected = {'width': image['w'], 'height': image['h'], 'metadata': str(files[0].relative_to(root)),
                                'config': str(config_path.relative_to(root)), 'manifest_selected': selected,
                                'active_bundle_version': active_version}
                    if target not in targets or targets[target].get('manifest_selected') is not True:
                        targets[target] = expected
    # Also cover captured ASTC with metadata in standalone or unavailable packs.
    for astc in root.rglob('*.astc'):
        targets.setdefault(astc.with_suffix('.webp'), {'width': None, 'height': None, 'metadata': 'captured ASTC counterpart'})
    for webp in root.rglob('*.webp'):
        targets.setdefault(webp, {'width': None, 'height': None, 'metadata': 'existing WebP; metadata not resolved'})
    return targets, missing_packs, binary_packs


def webp_dimensions(data):
    if len(data) < 30 or data[:4] != b'RIFF' or data[8:12] != b'WEBP' or struct.unpack('<I', data[4:8])[0] + 8 != len(data):
        raise ValueError('Invalid WebP container (possibly HTML or ASTC)')
    kind = data[12:16]
    if kind == b'VP8X':
        return 1 + int.from_bytes(data[24:27], 'little'), 1 + int.from_bytes(data[27:30], 'little')
    if kind == b'VP8 ' and data[23:26] == b'\x9d\x01\x2a':
        return int.from_bytes(data[26:28], 'little') & 16383, int.from_bytes(data[28:30], 'little') & 16383
    if kind == b'VP8L' and data[20] == 47:
        bits = int.from_bytes(data[21:25], 'little')
        return (bits & 16383) + 1, ((bits >> 14) & 16383) + 1
    raise ValueError('Unsupported WebP image header')


def audit(root, fetch=False, host='uat-wbgame.jlfafafa3.com', base_url=None):
    root = Path(root).resolve()
    if base_url:
        endpoint = urllib.parse.urlsplit(base_url)
        if (endpoint.scheme not in ('http', 'https') or endpoint.hostname not in ('localhost', '127.0.0.1', '::1')
                or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment or endpoint.path not in ('', '/')):
            raise ValueError('--base-url must be a loopback HTTP origin')
    targets, missing_packs, binary_packs = declared_webps(root)
    def check(pair):
        path, expected = pair
        relative = path.relative_to(root).as_posix()
        row = dict(path=relative, **expected)
        try:
            if not path.exists() and fetch:
                url = 'https://' + host + '/' + relative
                with urllib.request.urlopen(url, timeout=35) as response:
                    if response.status != 200:
                        raise ValueError('HTTP ' + str(response.status))
                    data = response.read()
                dimensions = webp_dimensions(data)
                if expected['width'] and dimensions != (expected['width'], expected['height']):
                    raise ValueError('Original WebP dimensions differ from metadata')
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_suffix('.webp.tmp')
                tmp.write_bytes(data)
                os.replace(tmp, path)
            data = path.read_bytes()
            dimensions = webp_dimensions(data)
            if expected['width'] and dimensions != (expected['width'], expected['height']):
                raise ValueError('WebP dimensions differ from ImageAsset metadata')
            astc = path.with_suffix('.astc')
            if astc.exists():
                header = astc.read_bytes()[:16]
                if header[:4] != b'\x13\xab\xa1\x5c':
                    raise ValueError('Invalid ASTC header')
                if dimensions != (int.from_bytes(header[7:10], 'little'), int.from_bytes(header[10:13], 'little')):
                    raise ValueError('WebP dimensions differ from captured ASTC')
            row.update(status='ok', size=len(data), sha256=hashlib.sha256(data).hexdigest(), dimensions=dimensions,
                       original_url='https://' + host + '/' + relative)
            if base_url:
                url = base_url.rstrip('/') + '/' + urllib.parse.quote(relative, safe='/')
                with urllib.request.urlopen(url, timeout=10) as response:
                    body = response.read()
                    mime = response.headers.get_content_type()
                    if response.status != 200 or mime != 'image/webp' or body != data:
                        raise ValueError('Local HTTP status, MIME or bytes differ from validated WebP')
                row['http_verified'] = True
        except Exception as exc:
            row.update(status='error', error=str(exc))
        return row
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(check, sorted(targets.items())))
    errors = [row for row in rows if row['status'] != 'ok']
    active = [row for row in rows if row.get('manifest_selected') is not False]
    historical_errors = [row for row in errors if row.get('manifest_selected') is False]
    return {'passed': not errors and bool(rows), 'required_webp': len(rows), 'valid_webp': len(rows)-len(errors),
            'active_passed': bool(active) and all(row['status'] == 'ok' for row in active),
            'active_required_webp': len(active), 'active_valid_webp': sum(row['status'] == 'ok' for row in active),
            'historical_asset_errors': historical_errors,
            'local_http_origin': base_url, 'http_verified': sum(row.get('http_verified', False) for row in rows),
            'scope': 'ASTC/WebP variants in available Cocos packs and captured ASTC; not a complete Windows visual test',
            'unavailable_import_packs': missing_packs, 'binary_import_packs': binary_packs, 'assets': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('static_root', type=Path)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--base-url', help='Also verify exact WebP bytes and MIME through a local replay HTTP origin')
    args = parser.parse_args()
    report = audit(args.static_root, args.fetch, base_url=args.base_url)
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('WebP variants: %d/%d valid' % (report['valid_webp'], report['required_webp']))
    errors = [row for row in report['assets'] if row['status'] != 'ok']
    for row in errors[:10]:
        print(row['path'] + ': ' + row['error'])
    if len(errors) > 10:
        print('Further errors: %d (use --report for the full list)' % (len(errors) - 10))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
