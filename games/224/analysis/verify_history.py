#!/usr/bin/env python3
"""Verify captured history entities and three seed-to-multiplier chains."""
import sys,json,hashlib,math
from pathlib import Path
from urllib.parse import urlsplit
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
from math_adapter import wire_to_math
from watch_live_math import command
offline='--offline' in sys.argv or not (HERE/'current_session.txt').exists()
s=HERE/'replay_data' if offline else Path((HERE/'current_session.txt').read_text().strip());p=s/'history' if offline else s/'history_netlog';rows=json.loads((p/('manifest.json'if offline else 'manifest.local.json')).read_text());data={};fair=[]
for r in rows:
 body=(p/r['body']).read_bytes();assert hashlib.sha256(body).hexdigest()==r['sha256'];u=urlsplit(r['url'])
 if '/v2/'not in u.path:continue
 d=json.loads(body);assert d['Code']==0
 if u.path=='/v2/fairness/steps':fair.append(d['Data'])
 else:data[u.path]=d['Data']
frames=[]
for frame_source in ((s/'proof_frames.jsonl',s/'frames.jsonl')if offline else(HERE/'webcap/20261109-100032/frames.jsonl',s/'frames.jsonl')):
 raw=[json.loads(l)for l in frame_source.read_text().splitlines()]
 app=[r for r in raw if (r['dir']=='RECV' and command(r['hex'])in(10,13,16))or(r['dir']=='SEND'and command(r['hex'])==10)]
 frames+=wire_to_math(app)
verified=[]
for h in data['/v2/history/aviator/get-history-record']:
 rid=h['RoundIndex'];d=data['/v2/history/aviator/get-detail-record/'+rid]
 m=json.loads((HERE/'math'/(rid+'.json')).read_text());assert float(h['Bet'])==sum(b.get('bet',0)for b in m['spinReq']['betData']);assert float(h['Win'])==m['data']['flyEnd'].get('totalWin',0);assert float(h['PostMoney'])==m['data']['flyEnd']['coin'];assert float(h['NetValue'])==float(h['Win'])-float(h['Bet'])
 for detail in d['Details']:
  assert float(detail['Bet'])==m['spinReq']['betData'][detail['BetType']]['bet']
  cash=next((c for c in m['data']['cashOuts']if c.get('betType',0)==detail['BetType']),{})
  assert float(detail['Win'])==cash.get('win',0);assert float(detail['WinRate'])==cash.get('myRate',0)
 digest=hashlib.sha512(''.join(d[k]for k in ('ServerSeed','ClientSeed1','ClientSeed2','ClientSeed3')).encode()).hexdigest();assert digest==d['TotalSeedHashed'];assert d['ClientSeed1']==m['spinReq']['seed']
 n=int(digest[:8],16);computed=(2**32-1)/(n+1)*(1-.03);actual=m['data']['flyEnd']['endRate'];assert math.isclose(computed,actual,rel_tol=0,abs_tol=2e-14)
 f=next(x for x in fair if x[0]['Sha512Data']['Sha512']==digest);parts={x['Type']:x for x in f};assert parts['hexToDecimal']['HexsData']['Result']==str(n);assert float(parts['multiEdged']['MultiEdgedData']['FinalResult'])==actual;assert parts['finalResult']['Value']==math.floor(actual*100)/100
 commitment=hashlib.sha256(d['ServerSeed'].encode()).hexdigest();pre=None;found=False
 for x in frames:
  if x['message']=='Info':pre=x
  elif x['message']=='BetReq' and x['data'].get('seed')==d['ClientSeed1']and pre and pre['data']['serverHash']==commitment:found=True
 assert found
 verified.append({'round_id':rid,'history_math_amounts_match':True,'detail_cashouts_match':True,'server_sha256_prebet_commitment':True,'ordered_four_seed_utf8_sha512_match':True,'first_8_hex_to_integer':True,'multiplier_matches_fly_end':True,'display_floor_2_decimals':True,'end_rate':actual,'formula_absolute_error':abs(computed-actual)})
report={'session':s.name,'http_entities_sha256_verified':len(rows),'history_rows':len(verified),'detail_responses':len(verified),'fairness_responses':len(fair),'verified':verified,'formula':'SHA512(UTF8(ServerSeed + ClientSeed1 + ClientSeed2 + ClientSeed3)); N=int(first 8 hex,16); (2^32-1)/(N+1)*(1-0.03)','scope':'Three captured rounds verified; boundary clamps, minimum/maximum rates and full distribution/RTP not established. Client2/3 authenticity and shared multiplayer outcomes not established.','replay':'Original Nuxt UI; captured list/details/fairness; local mock auth only. Captured list is a historical snapshot, local replay wagers do not add real history.'}
(HERE/'analysis/history_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
