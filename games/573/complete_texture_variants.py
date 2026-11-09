"""Download original versioned Cocos image variants; never transcode or rename."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
STATIC = HERE / 'static'
ORIGIN = 'https://uat-wbgame.jlfafafa3.com/'
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.webp', '.pvr', '.pkm', '.astc']

def expand(value):
    if len(value) == 22:
        digits = value[:2] + ''.join('%03x' % ((ALPHABET.index(value[i]) << 6) |
                                    ALPHABET.index(value[i + 1])) for i in range(2, 22, 2))
        return '-'.join((digits[:8], digits[8:12], digits[12:16], digits[16:20], digits[20:]))
    if not re.fullmatch(r'[a-zA-Z0-9@._-]+', value):
        raise ValueError('Unsupported Cocos UUID: ' + value)
    return value

def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        f.write(data)
        temp = Path(f.name)
    try:
        # Existing original assets are immutable. Never overwrite a different file.
        if path.exists():
            if path.read_bytes() != data:
                raise ValueError('Existing asset content differs: ' + str(path))
        else:
            os.link(temp, path)
    finally:
        temp.unlink(missing_ok=True)

def fetch(relative):
    path = STATIC / relative
    if path.exists():
        return path.read_bytes(), False
    request = urllib.request.Request(ORIGIN + relative, headers={'User-Agent': 'Mozilla/5.0'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read(), True
        except urllib.error.HTTPError as error:
            if error.code != 429 and error.code < 500:
                raise
            if attempt == 2:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(2 ** (attempt + 1))

def image_format(value):
    if isinstance(value, dict):
        if isinstance(value.get('fmt'), str):
            yield value['fmt']
        for key, child in value.items():
            if key != 'fmt':
                yield from image_format(child)
    elif isinstance(value, list):
        for child in value:
            yield from image_format(child)
    elif isinstance(value, str) and re.fullmatch(r'[0-7](?:@\d+)?(?:_[0-7](?:@\d+)?)+', value):
        yield value

def validate_image(data, extension):
    valid = {'.webp': data[:4] == b'RIFF' and data[8:12] == b'WEBP',
             '.png': data.startswith(b'\x89PNG\r\n\x1a\n'),
             '.jpg': data.startswith(b'\xff\xd8\xff'),
             '.jpeg': data.startswith(b'\xff\xd8\xff'),
             '.astc': data.startswith(b'\x13\xab\xa1\x5c'),
             '.bmp': data.startswith(b'BM'),
             '.pvr': data.startswith((b'PVR\x03', b'\x03RVP')),
             '.pkm': data.startswith(b'PKM ')}
    if not valid.get(extension, False):
        raise ValueError('Invalid original image signature for ' + extension)

def plan_metadata():
    plans = {}
    for config_path in sorted(STATIC.rglob('config*.json')):
        config = json.loads(config_path.read_text())
        if 'uuids' not in config:
            continue
        uuids = config['uuids']
        versions = {kind: dict(zip(values[::2], values[1::2]))
                    for kind, values in config.get('versions', {}).items()}
        packed = {i: pack for pack, indices in config.get('packs', {}).items() for i in indices}
        for index, version in versions.get('native', {}).items():
            info = config.get('paths', {}).get(str(index))
            if info and config['types'][info[1]] != 'cc.ImageAsset':
                continue
            pack = packed.get(index)
            import_index = uuids.index(pack) if pack else index
            import_uuid = expand(uuids[import_index])
            import_version = versions.get('import', {}).get(import_index)
            if not import_version:
                raise ValueError('Missing metadata version: %s index=%s' % (config_path, index))
            relative = (config_path.parent / 'import' / import_uuid[:2] /
                        (import_uuid + '.' + import_version + '.json')).relative_to(STATIC).as_posix()
            plan = plans.setdefault(relative, {'packed': bool(pack), 'items': []})
            plan['items'].append({'index': index, 'uuid': expand(uuids[index]),
                                  'native_version': version,
                                  'bundle': config_path.parent.relative_to(STATIC).as_posix(),
                                  'config': config_path.relative_to(STATIC).as_posix(),
                                  'position': config['packs'][pack].index(index) if pack else None,
                                  'declared_image': bool(info)})
    return plans

def execute(download=False, workers=8, bundle=None):
    # Include declared game bundles even when the initial Mac session did not load them.
    for settings in sorted((STATIC / 'rc2/src').glob('settings*.json')):
        for name, version in json.loads(settings.read_text()).get('assets', {}).get('bundleVers', {}).items():
            if not re.fullmatch(r'[A-Za-z0-9_-]+', name + version):
                raise ValueError('Invalid original bundle/version')
            path = settings.parent.parent / 'assets' / name / ('config.' + version + '.json')
            relative = path.relative_to(STATIC).as_posix()
            if not path.exists():
                if not download:
                    raise ValueError('Missing declared bundle config: ' + relative)
                data, _ = fetch(relative)
                json.loads(data)
                atomic(path, data)
    plans = plan_metadata()
    if bundle:
        plans = {key: value for key, value in plans.items()
                 if any(item['bundle'] == bundle for item in value['items'])}
        if not plans:
            raise ValueError('Unknown texture bundle: ' + bundle)
    errors, images, skipped = [], {}, []
    def metadata_task(entry):
        relative, plan = entry
        path = STATIC / relative
        if not path.exists() and not download:
            raise ValueError('Metadata not cached: ' + relative)
        data, fresh = fetch(relative)
        parsed = json.loads(data)
        if fresh:
            atomic(path, data)
        output, other = [], []
        for item in plan['items']:
            payload = parsed[5][item['position']] if plan['packed'] else parsed
            formats = sorted(set(image_format(payload)))
            if not formats:
                if item['declared_image']:
                    raise ValueError('Declared image has no format metadata: ' + relative)
                other.append({'uuid': item['uuid'], 'bundle': item['bundle']})
                continue
            if len(formats) != 1:
                raise ValueError('Ambiguous image metadata: ' + relative)
            extensions = {EXTENSIONS[int(token.split('@')[0])] for token in formats[0].split('_')}
            for ext in sorted(extensions):
                name = item['uuid'] + '.' + item['native_version'] + ext
                native = item['bundle'] + '/native/' + item['uuid'][:2] + '/' + name
                output.append((native, {**item, 'format': formats[0], 'extension': ext,
                                        'metadata': relative}))
        return output, other
    print('Versioned metadata files:', len(plans), flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        tasks = {pool.submit(metadata_task, entry): entry[0] for entry in plans.items()}
        for n, future in enumerate(as_completed(tasks), 1):
            try:
                output, other = future.result()
                images.update(output)
                skipped.extend(other)
            except Exception as error:
                errors.append({'phase': 'metadata', 'path': tasks[future], 'error': str(error)})
                print('Metadata ERROR ' + tasks[future] + ': ' + str(error), flush=True)
            if n % 50 == 0 or n == len(tasks):
                print('Metadata %d/%d; images planned=%d; errors=%d' %
                      (n, len(tasks), len(images), len(errors)), flush=True)
    report = {'game_id': 573, 'origin': ORIGIN, 'metadata_files': len(plans),
              'metadata_non_image_entries': len(skipped), 'variants': [], 'errors': errors}
    def texture_task(entry):
        relative, evidence = entry
        if not download and not (STATIC / relative).exists():
            raise ValueError('Missing original variant')
        data, fresh = fetch(relative)
        validate_image(data, evidence['extension'])
        if fresh:
            atomic(STATIC / relative, data)
        return {'path': relative, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                'config': evidence['config'], 'metadata': evidence['metadata'],
                'format': evidence['format'], 'extension': evidence['extension']}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        tasks = {pool.submit(texture_task, entry): entry[0] for entry in sorted(images.items())}
        for n, future in enumerate(as_completed(tasks), 1):
            try:
                report['variants'].append(future.result())
            except Exception as error:
                report['errors'].append({'phase': 'texture', 'path': tasks[future], 'error': str(error)})
                print('Texture ERROR ' + tasks[future] + ': ' + str(error), flush=True)
            if n % 100 == 0 or n == len(tasks):
                print('Textures %d/%d; verified=%d; errors=%d' %
                      (n, len(tasks), len(report['variants']), len(report['errors'])), flush=True)
    report['variants'].sort(key=lambda x: x['path'])
    report['expected_variants'] = len(images)
    report['complete'] = not report['errors']
    report['counts'] = {ext: sum(r['extension'] == ext for r in report['variants']) for ext in EXTENSIONS}
    report_name = 'texture_variants-' + Path(bundle).name + '.json' if bundle else 'texture_variants.json'
    (HERE / report_name).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['expected_variants', 'counts', 'complete']}) +
          ' errors=' + str(len(report['errors'])), flush=True)
    if report['errors']:
        raise SystemExit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', help='Fetch missing original CDN files')
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--bundle', help='Limit a download pass to one declared bundle')
    args = parser.parse_args()
    execute(args.download, args.workers, args.bundle)
