"""Write sample coverage and provenance without copying live credentials."""
from collections import Counter
import hashlib,json
from pathlib import Path
from math_adapter import SCHEMA,records
HERE=Path(__file__).resolve().parent
counts=Counter();modes=Counter();bets=Counter();unknown=Counter();sources={};fields_seen=Counter()
for session in (HERE/'webcap').iterdir():
    source_path=session/'source.json'
    source=json.loads(source_path.read_text()) if source_path.exists() else {'session':session.name,'currency':'unrecorded'}
    for p in (session/'math').glob('*.json'):
        if p.stem.isdigit():sources[p.stem]={'currency': source.get('currency','unrecorded'), 'session': session.name}

def visit(obj,name,path):
    table={f['number']:f for f in SCHEMA[name]}
    for n,w,v,raw in records(bytes(obj.get('_wire',[]))):
        if n not in table:unknown[path+'.f'+str(n)]+=1
        else:fields_seen[path+'.'+table[n]['name']]+=1
    for f in table.values():
        if f['type'] in SCHEMA:
            val=obj[f['name']]
            for sub in val if f['repeated'] else [val]:visit(sub,f['type'],path+'.'+f['name'])

for p in sorted((HERE/'math').glob('*.json')):
    if not p.stem.isdigit():continue
    j=json.loads(p.read_text());counts['spins']+=1;d=j['data'];bets[str(j['spinReq']['bet'])]+=1
    modes[str((d['GameType'],d['ReelType'],d['AckType'],d['Extra']))]+=1
    if d['TotalWin']>0:counts['winning_spins']+=1
    if len(d['RoundInfo'])>1:counts['multiple_RoundInfo']+=1
    for stage in d['RoundInfo']:
        for name in ('CollectList','MysteryList','AwardDataVec','PotList'):
            if stage[name]:counts[name+'_stages']+=1
        if stage['GetReSpin'] or stage['ReSpinTotalRound'] or stage['ReSpinRemainRound']:counts['respin_stages']+=1
    visit(dict(j,totalWin=d['TotalWin']),'Envelope','response')
report={'counts':dict(counts),'bets':dict(bets),'modes_GameType_ReelType_AckType_Extra':dict(modes),
        'unknown_fields_preserved_in_wire_sidecars':dict(unknown),'observed_fields':dict(fields_seen),
        'missing':['更多重轉、加次數、連續觸發與各獎池案例','其他下注級距、特殊模式與錯誤回覆','未出現的 codec 欄位及非空 service','離線瀏覽器畫面與長時間演出驗收']}
(HERE/'coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(HERE/'math_sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'counts':dict(counts),'unknown':dict(unknown)},ensure_ascii=False))
