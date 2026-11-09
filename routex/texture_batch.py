#!/usr/bin/env python3
"""Complete exact versioned WebP variants across game folders and verify local HTTP.

No game/login endpoints, placeholder images, live browser or VPN changes.
Existing invalid images require --repair-invalid and are backed up before replacement.
"""
import argparse,functools,hashlib,json,os,struct,tempfile,threading,time,urllib.error,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import texture_variants as tv
ROOT=Path(__file__).resolve().parent.parent
HOST='uat-wbgame.jlfafafa3.com'

def locations(gid):
 if gid=='shared':return ROOT/'games/shared',ROOT/'games/shared',ROOT/'games/shared/texture_validation.json'
 if gid=='legacy_696':return ROOT/'games/696',ROOT/'game_site_backup'/HOST,ROOT/'games/696/texture_validation_legacy.json'
 game=ROOT/'games'/gid
 return game,game/'static',game/'texture_validation.json'

def backup_path(gid,relative):
 # The shared root itself serves assets; keep invalid backups outside that root.
 game=ROOT/'games/696'if gid=='shared'else locations(gid)[0]
 return game/'texture_repairs/original_invalid'/gid/relative

def validate(data,row,path):
 dimensions=tv.webp_dimensions(data)
 if row.get('width')and dimensions!=(row['width'],row['height']):raise ValueError('Original WebP dimensions differ from metadata')
 astc=path.with_suffix('.astc')
 if astc.exists():
  h=astc.read_bytes()[:16]
  if h[:4]!=b'\x13\xab\xa1\x5c' or dimensions!=(int.from_bytes(h[7:10],'little'),int.from_bytes(h[10:13],'little')):raise ValueError('ASTC/WebP dimensions mismatch')
 return dimensions

def publish(path,data,old=None,backup=None):
 path.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.'+path.name+'.',delete=False)as f:
  temp=Path(f.name);f.write(data);f.flush();os.fsync(f.fileno())
 try:
  if old is None:
   try:os.link(temp,path)
   except FileExistsError:
    if path.read_bytes()!=data:raise ValueError('Concurrent asset edit preserved: '+str(path))
  else:
   if path.read_bytes()!=old:raise ValueError('Asset changed during download; preserved: '+str(path))
   backup.parent.mkdir(parents=True,exist_ok=True)
   if not backup.exists():backup.write_bytes(old)
   elif backup.read_bytes()!=old:raise ValueError('Existing backup differs')
   os.replace(temp,path)
 finally:temp.unlink(missing_ok=True)

class QuietHandler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass


def run(games,fetch=False,repair=False,workers=8):
 before={};jobs={};existing={};events=[];job_errors=[]
 for gid in games:
  game,root,_=locations(gid);report=tv.audit(root);before[gid]=report
  for row in report['assets']:
   path=root/row['path']
   if row['status']=='ok':existing.setdefault(row['path'],[]).append((path,row['sha256']));continue
   if not fetch:continue
   old=path.read_bytes()if path.exists()else None
   if old is not None and not repair:continue
   jobs.setdefault(row['path'],[]).append((gid,path,row,old))
 print(json.dumps({'stage':'plan','games':games,'required_webp':sum(r['required_webp']for r in before.values()),'unique_downloads':len(jobs),'target_repairs':sum(len(j)for j in jobs.values())}),flush=True)
 def download(entry):
  relative,targets=entry;data=None;source='original-cdn';last=None
  for attempt in range(3):
   try:
    request=urllib.request.Request('https://'+HOST+'/'+relative,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(request,timeout=25)as response:
     if response.status!=200:raise ValueError('Unexpected HTTP status')
     data=response.read()
    tv.webp_dimensions(data);break
   except (urllib.error.URLError,TimeoutError,ValueError)as e:
    last=e
    if isinstance(e,urllib.error.HTTPError)and e.code not in (408,429)and e.code<500:break
    if attempt<2:time.sleep(attempt+1)
  if data is None:
   # Same relative path includes the immutable original UUID and version.
   for candidate,digest in existing.get(relative,[]):
    cached=candidate.read_bytes()
    if hashlib.sha256(cached).hexdigest()==digest:
     tv.webp_dimensions(cached);data=cached;source='existing-validated-same-version';break
  if data is None:
   quarantined=[]
   if isinstance(last,urllib.error.HTTPError)and last.code==404:
    for gid,path,row,old in targets:
     if old is not None:
      backup=backup_path(gid,relative)
      backup.parent.mkdir(parents=True,exist_ok=True)
      if path.read_bytes()!=old:raise ValueError('Concurrent invalid asset edit preserved')
      if backup.exists():
       if backup.read_bytes()!=old:raise ValueError('Backup content differs')
      else:os.link(path,backup)
      path.unlink()
      quarantined.append({'game_id':gid,'path':relative,'action':'quarantined-invalid-unrecoverable','source':'invalid asset; original CDN 404','backup':str(backup.relative_to(ROOT))})
   return quarantined,{'path':relative,'error':str(last),'games':[t[0]for t in targets]}
  out=[]
  for gid,path,row,old in targets:
   try:
    dimensions=validate(data,row,path)
    backup=backup_path(gid,relative) if old is not None else None
    publish(path,data,old,backup)
    out.append({'game_id':gid,'path':relative,'action':'repaired-invalid'if old is not None else 'added','source':source,'sha256':hashlib.sha256(data).hexdigest(),'dimensions':dimensions,'backup':str(backup.relative_to(ROOT))if backup else None})
   except Exception as e:out.append({'game_id':gid,'path':relative,'error':str(e)})
  return out,None
 if jobs:
  with ThreadPoolExecutor(max_workers=workers)as pool:
   futures=[pool.submit(download,item)for item in sorted(jobs.items())]
   completed=0
   for future in as_completed(futures):
    out,error=future.result();events.extend(out)
    if error:job_errors.append(error)
    completed+=1
    if completed%100==0 or completed==len(jobs):print(json.dumps({'stage':'download','completed_urls':completed,'total_urls':len(jobs),'file_updates':len(events),'failed_urls':len(job_errors)}),flush=True)
 results={}
 def verify(gid):
  game,static,report_path=locations(gid)
  handler=functools.partial(QuietHandler,directory=str(static))
  httpd=ThreadingHTTPServer(('127.0.0.1',0),handler);httpd.daemon_threads=True
  thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
  try:r=tv.audit(static,base_url='http://127.0.0.1:%d'%httpd.server_port)
  finally:httpd.shutdown();httpd.server_close();thread.join()
  r['http_server_kind']='isolated game static root; not a browser or complete replay test'
  r['batch_actions']={key:sum(e.get('action')==key and e['game_id']==gid for e in events)for key in ['added','repaired-invalid','quarantined-invalid-unrecoverable']}
  report_path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
  return gid,{'passed':r['passed'],'active_passed':r['active_passed'],'active_required_webp':r['active_required_webp'],'active_valid_webp':r['active_valid_webp'],'historical_asset_errors':r['historical_asset_errors'],'required_webp':r['required_webp'],'valid_webp':r['valid_webp'],'http_verified':r['http_verified'],'unavailable_import_packs':len(r['unavailable_import_packs']),'binary_import_packs':len(r['binary_import_packs']),'actions':r['batch_actions'],'errors':[{'path':x['path'],'error':x['error']}for x in r['assets']if x['status']!='ok']}
 with ThreadPoolExecutor(max_workers=3)as pool:
  for gid,result in pool.map(verify,games):
   results[gid]=result;print(json.dumps({'stage':'verified','game_id':gid,**{k:v for k,v in result.items()if k not in ('errors','historical_asset_errors')}}),flush=True)
 report={'created_utc':datetime.now(timezone.utc).isoformat(),'passed':all(r['passed']for r in results.values()),'games':results,'required_webp':sum(r['required_webp']for r in results.values()),'valid_webp':sum(r['valid_webp']for r in results.values()),'http_verified':sum(r['http_verified']for r in results.values()),'unique_download_urls':len(jobs),'actions':events,'download_errors':job_errors,'windows_visual_verification':'not performed','scope':'Available metadata, captured ASTC counterparts and all existing WebP. Unavailable/binary import packs remain explicitly listed per game.','http_verification':'Each game static root served only on an ephemeral loopback port; no live game APIs or browser actions.'}
 report.update(active_passed=all(r['active_passed']for r in results.values()),active_required_webp=sum(r['active_required_webp']for r in results.values()),active_valid_webp=sum(r['active_valid_webp']for r in results.values()))
 current_games=[r for gid,r in results.items()if gid.isdigit()]
 report.update(current_games_active_passed=all(r['active_passed']for r in current_games),current_games_active_required_webp=sum(r['active_required_webp']for r in current_games),current_games_active_valid_webp=sum(r['active_valid_webp']for r in current_games))
 target=ROOT/'artifacts/texture_webp_batch.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'stage':'complete','passed':report['passed'],'required':report['required_webp'],'valid':report['valid_webp'],'http_verified':report['http_verified'],'report':str(target)}),flush=True)
 return 0 if report['passed']else 1

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('games',nargs='*');parser.add_argument('--fetch',action='store_true');parser.add_argument('--repair-invalid',action='store_true');parser.add_argument('--include-runtime-mirrors',action='store_true');parser.add_argument('--workers',type=int,default=8);args=parser.parse_args()
 games=args.games or sorted(p.name for p in(ROOT/'games').iterdir()if p.name.isdigit()and(p/'static').is_dir())
 if any(not gid.isdigit()or not(ROOT/'games'/gid/'static').is_dir()for gid in games):parser.error('Use existing numeric game IDs')
 if args.include_runtime_mirrors:games+=['shared','legacy_696']
 if not 1<=args.workers<=12:parser.error('--workers must be 1..12')
 raise SystemExit(run(games,args.fetch,args.repair_invalid,args.workers))
