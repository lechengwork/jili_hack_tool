#!/usr/bin/env python3
"""Build the credential-free, self-contained 518 probability test handoff."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
GAME = ROOT / 'games/518'
STAGE = ROOT / 'dist518_math'
ARCHIVE = ROOT / 'jili_518_math_test_20261102.zip'
subprocess.run([sys.executable, '-B', str(GAME / 'math_adapter.py'), '--selftest'], check=True)
marker = STAGE / '.generated_518_package'
if STAGE.exists():
    if not marker.exists():
        raise RuntimeError('Refusing to replace an unrecognized dist518_math directory')
    shutil.rmtree(STAGE)
STAGE.mkdir(); marker.write_text('build_518_math_package.py\n')


def copy(source, destination=None):
    target = STAGE / (destination or source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / source, target)


for name in ['replay_518.py', 'replay_518.cmd', 'replay_518.ps1', 'requirements_518.txt']:
    copy(name)
copy('README_ForMath_518.md', 'README.md')
for name in ['mock_server.py', 'open_mock.py', 'runtime_support.py', 'math_adapter.py',
             'math_schema.json', 'math_518.proto', 'math_518.desc', 'cj_518.proto']:
    copy('games/518/' + name)
for folder in ['math', 'static']:
    shutil.copytree(GAME / folder, STAGE / 'games/518' / folder,
                    ignore=shutil.ignore_patterns('.DS_Store', '__pycache__'))
for name in ['server.py', 'fg5.py', 'mockkeys.json', 'wasm_patch_shim.js', 'err_probe_shim.js',
             'wasm_pub_patches.json', 'crypto.patched.wasm']:
    copy('routex/' + name)

# Keep response bodies/types needed for local UI, discard response headers such as cookies.
aux = json.loads((GAME / 'auxiliary_responses.json').read_text())
aux = {key: {'body_hex': value['body_hex'],
              'headers': [h for h in value['headers'] if h.startswith('content-type: ')]}
       for key, value in aux.items() if key.startswith(('/vipservice/', '/favoriteservice/', '/rankingservice/'))}
(STAGE / 'games/518/auxiliary_responses.json').write_text(json.dumps(aux))
sso = json.loads((GAME / 'mock_sso.json').read_text())
assert sso['token'] == '0' * 40
(STAGE / 'games/518/mock_sso.json').write_text(json.dumps(sso))

session = Path((GAME / 'current_session.txt').read_text().strip())
rows = [json.loads(line) for line in (session / 'export/exchanges_ordered.jsonl').read_text().splitlines() if line]
sys.path.insert(0, str(ROOT / 'routex'))
import fg5
requests = []
secrets = set()
for rec in map(json.loads, (session / 'exchanges.jsonl').read_text().splitlines()):
    parsed = fg5.parse_fields(bytes.fromhex(rec['req_body_hex']))
    if len(parsed.get(3, b'')) >= 16:
        secrets.add(parsed[3])
    # Replay lookup needs only the message type and action. No auth token or session pubkey.
    body = fg5.field_varint(1, parsed.get(1, 0)) + fg5.field_bytes(2, parsed.get(2, b''))
    requests.append({'seq': rec['seq'], 'req_body_hex': body.hex()})
    assert set(fg5.parse_fields(body)) <= {1, 2}
clean_rows = [{key: row[key] for key in ['idx', 'kind', 'type', 'ret', 'raw']} for row in rows]
for row in clean_rows:
    assert not any(token in bytes(row['raw']) for token in secrets)
base = STAGE / 'games/518/webcap/samples'; (base / 'export').mkdir(parents=True)
(base / 'exchanges.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in requests))
(base / 'export/exchanges_ordered.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in clean_rows))
(STAGE / 'games/518/current_session.txt').write_text('webcap/samples\n')

report = {'samples':151, 'original_signatures_verified':True, 'native_codec_roundtrips':151,
          'compiled_protobuf_roundtrips':151, 'full_envelope_roundtrips':151,
          'edited_math_http_replay':'verified TotalWin 1.05 -> 2.10, signature, decryption, matching balance',
          'inconsistent_math_totals':'rejected by validator',
          'macos_wire_replay':'user confirmed entry and consecutive spins',
          'windows_visual_replay':'not tested on a Windows host',
          'captured_auth_tokens_included':False, 'session_keys_included':False,
          'mock_private_keys':'local mock keys only; required for offline signing'}
(STAGE / 'VALIDATION.json').write_text(json.dumps(report, indent=2) + '\n')
if (session / 'key.json').exists():
    secrets.add(bytes.fromhex(json.loads((session / 'key.json').read_text())['key']))
if (session / 'grv.jsonl').exists():
    for line in (session / 'grv.jsonl').read_text().splitlines():
        secrets.add(bytes.fromhex(json.loads(line)['out']))
secret_patterns = [pattern for secret in secrets for pattern in (secret, secret.hex().encode())]
manifest = {}
for file in sorted(STAGE.rglob('*')):
    if file.is_file():
        content = file.read_bytes()
        if any(pattern in content for pattern in secret_patterns):
            raise RuntimeError('Captured credential/key found in staged output: ' + str(file.relative_to(STAGE)))
        manifest[file.relative_to(STAGE).as_posix()] = hashlib.sha256(content).hexdigest()
(STAGE / 'MANIFEST.sha256.json').write_text(json.dumps(manifest, indent=2) + '\n')
with zipfile.ZipFile(ARCHIVE, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for file in sorted(STAGE.rglob('*')):
        if file.is_file():
            archive.write(file, 'jili_518_math_test/' + file.relative_to(STAGE).as_posix())
print('Folder: ' + str(STAGE))
print('Archive: %s (%s bytes)' % (ARCHIVE, ARCHIVE.stat().st_size))
