#!/usr/bin/env python3
"""Restore only metadata-addressed gaps from verified local originals or exact CDN URLs.

Never changes existing files. Unknown extensions, content conflicts and unavailable
original versions are recorded per game instead of guessed or replaced by placeholders.
"""
import argparse
import os
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
from functools import lru_cache
import json
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

from asset_audit import SHARED_SHA, validate_content
from texture_variants import expand_uuid, image_records

ROOT = Path(__file__).resolve().parents[1]
BATCH = ['545', '573', '200', '224', '461', '664']
ORIGIN = 'https://uat-wbgame.jlfafafa3.com/'
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.webp', '.pvr', '.pkm', '.astc']
SUPPORTED_IMAGES = {'.png', '.jpg', '.jpeg', '.webp', '.astc'}
SOURCE_746 = 'game_site_backup/uat-wbgame.jlfafafa3.com/fg5/assets/game/native/45/456888e5-c417-4f6c-b4cb-80a274bd089d.9926e.whykq8935c'


def sha(data):
    return hashlib.sha256(data).hexdigest()


SOURCE_EVIDENCE = {}


def git_sources():
    changed = set(subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT, text=True).splitlines())
    result = defaultdict(list)
    SOURCE_EVIDENCE.clear()
    def add(path, evidence):
        f = ROOT / path
        if not f.is_file() or not ({'native', 'import'} & set(f.parts)):
            return
        SOURCE_EVIDENCE[path] = evidence
        parent_parts = f.parent.name.split('.')
        if 'native' in f.parts and len(parent_parts) == 2 and re.fullmatch(r'[0-9a-f]{5}', parent_parts[1]):
            result[('native', parent_parts[0], parent_parts[1])].append(path)
        parts = f.name.split('.')
        if len(parts) >= 3 and re.fullmatch(r'[0-9a-f]{5}', parts[1]):
            result[('native' if 'native' in f.parts else 'import', parts[0], parts[1])].append(path)
    for path in subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0'):
        if not path or path in changed or not (path.startswith('games/') and '/static/' in path or path.startswith('game_site_backup/')):
            continue
        add(path, {'kind': 'unchanged tracked original'})
    # A successful restoration remains a usable original for another bundle,
    # but only while its bytes still match the recorded verified SHA256.
    for gid in BATCH:
        journal = ROOT / 'games' / gid / 'asset_repairs.json'
        if not journal.exists():
            continue
        static = journal.parent / 'static'
        for outcome in json.loads(journal.read_text()).get('outcomes', []):
            if outcome.get('status') != 'restored':
                continue
            file = static / outcome['target']
            if static.resolve() not in file.resolve().parents or not file.is_file():
                continue
            if sha(file.read_bytes()) != outcome.get('sha256'):
                continue
            add(file.relative_to(ROOT).as_posix(), {'kind': 'verified restoration',
                'journal': journal.relative_to(ROOT).as_posix(), 'sha256': outcome['sha256'],
                'original_url': outcome.get('original_url'), 'original_local_source': outcome.get('source')})
    return result


@lru_cache(maxsize=8)
def image_format_evidence(root):
    evidence = []
    for path in root.rglob('*.js'):
        if not any('cocos' in part for part in path.parts):
            continue
        data = path.read_bytes()
        match = re.search(r'\.extnames=(\["\.png","\.jpg"[^\]]+\])', data.decode('utf-8', 'replace'))
        if match:
            values = json.loads(match[1])
            if values != IMAGE_EXTENSIONS:
                raise ValueError('Unrecognized original image-format table: ' + str(path))
            evidence.append({'path': path.relative_to(root).as_posix(), 'sha256': sha(data), 'extensions': values})
    return evidence


def literal_native_names(value):
    if isinstance(value, list):
        if len(value) >= 3 and isinstance(value[0], int) and isinstance(value[1], str) and isinstance(value[2], str):
            name = value[2]
            if re.fullmatch(r'\.[A-Za-z0-9]{1,13}', name) or (Path(name).name == name and re.fullmatch(r'[A-Za-z0-9_ .-]+\.(ttf|otf|woff2?|bin|json|atlas|mp3|ogg|wav|skel)', name)):
                yield name
        for item in value:
            yield from literal_native_names(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from literal_native_names(item)


def native_metadata(folder, config, root):
    result = defaultdict(list)
    format_evidence = image_format_evidence(root)
    if not format_evidence:
        return result
    imports = dict(zip(config.get('versions', {}).get('import', [])[::2], config.get('versions', {}).get('import', [])[1::2]))
    for pack, ids in config.get('packs', {}).items():
        i = config['uuids'].index(pack) if pack in config['uuids'] else None
        version = imports.get(i)
        # Do not select the first historical revision when the original import
        # version is unavailable or ambiguous.
        files = list((folder / config.get('importBase', 'import') / pack[:2]).glob(pack + ('.' + version if version else '.*') + '.json'))
        if len(files) != 1:
            continue
        try:
            data = json.loads(files[0].read_text())
            records = data['data'] if isinstance(data, dict) and 'type' in data else data[5]
            if len(records) != len(ids):
                continue
            for index, record in zip(ids, records):
                uuid = expand_uuid(config['uuids'][int(index)])
                for name in sorted(set(literal_native_names(record))):
                    result[uuid].append({'native_name': name, 'metadata': files[0].relative_to(root).as_posix()})
                for image in image_records(record):
                    for fmt in str(image['fmt']).split('_'):
                        number = fmt.split('@')[0]
                        if number.isdigit() and int(number) < len(IMAGE_EXTENSIONS):
                            ext = IMAGE_EXTENSIONS[int(number)]
                            if ext in SUPPORTED_IMAGES:
                                result[uuid].append({'extension': ext, 'metadata': files[0].relative_to(root).as_posix(),
                                                     'width': image['w'], 'height': image['h'],
                                                     'format_evidence': format_evidence})
        except (ValueError, KeyError, IndexError, TypeError):
            continue
    return result


def repair(gids, fetch=False, skip_known_unavailable=False):
    index = git_sources()
    payload = (ROOT / SOURCE_746).read_bytes()
    if len(payload) != 746 or sha(payload) != SHARED_SHA or not hashlib.md5(payload).hexdigest().startswith('9926e'):
        raise ValueError('Verified original 746-byte payload changed')
    source_dirty = set(subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT, text=True).splitlines())
    if SOURCE_746 in source_dirty:
        raise ValueError('Original common payload is modified; refusing source')
    plans = defaultdict(list)
    unresolved = defaultdict(list)
    configs, meta = {}, {}
    for gid in gids:
        root = ROOT / 'games' / gid / 'static'
        report = json.loads((root.parent / 'asset_validation.json').read_text())
        for row in report['declarations']:
            if row['status'] != 'missing':
                continue
            cfg_rel = row['config']; key = (gid, cfg_rel)
            if key not in configs:
                configs[key] = json.loads((root / cfg_rel).read_text())
                meta[key] = native_metadata((root / cfg_rel).parent, configs[key], root)
            config = configs[key]
            basic = {'kind': row['kind'], 'config': cfg_rel, 'uuid': row.get('uuid'), 'version': row.get('version')}
            if row.get('version') == '9926e' and row.get('expected_path'):
                plans[gid].append(dict(basic, target=row['expected_path'], source=SOURCE_746,
                                       method='original 746-byte SHA256 plus target manifest and literal extension',
                                       extension_evidence=row['extension_evidence'], expected_sha256=SHARED_SHA))
                continue
            uid = row.get('uuid') or row.get('pack')
            if not uid or not row.get('version'):
                unresolved[gid].append(dict(basic, reason='original UUID or revision unresolved'))
                continue
            kind = 'native' if row['kind'] == 'native' else 'import'
            sources = index.get((kind, uid, row['version']), [])
            grouped = defaultdict(list)
            for source in sources:
                parent_key = Path(source).parent.name
                suffix = '/' + Path(source).name if parent_key == uid + '.' + row['version'] else Path(source).suffix
                grouped[suffix].append(source)
            copied = False
            for ext, source_paths in sorted(grouped.items()):
                # Same UUID/revision/extension must have a single captured byte value.
                digests = {sha((ROOT / p).read_bytes()) for p in source_paths}
                if len(digests) != 1:
                    unresolved[gid].append(dict(basic, extension=ext, reason='conflicting tracked originals', sources=source_paths))
                    continue
                source = sorted(source_paths)[0]
                prefix = row.get('expected_prefix')
                if prefix is None:
                    folder = root / row['bundle'] / config.get('importBase', 'import') / uid[:2]
                    prefix = (folder / (uid + '.' + row['version'])).relative_to(root).as_posix()
                plans[gid].append(dict(basic, target=prefix + ext, source=source,
                                       method='verified original with identical UUID, revision and extension', source_evidence=SOURCE_EVIDENCE.get(source, {}), expected_sha256=next(iter(digests))))
                copied = True
            if copied:
                continue
            if row['kind'] == 'native':
                records = meta[key].get(uid, [])
                if records:
                    for record in records:
                        if 'native_name' in record:
                            name = record['native_name']
                            suffix = name if name.startswith('.') else '/' + name
                            method = 'exact CDN native path from UUID/revision and original native filename metadata'
                        else:
                            suffix = record['extension']
                            method = 'exact CDN image path from UUID/revision and original ImageAsset format metadata'
                        plans[gid].append(dict(basic, target=row['expected_prefix'] + suffix, method=method, **record))
                else:
                    unresolved[gid].append(dict(basic, expected_prefix=row.get('expected_prefix'), reason='no tracked same-version original or resolved native extension'))
            else:
                # Cocos import defaults to JSON unless extensionMap explicitly
                # declares a different per-UUID container. No extension probing.
                overrides = [ext for ext, ids in config.get('extensionMap', {}).items()
                             if uid in config['uuids'] and config['uuids'].index(uid) in ids]
                ext = overrides[0] if len(overrides) == 1 else '.json' if not overrides else None
                if ext not in ('.json', '.cconb'):
                    unresolved[gid].append(dict(basic, reason='ambiguous/unsupported original import extension'))
                    continue
                prefix = row.get('expected_prefix') or (Path(row['bundle']) / config.get('importBase', 'import') / uid[:2] / (uid + '.' + row['version'])).as_posix()
                plans[gid].append(dict(basic, target=prefix + ext, method='exact original Cocos import UUID/revision and extensionMap/default JSON'))
    # Deduplicate targets while preserving all metadata references.
    for gid in gids:
        unique = {}
        for plan in plans[gid]:
            unique.setdefault(plan['target'], plan)
        plans[gid] = list(unique.values())
    remote_cache = {}
    if skip_known_unavailable:
        for gid in gids:
            report_file = ROOT / 'games' / gid / 'asset_repairs.json'
            if report_file.exists():
                for old in json.loads(report_file.read_text()).get('outcomes', []):
                    if old.get('status') == 'unresolved' and 'source' not in old and old.get('error') != 'network fetch not requested':
                        remote_cache[old['target']] = (None, old.get('error', 'previous exact original unavailable'))
    remote_paths = sorted({p['target'] for entries in plans.values() for p in entries if 'source' not in p and p['target'] not in remote_cache})
    def download(relative):
        if not fetch:
            return relative, None, 'network fetch not requested'
        url = ORIGIN + urllib.parse.quote(relative, safe='/')
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status != 200:
                    raise ValueError('HTTP %s' % response.status)
                content = response.read(32 * 1024 * 1024 + 1)
                if not content or len(content) > 32 * 1024 * 1024:
                    raise ValueError('empty or over-size original')
                if response.geturl().split('?')[0] != url:
                    raise ValueError('original asset redirected to another URL')
            return relative, content, None
        except (OSError, ValueError) as error:
            return relative, None, str(error)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for relative, data, error in pool.map(download, remote_paths):
            remote_cache[relative] = (data, error)
    for gid in gids:
        root = ROOT / 'games' / gid / 'static'
        previous_file = root.parent / 'asset_repairs.json'
        previous = {o['target']: o for o in json.loads(previous_file.read_text()).get('outcomes', [])} if previous_file.exists() else {}
        outcomes = []
        for plan in plans[gid]:
            target = root / plan['target']
            if root.resolve() not in target.resolve().parents:
                raise ValueError('target outside static root')
            outcome = dict(plan)
            if target.exists():
                digest = sha(target.read_bytes())
                old = previous.get(plan['target'])
                if old and old.get('status') == 'restored' and old.get('sha256') == digest:
                    outcome = dict(old, existing_verified=True)
                else:
                    outcome.update(status='existing_preserved', sha256=digest)
                    if plan.get('expected_sha256') and digest != plan['expected_sha256']:
                        outcome.update(status='existing_conflict', error='existing content differs from verified source; preserved')
                outcomes.append(outcome); continue
            try:
                if 'source' in plan:
                    data = (ROOT / plan['source']).read_bytes()
                    if sha(data) != plan['expected_sha256']:
                        raise ValueError('local original changed after planning')
                else:
                    data, error = remote_cache[plan['target']]
                    if error:
                        raise ValueError(error)
                    outcome['original_url'] = ORIGIN + urllib.parse.quote(plan['target'], safe='/')
                    # Opaque import containers must also match their original
                    # revision digest. Image variants share the primary PNG's
                    # version, so use original format/dimensions instead there.
                    if not plan['method'].startswith('exact CDN image') and not hashlib.md5(data).hexdigest().startswith(plan['version']):
                        raise ValueError('content does not match original revision digest')
                # Validate before writing; write-once creation never overwrites.
                with tempfile.TemporaryDirectory(prefix='jili-asset-validate-') as tmp:
                    sample = Path(tmp) / target.name; sample.write_bytes(data)
                    verified = validate_content(sample, plan['version'])
                    dimensions = verified.get('dimensions')
                    if dimensions and plan.get('width') and plan.get('height'):
                        if dimensions != [plan['width'], plan['height']]:
                            raise ValueError('original image dimensions mismatch')
                target.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as f:
                    temp_path = Path(f.name); f.write(data)
                try:
                    os.link(temp_path, target)  # atomic no-replace publication
                finally:
                    temp_path.unlink(missing_ok=True)
                outcome.update(status='restored', **verified)
            except (OSError, ValueError, UnicodeError) as error:
                outcome.update(status='unresolved', error=str(error))
            outcomes.append(outcome)
        seen = {o['target'] for o in outcomes}
        for target_name, old in previous.items():
            if target_name not in seen and old.get('status') == 'restored':
                existing = root / target_name
                if existing.is_file() and sha(existing.read_bytes()) == old.get('sha256'):
                    outcomes.append(dict(old, existing_verified=True))
                else:
                    outcomes.append(dict(old, status='existing_conflict', error='previously restored file missing or changed; preserved'))
        for outcome in outcomes:
            if outcome['method'].startswith('exact CDN image'):
                outcome['format_evidence'] = image_format_evidence(root)
        destination = root.parent / 'asset_repairs.json'
        result = {'game_id': gid, 'origin': ORIGIN, 'no_existing_files_overwritten': True,
                  'restored': sum(o['status'] == 'restored' for o in outcomes),
                  'failed_or_unavailable': sum(o['status'] in ('unresolved', 'existing_conflict') for o in outcomes),
                  'unconfirmed': unresolved[gid], 'outcomes': outcomes}
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'game_id': gid, 'restored': result['restored'], 'failed_or_unavailable': result['failed_or_unavailable'], 'unconfirmed': len(unresolved[gid])}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game_ids', nargs='*', default=BATCH)
    parser.add_argument('--fetch', action='store_true', help='Fetch only exact metadata-derived original CDN paths')
    parser.add_argument('--skip-known-unavailable', action='store_true', help='Do not re-request exact original URLs already recorded as unavailable')
    args = parser.parse_args()
    if any(gid not in BATCH for gid in args.game_ids):
        parser.error('unsupported game ID')
    repair(args.game_ids, args.fetch, args.skip_known_unavailable)
