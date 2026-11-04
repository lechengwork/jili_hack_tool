#!/usr/bin/env python3
"""Build and independently exercise the standalone 807 probability handoff."""
import hashlib,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
GAME=ROOT/'games/807'
STAGE=ROOT/'dist807_math'
ARCHIVE=ROOT/'jili_807_math_test_20261104.zip'
marker=STAGE/'.generated_807_package'
if STAGE.exists():
 if not marker.exists():raise RuntimeError('Refusing to replace an unrecognized dist807_math directory')
 shutil.rmtree(STAGE)
STAGE.mkdir();marker.write_text('build_807_math_package.py\n')
def copy(source,dest=None):
 target=STAGE/(dest or source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source,target)
for name in ['replay_807.py','replay_807.cmd','replay_807.ps1','requirements_807.txt']:copy(name)
copy('README_ForMath_807.md','README.md')
for name in ['mock_server.py','open_mock.py','runtime_support.py','math_adapter.py','math_schema.json','math_807.proto','math_807.desc','wire_807.proto','wire_807.desc','replay_samples.json','verify_mock.py','verify_math.py','capture_summary.json','wasm_patch_shim.js','RULES_807.md','696_807_FIELD_MAP.md','HANDOFF.md','WATCH_FIELDS.md','login_config.example.json']:
 copy('games/807/'+name)
for folder in ['math','static','handoff']:
 shutil.copytree(GAME/folder,STAGE/'games/807'/folder,ignore=shutil.ignore_patterns('.DS_Store','__pycache__','*.download'))
for name in ['server.py','fg5.py','mockkeys.json','wasm_patch_shim.js','err_probe_shim.js','wasm_pub_patches.json','crypto.patched.wasm']:
 copy('routex/'+name)
# Exercise only staged code and data, so missing repo dependencies are detected.
env=dict(os.environ)
for key in ['SCHEMA_PROBE','REPLAY_ROUNDS','REPLAY_SESSION','MATH_DIR','REPLAY_SOURCE']:env.pop(key,None)
for command in [
 [sys.executable,'-B',str(STAGE/'games/807/math_adapter.py'),'--selftest'],
 [sys.executable,'-B',str(STAGE/'replay_807.py'),'--selftest'],
 [sys.executable,'-B',str(STAGE/'games/807/verify_mock.py'),'--source','math'],
 [sys.executable,'-B',str(STAGE/'games/807/verify_math.py')]]:
 subprocess.run(command,cwd=str(STAGE),env=env,check=True)
# Build reports come from actual checks, not hard-coded success values.
coverage=json.loads((STAGE/'games/807/math/COVERAGE.json').read_text())
protocol=json.loads((STAGE/'games/807/mock_validation.json').read_text())
editing=json.loads((STAGE/'games/807/math/EDIT_VALIDATION.json').read_text())
report={'samples':coverage['samples'],'byte_roundtrips':coverage['wire_roundtrips'],'compiled_protobuf_roundtrips':coverage['independent_compiled_protobuf_roundtrips'],'standalone_https':protocol,'edited_math_http':editing,'macos_wire_browser':'user confirmed entry and consecutive spins','macos_edited_math_browser':'not yet visually verified','windows_browser':'not tested on a Windows host','captured_credentials_included':False,'private_keys':'local mock signing/encryption keys only; not live server keys','schema_scope':'2399 spins; repeated f9 contexts and all observed fields preserved. Unseen f17[2] and nonempty f9 remain undefined; see INTERFACE.md.'}
(STAGE/'VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.rmtree(STAGE/'games/807/runtime',ignore_errors=True)
# No original login, auth token or per-session key may enter the output.
sys.path.insert(0,str(ROOT/'routex'));import fg5
secrets=set()
config_path=ROOT/'config.json'
if config_path.exists():
 for account in json.loads(config_path.read_text()).get('login_accounts',{}).values():
  if isinstance(account,dict) and account.get('token'):secrets.add(account['token'].encode())
for session in (GAME/'webcap').glob('*'):
 if not session.is_dir():continue
 for line in (session/'exchanges.jsonl').read_text().splitlines() if (session/'exchanges.jsonl').exists() else []:
  token=fg5.parse_fields(bytes.fromhex(json.loads(line)['req_body_hex'])).get(3,b'')
  if len(token)>=16:secrets.add(token)
 if (session/'key.json').exists():secrets.add(bytes.fromhex(json.loads((session/'key.json').read_text())['key']))
 for line in (session/'grv.jsonl').read_text().splitlines() if (session/'grv.jsonl').exists() else []:
  raw=bytes.fromhex(json.loads(line)['out'])
  if len(raw)>=32:secrets.add(raw)
patterns=[pattern for secret in secrets for pattern in (secret,secret.hex().encode())]
manifest={}
for file in sorted(STAGE.rglob('*')):
 if file.is_file():
  content=file.read_bytes()
  if any(pattern in content for pattern in patterns):raise RuntimeError('Captured credential found in staged file: '+str(file.relative_to(STAGE)))
  manifest[file.relative_to(STAGE).as_posix()]=hashlib.sha256(content).hexdigest()
(STAGE/'MANIFEST.sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for file in sorted(STAGE.rglob('*')):
  if file.is_file():z.write(file,'jili_807_math_test/'+file.relative_to(STAGE).as_posix())
print('Archive:',ARCHIVE,'bytes:',ARCHIVE.stat().st_size,'files:',len(manifest)+1)
