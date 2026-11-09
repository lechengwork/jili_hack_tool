#!/usr/bin/env python3
"""Restore manifest-declared 9926e assets using the already verified original shared payload."""
import hashlib,json,re
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
PAYLOAD_SHA='6a7340a324579cd3735145aa5c72d0cce9902ce87332edb99ba04c46037e5c82'
ALPHABET='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

def expand_uuid(value):
    if len(value)==36:return value
    if len(value)!=22:raise ValueError('Unsupported Cocos UUID')
    digits=value[:2]+''.join('%03x'%((ALPHABET.index(value[i])<<6)|ALPHABET.index(value[i+1]))for i in range(2,22,2))
    return '-'.join((digits[:8],digits[8:12],digits[12:16],digits[16:20],digits[20:]))

def main():
    source=ROOT/'game_site_backup/uat-wbgame.jlfafafa3.com/fg5/assets/game/native/45/456888e5-c417-4f6c-b4cb-80a274bd089d.9926e.whykq8935c'
    payload=source.read_bytes()
    if hashlib.sha256(payload).hexdigest()!=PAYLOAD_SHA or not hashlib.md5(payload).hexdigest().startswith('9926e'):
        raise ValueError('Original shared payload changed; do not guess replacement bytes')
    report={'source':'previously captured original common 9926e payload','payload_sha256':PAYLOAD_SHA,
            'payload_size':len(payload),'method':'manifest UUID/version + literal filename/extension arrays in original codec bundle',
            'assets':[],'unreferenced_manifest_names':[]}
    pending=[]
    for relative,config_name,index_name in (
        ('pappu/assets/game','config.6f303.json','index.6f303.js'),
        ('aeon/3.8/web-mobile/assets/aeon-script','config.617bb.json','index.617bb.js')):
        folder=HERE/'static'/relative;config=json.loads((folder/config_name).read_text())
        versions=dict(zip(config['versions']['native'][::2],config['versions']['native'][1::2]))
        targets={v[0]:int(k)for k,v in config['paths'].items()if versions.get(int(k))=='9926e'}
        code=(folder/index_name).read_text();arrays=[]
        for match in re.finditer(r'\[(?:\d{1,3},){8,12}\d{1,3}\]',code):
            value=''.join(chr(int(x))for x in match.group()[1:-1].split(','))
            if re.fullmatch('[a-z0-9]{9,13}',value):arrays.append((match.start(),match.end(),value))
        found={}
        for i,(start,end,name)in enumerate(arrays[:-1]):
            if name in targets and arrays[i+1][0]-end<40:
                ext=arrays[i+1][2]
                if name in found and found[name]!=ext:raise ValueError('Conflicting native extension')
                found[name]=ext
        for name in sorted(set(targets)-set(found)):
            report['unreferenced_manifest_names'].append({'bundle':relative,'name':name,'note':'No literal native check in captured script; not fabricated'})
        for name,extension in found.items():
            uuid=expand_uuid(config['uuids'][targets[name]])
            rel=relative+'/native/'+uuid[:2]+'/'+uuid+'.9926e.'+extension
            target=HERE/'static'/rel
            if target.exists()and target.read_bytes()!=payload:raise ValueError('Existing native asset differs: '+rel)
            pending.append(target);report['assets'].append({'path':'/'+rel,'sha256':PAYLOAD_SHA})
    for target in pending:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
    (HERE/'replay_asset_sources.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Restored %d script-declared native assets; no general 404 fallback installed'%len(pending))

if __name__=='__main__':main()
