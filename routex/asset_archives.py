"""Rebuild ignored Cocos ZIP load bundles from tracked, hash-checked asset members."""
import hashlib,json,os,tempfile,zipfile
from pathlib import Path

def member_path(root,relative):
 root=Path(root).resolve();path=(root/relative).resolve()
 if root not in path.parents:raise ValueError('Archive member outside static root')
 return path

def prepare(root):
 root=Path(root).resolve();archives=[]
 for archive in sorted(root.rglob('*.zip')):
  members=[]
  with zipfile.ZipFile(archive)as bundle:
   for item in bundle.infolist():
    if item.is_dir():continue
    relative=(archive.parent.relative_to(root)/item.filename).as_posix();target=member_path(root,relative);data=bundle.read(item)
    if target.exists():
     if target.read_bytes()!=data:raise ValueError('Original ZIP/member content differs: '+relative)
    else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    members.append({'name':item.filename,'path':relative,'sha256':hashlib.sha256(data).hexdigest(),'compression':item.compress_type})
  archives.append({'path':archive.relative_to(root).as_posix(),'original_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'members':members})
 if archives:(root/'archive_manifest.json').write_text(json.dumps({'description':'Original Cocos archive members; ZIPs are local generated runtime files, not versioned','archives':archives},indent=2)+'\n')
 return sum(len(a['members'])for a in archives)

def materialize(root):
 root=Path(root).resolve();manifest=root/'archive_manifest.json'
 if not manifest.exists():return 0
 built=0
 for archive in json.loads(manifest.read_text())['archives']:
  target=member_path(root,archive['path'])
  if target.exists():continue
  target.parent.mkdir(parents=True,exist_ok=True)
  with tempfile.NamedTemporaryFile(dir=target.parent,delete=False)as f:temp=Path(f.name)
  try:
   with zipfile.ZipFile(temp,'w')as bundle:
    for item in archive['members']:
     data=member_path(root,item['path']).read_bytes()
     if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('Archive asset hash mismatch: '+item['path'])
     bundle.writestr(item['name'],data,compress_type=item['compression'])
   os.replace(temp,target);built+=1
  finally:temp.unlink(missing_ok=True)
 return built

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root');p.add_argument('--prepare',action='store_true');a=p.parse_args()
 print(prepare(a.root)if a.prepare else materialize(a.root))
