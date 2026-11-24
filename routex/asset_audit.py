#!/usr/bin/env python3
"""Read-only Cocos inventory audit. Never fetches or restores assets.

Checks every captured config's native/import versions, packed imports, literal
random-native names and existing files. Loopback HTTP checks can target the actual replay handler, or an isolated
static root; neither is a browser/Windows acceptance test.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
from http.client import HTTPConnection, HTTPSConnection, HTTPException
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
import struct
import ssl
import threading
import urllib.parse

from texture_variants import expand_uuid, webp_dimensions

SHARED_SHA = '6a7340a324579cd3735145aa5c72d0cce9902ce87332edb99ba04c46037e5c82'
ARRAY = re.compile(r'\[(?:\d{1,3},){8,12}\d{1,3}\]')
RANDOM_NAME = re.compile(r'[a-z0-9]{9,13}')


def walk_native_names(value):
    if isinstance(value, list):
        if (len(value) >= 3 and isinstance(value[0], int) and isinstance(value[1], str)
                and isinstance(value[2], str) and RANDOM_NAME.fullmatch(value[1])
                and re.fullmatch(r'\.[a-z0-9]{9,13}', value[2])):
            yield value[1], value[2]
        for item in value:
            yield from walk_native_names(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from walk_native_names(item)


def random_extensions(root):
    found = defaultdict(set)
    evidence = defaultdict(set)
    for file in sorted(root.rglob('*')):
        if file.suffix == '.js':
            text = file.read_text(encoding='utf-8', errors='replace')
            arrays = []
            for match in ARRAY.finditer(text):
                numbers = [int(n) for n in match[0][1:-1].split(',')]
                if max(numbers) > 127:
                    continue
                value = ''.join(map(chr, numbers))
                if RANDOM_NAME.fullmatch(value):
                    arrays.append((match.start(), match.end(), value))
            for a, b in zip(arrays, arrays[1:]):
                if 0 <= b[0] - a[1] < 40:
                    found[a[2]].add('.' + b[2])
                    evidence[a[2]].add(file.relative_to(root).as_posix())
        elif file.suffix == '.json' and 'import' in file.parts:
            try:
                for name, ext in walk_native_names(json.loads(file.read_text())):
                    found[name].add(ext)
                    evidence[name].add(file.relative_to(root).as_posix())
            except (ValueError, UnicodeError):
                continue
    return found, evidence


def validate_content(path, expected_version=None):
    data = path.read_bytes()
    if not data:
        raise ValueError('empty file')
    result = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if expected_version == '9926e':
        if len(data) != 746 or result['sha256'] != SHARED_SHA:
            raise ValueError('9926e content differs from the verified original 746-byte payload')
        result['content_check'] = 'exact original 9926e payload hash'
        return result
    ext = path.suffix.lower()
    if ext == '.webp':
        result['dimensions'] = list(webp_dimensions(data))
    elif ext == '.astc':
        if len(data) < 16 or data[:4] != b'\x13\xab\xa1\x5c':
            raise ValueError('invalid ASTC header')
        result['dimensions'] = [int.from_bytes(data[7:10], 'little'), int.from_bytes(data[10:13], 'little')]
        if not all(result['dimensions']):
            raise ValueError('zero ASTC dimensions')
    elif ext == '.png':
        if len(data) < 24 or data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
            raise ValueError('invalid PNG header')
        result['dimensions'] = list(struct.unpack('>II', data[16:24]))
        if not all(result['dimensions']):
            raise ValueError('zero PNG dimensions')
    elif ext in ('.jpg', '.jpeg'):
        if not data.startswith(b'\xff\xd8\xff') or not data.endswith(b'\xff\xd9'):
            raise ValueError('invalid/truncated JPEG container')
    elif ext == '.mp3':
        if len(data) < 10 or not (data.startswith(b'ID3') or data[0] == 255 and data[1] & 224 == 224):
            raise ValueError('invalid MP3 header')
    elif ext in ('.ogg', '.wav'):
        if not (data.startswith(b'OggS') if ext == '.ogg' else data[:4] == b'RIFF' and data[8:12] == b'WAVE'):
            raise ValueError('invalid audio container')
    elif ext in ('.ttf', '.otf', '.woff', '.woff2'):
        if data[:4] not in (b'\x00\x01\x00\x00', b'OTTO', b'true', b'wOFF', b'wOF2', b'ttcf'):
            raise ValueError('invalid font header')
    elif ext == '.json':
        json.loads(data)
    elif ext in ('.atlas', '.plist', '.txt', '.fnt', '.xml'):
        data.decode('utf-8')
    else:
        result['content_check'] = 'nonempty and hashed only; opaque format not decoded'
        return result
    result['content_check'] = 'format/container header; not a full media decoder'
    return result


def audit(root, check_http=False, base_url=None, ca_file=None):
    endpoint = urllib.parse.urlsplit(base_url) if base_url else None
    if endpoint and (endpoint.scheme not in ('http', 'https') or endpoint.hostname not in ('localhost', '127.0.0.1', '::1')
                     or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment or endpoint.path not in ('', '/')):
        raise ValueError('base_url must be a loopback HTTP origin')
    root = Path(root).resolve()
    extensions, extension_sources = random_extensions(root)
    inventory = defaultdict(list)
    for path in sorted(root.rglob('*')):
        if path.is_file():
            inventory[path.parent].append(path)
    rows, config_rows, errors, unresolved = [], [], [], []
    for config_path in sorted(root.rglob('config*.json')):
        try:
            config = json.loads(config_path.read_text())
        except (ValueError, UnicodeError) as error:
            errors.append({'path': config_path.relative_to(root).as_posix(), 'error': str(error)})
            continue
        if not isinstance(config, dict) or 'uuids' not in config or 'versions' not in config:
            continue
        folder = config_path.parent
        cfg_rel = config_path.relative_to(root).as_posix()
        uuids = config['uuids']
        versions = {kind: {int(i): v for i, v in zip(values[::2], values[1::2])}
                    for kind, values in config['versions'].items()}
        selected = 'unknown'
        manifest_path = folder.parent / 'versions.json'
        if manifest_path.exists():
            try:
                revision = json.loads(manifest_path.read_text()).get(config.get('name', folder.name))
                if revision:
                    selected = 'selected' if config_path.name == 'config.' + revision + '.json' else 'historical'
            except (ValueError, UnicodeError):
                pass
        start = len(rows)
        for index, version in versions.get('native', {}).items():
            uuid = expand_uuid(uuids[index])
            info = config.get('paths', {}).get(str(index), [])
            name = info[0] if info else None
            typ = config.get('types', [])[info[1]] if len(info) > 1 else 'unresolved'
            directory = folder / config.get('nativeBase', 'native') / uuid[:2]
            prefix = uuid + '.' + version
            matches = [p for p in inventory[directory] if p.name.startswith(prefix + '.')]
            # Cocos native names without a leading dot (notably fonts) are
            # stored under <uuid>.<version>/<original filename>.
            matches += inventory[directory / prefix]
            row = {'config': cfg_rel, 'bundle': folder.relative_to(root).as_posix(), 'selection': selected,
                   'kind': 'native', 'uuid': uuid, 'version': version, 'type': typ, 'name': name,
                   'expected_prefix': (directory / prefix).relative_to(root).as_posix(),
                   'files': [], 'status': 'present' if matches else 'missing'}
            exts = extensions.get(name, set()) if name else set()
            if version == '9926e' and len(exts) == 1:
                row['expected_path'] = row['expected_prefix'] + next(iter(exts))
                row['extension_evidence'] = sorted(extension_sources[name])
                exact = root / row['expected_path']
                matches = [exact] if exact.is_file() else []
                row['status'] = 'present' if matches else 'missing'
            elif not matches:
                unresolved.append({'config': cfg_rel, 'uuid': uuid, 'reason': 'native extension unresolved',
                                   'candidate_extensions': sorted(exts)})
            for path in matches:
                file = {'path': path.relative_to(root).as_posix()}
                try:
                    file.update(validate_content(path, version))
                    file['status'] = 'valid'
                except (ValueError, OSError, UnicodeError, struct.error) as error:
                    file.update(status='invalid', error=str(error)); row['status'] = 'invalid'
                row['files'].append(file)
            rows.append(row)
        # A packed member has no standalone import file; verify its container instead.
        packed_members = set()
        pack_indexes = {}
        for pack, members in config.get('packs', {}).items():
            packed_members.update(int(i) for i in members)
            if pack in uuids:
                pack_indexes[uuids.index(pack)] = pack
            candidates = {pack, expand_uuid(pack)}
            index = uuids.index(pack) if pack in uuids else None
            version = versions.get('import', {}).get(index)
            paths = []
            for key in candidates:
                prefix = key + ('.' + version if version else '.')
                directory = folder / config.get('importBase', 'import') / key[:2]
                paths.extend(p for p in inventory[directory] if p.name.startswith(prefix) and p.suffix in ('.json', '.bin', '.cconb'))
            paths = sorted(set(paths))
            row = {'config': cfg_rel, 'bundle': folder.relative_to(root).as_posix(), 'selection': selected,
                   'kind': 'import_pack', 'pack': pack, 'version': version,
                   'status': 'present' if paths else 'missing', 'files': []}
            for path in paths:
                f = {'path': path.relative_to(root).as_posix()}
                try:
                    f.update(validate_content(path)); f['status'] = 'valid'
                except (ValueError, OSError, UnicodeError) as error:
                    f.update(status='invalid', error=str(error)); row['status'] = 'invalid'
                if path.suffix != '.json':
                    unresolved.append({'config': cfg_rel, 'path': f['path'], 'reason': 'binary import pack not decoded'})
                row['files'].append(f)
            if version is None:
                unresolved.append({'config': cfg_rel, 'pack': pack, 'reason': 'pack revision not resolved from import versions'})
            rows.append(row)
        for index, version in versions.get('import', {}).items():
            if index in packed_members or index in pack_indexes:
                continue
            uuid = expand_uuid(uuids[index]); directory = folder / config.get('importBase', 'import') / uuid[:2]
            prefix = uuid + '.' + version
            paths = [p for p in inventory[directory] if p.name.startswith(prefix + '.') and p.suffix in ('.json', '.bin', '.cconb')]
            row = {'config': cfg_rel, 'bundle': folder.relative_to(root).as_posix(), 'selection': selected,
                   'kind': 'import', 'uuid': uuid, 'version': version,
                   'expected_prefix': (directory / prefix).relative_to(root).as_posix(),
                   'status': 'present' if paths else 'missing', 'files': []}
            for path in paths:
                f = {'path': path.relative_to(root).as_posix()}
                try:
                    f.update(validate_content(path)); f['status'] = 'valid'
                except (ValueError, OSError, UnicodeError) as error:
                    f.update(status='invalid', error=str(error)); row['status'] = 'invalid'
                if path.suffix != '.json':
                    unresolved.append({'config': cfg_rel, 'path': f['path'], 'reason': 'binary import metadata not decoded'})
                row['files'].append(f)
            rows.append(row)
        config_rows.append({'path': cfg_rel, 'selection': selected,
                            'counts': dict(Counter(r['status'] for r in rows[start:]))})
    # Hash/header-check all remaining mirrored native assets, including WebP/ASTC variants.
    referenced = {f['path'] for r in rows for f in r['files']}
    extras = []
    for directory, paths in inventory.items():
        for path in paths:
            if ('native' not in directory.relative_to(root).parts and path.suffix.lower() not in
                    ('.webp', '.astc', '.png', '.jpg', '.jpeg', '.mp3', '.ogg', '.wav', '.ttf', '.otf', '.woff', '.woff2')):
                continue
            rel = path.relative_to(root).as_posix()
            if rel in referenced:
                continue
            f = {'path': rel, 'note': 'existing mirrored native/media not matched to inspected config revision'}
            try:
                f.update(validate_content(path, '9926e' if '.9926e.' in path.name else None)); f['status'] = 'valid'
            except (ValueError, OSError, UnicodeError, struct.error) as error:
                f.update(status='invalid', error=str(error))
            extras.append(f)
    http = {'checked': False, 'scope': 'not run'}
    if check_http:
        files = {f['path']: f for r in rows for f in r['files'] if f.get('status') == 'valid'}
        files.update({f['path']: f for f in extras if f['status'] == 'valid'})
        class Handler(SimpleHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(root), **kwargs)
            def log_message(self, *args):
                pass
        server = None
        thread = None
        if not endpoint:
            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            server.daemon_threads = True
            thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
        local = threading.local()
        connections = []
        connection_lock = threading.Lock()
        def connection():
            if endpoint:
                if endpoint.scheme == 'https':
                    return HTTPSConnection(endpoint.hostname, endpoint.port or 443, timeout=10,
                                           context=ssl.create_default_context(cafile=ca_file))
                return HTTPConnection(endpoint.hostname, endpoint.port or 80, timeout=10)
            return HTTPConnection('127.0.0.1', server.server_port, timeout=10)
        def check(pair):
            rel, f = pair
            try:
                if not hasattr(local, 'connection'):
                    local.connection = connection()
                    with connection_lock:
                        connections.append(local.connection)
                local.connection.request('GET', '/' + urllib.parse.quote(rel, safe='/'))
                response = local.connection.getresponse()
                data = response.read(); mime = response.headers.get_content_type()
                expected = mimetypes.guess_type(rel)[0] or 'application/octet-stream'
                if response.status != 200 or hashlib.sha256(data).hexdigest() != f['sha256'] or mime != expected:
                    raise ValueError('HTTP status, MIME or full bytes mismatch: status=%s MIME=%s expected=%s' % (response.status, mime, expected))
                return {'path': rel, 'status': 'valid', 'mime': mime}
            except (OSError, ValueError, HTTPException) as error:
                return {'path': rel, 'status': 'invalid', 'error': str(error)}
        try:
            with ThreadPoolExecutor(max_workers=4) as pool:
                checks = list(pool.map(check, sorted(files.items())))
        finally:
            for connection in connections:
                connection.close()
            if server:
                server.shutdown();server.server_close();thread.join()
        http = {'checked': True, 'scope': 'actual local replay handler; not browser/Windows acceptance' if endpoint else 'isolated static-root loopback server; NOT actual replay handler or browser acceptance',
                'base_url': base_url,
                'valid': sum(c['status'] == 'valid' for c in checks), 'invalid': sum(c['status'] != 'valid' for c in checks), 'files': checks}
    counts = Counter(r['status'] for r in rows)
    random_rows = [r for r in rows if r.get('kind') == 'native' and r.get('version') == '9926e']
    return {'game_id': root.parent.name, 'scope': 'all captured config manifests, including optional/historical bundles; inventory gaps are not proof of a runtime request',
            'complete_acceptance_passed': False,
            'inventory_no_known_missing_or_invalid': not counts['missing'] and not counts['invalid'] and not errors and all(f['status'] == 'valid' for f in extras),
            'other_mirrored_media_counts': dict(Counter(f['status'] for f in extras)),
            'counts': dict(counts), 'random_native_9926e': dict(Counter(r['status'] for r in random_rows)),
            'configs': config_rows, 'declarations': rows, 'other_mirrored_media': extras, 'http': http,
            'uncovered': unresolved, 'errors': errors,
            'limitations': ['Binary import packs are not decoded.', 'Computed/dynamic URLs other than resolved random-native literal mappings are not evaluated.',
                           'Opaque binary assets are only checked for nonempty content and hashed; media headers are not full decoding.',
                           'Not a full dependency/reachability graph; some optional/historical declarations may not be used by this replay.',
                           'Protocol, browser long-run/random effects and Windows visual acceptance are separate and not run by this tool.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game_ids', nargs='+')
    parser.add_argument('--http', action='store_true', help='Check existing assets through an isolated loopback static server')
    parser.add_argument('--base-url', help='Actual loopback replay origin; requires one game ID and --http')
    parser.add_argument('--ca-file', help='Trust only the specified local HTTPS test certificate')
    args = parser.parse_args()
    if args.base_url and (len(args.game_ids) != 1 or not args.http):
        parser.error('--base-url requires one game ID and --http')
    root = Path(__file__).resolve().parents[1]
    failed = False
    for gid in args.game_ids:
        if not gid.isdigit():
            parser.error('game IDs must be numeric')
        report = audit(root / 'games' / gid / 'static', args.http, args.base_url, args.ca_file)
        (root / 'games' / gid / 'asset_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'game_id': gid, 'counts': report['counts'], 'random_native_9926e': report['random_native_9926e'],
                          'uncovered': len(report['uncovered']), 'http_valid': report['http'].get('valid'), 'http_invalid': report['http'].get('invalid')}, ensure_ascii=False), flush=True)
        failed |= not report['inventory_no_known_missing_or_invalid'] or bool(report['uncovered']) or bool(report['http'].get('invalid'))
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
