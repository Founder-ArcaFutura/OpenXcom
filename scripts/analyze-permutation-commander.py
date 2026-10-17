"""Validate and tabulate the offline permutation-mean commander experiment."""
import argparse,collections,csv,json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('permutation_probe',ROOT/'scripts/test-permutation-commander.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def pairs(row):return sorted((o['mission'],o['region']) for o in row['operations'])
def mix(row):return dict(collections.Counter(o['mission'].removeprefix('STR_ALIEN_') for o in row['operations']))
def first_plan(result):
 d=next(d for d in result['decisions'] if d['stage']=='PLAN');label=d['answer']['choice']
 return 'SAVE' if label=='SAVE' else d['question']['criteria'][label].split(':',1)[0]
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--input',type=Path,required=True);a.add_argument('--out',type=Path,required=True);args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 summary=json.loads((args.input/'summary.json').read_text());rows=summary['rows'];assert len(rows)==25
 stored={};derived=[];totals={k:0 for k in summary['totals']};max_tokens=0;components=unanimous=0
 for row in rows:
  assert row['status']!='REJECTED',row
  month=row['decision'][:7];data=json.loads((args.input/month/'input.json').read_text());p.f.n.w.validate(row['operations'],data)
  assert row['remainingProposed']==data['budget']['remaining']-sum(p.e.m.PORTFOLIO_COSTS[o['mission']] for o in row['operations'])
  result=json.loads((args.input/month/(row['arm']+'.json')).read_text());stored[month,row['arm']]=result
  margins=[]
  for d in result['decisions']:
   leaves=d.get('permutations',[d])
   if 'permutations' in d:
    criteria=d['question']['criteria'];orders=p.families(criteria,d['family'])
    assert d['permutationKeys']==[list(x) for x in orders]
    for position in range(len(criteria)):assert collections.Counter(order[position] for order in d['permutationKeys'])==collections.Counter(criteria.keys())
    for sub,order in zip(leaves,orders):assert sub['state']==d['state'] and list(sub['question']['criteria'].items())==list(order.items())
    label,means,votes,margin=p.aggregate_answers(leaves,criteria)
    assert label==d['answer']['choice'] and means==d['answer']['probabilities'] and votes==d['votes'] and margin==d['margin']
    components+=1;unanimous+=int(max(votes.values())==len(leaves));margins.append(margin)
   for leaf in leaves:
    max_tokens=max(max_tokens,leaf.get('tokenCount',0))
    kind=leaf['inferenceSource'];key='cacheReuses' if kind=='EXACT_ORDERED_PACKET_CACHE' else 'automaticDecisions' if kind=='AUTOMATIC' else 'newModelInferences'
    totals[key]+=1
  derived.append({**row,'mix':mix(row),'spend':data['budget']['remaining']-row['remainingProposed'],'deferAll':not row['operations'],'firstPlan':first_plan(result),'minimumAggregateMargin':min(margins) if margins else None})
 assert totals==summary['totals']
 for manifest in args.input.glob('1999-*/manifest.json'):
  meta=json.loads(manifest.read_text());assert p.e.m.file_digest(meta['source'])==meta['sourceSha256']
  for file,sha in meta['scripts'].items():assert p.e.m.file_digest(ROOT/file)==sha
  assert p.e.m.digest(json.loads((manifest.parent/'input.json').read_text()))==meta['pairedInputSha256']
 comparisons=[]
 for month in sorted({r['decision'][:7] for r in rows}):
  a=next(r for r in derived if r['decision'].startswith(month) and r['arm']=='aggregate_A');b=next(r for r in derived if r['decision'].startswith(month) and r['arm']=='aggregate_B')
  da=stored[month,'aggregate_A']['decisions'][0];db=stored[month,'aggregate_B']['decisions'][0]
  assert da['state']==db['state'] and da['question']['criteria']==db['question']['criteria']
  if len(da['question']['criteria'])>2:assert {tuple(x) for x in da['permutationKeys']}.isdisjoint({tuple(x) for x in db['permutationKeys']})
  comparisons.append({'month':month,'exactAgreement':a['operations']==b['operations'],'operationSetAgreement':pairs(a)==pairs(b),'missionMixAgreement':a['mix']==b['mix'],'firstPlanAgreement':a['firstPlan']==b['firstPlan'],'A':a,'B':b})
 stats={}
 for arm in p.ARMS:
  group=[r for r in derived if r['arm']==arm];stats[arm]={'deferAll':sum(r['deferAll'] for r in group),'spend':sum(r['spend'] for r in group),'operationCount':sum(len(r['operations']) for r in group),'mix':dict(collections.Counter(o['mission'].removeprefix('STR_ALIEN_') for r in group for o in r['operations']))}
 result={'rows':derived,'armStats':stats,'familyComparisons':comparisons,'validation':{'legalPortfolios':25,'sourceAndScriptsUnchanged':True,'maxTokens':max_tokens,**totals,'aggregatePlanDecisions':components,'unanimousComponentWinners':unanimous},'interpretation':'Fixed-state score aggregation; not game outcome, calibrated confidence or universal order invariance.'}
 (args.out/'results.json').write_text(json.dumps(result,indent=2))
 with (args.out/'portfolios.csv').open('w',newline='',encoding='utf-8') as file:
  fields=['decision','arm','status','spend','remainingProposed','deferAll','firstPlan','mix','minimumAggregateMargin'];writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader()
  for r in derived:writer.writerow({k:json.dumps(r[k]) if k=='mix' else r[k] for k in fields})
 with (args.out/'component-scores.csv').open('w',newline='',encoding='utf-8') as file:
  fields=['month','arm','stage','decisionIndex','permutationIndex','order','choice','scores','aggregateChoice','aggregateMargin','tokenCount','inferenceSource','cacheOrigin'];writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader()
  for (month,arm),receipt in stored.items():
   for i,d in enumerate(receipt['decisions']):
    for j,leaf in enumerate(d.get('permutations',[d])):
     writer.writerow({'month':month,'arm':arm,'stage':d['stage'],'decisionIndex':i,'permutationIndex':j,'order':json.dumps(list(leaf['question']['criteria'])),'choice':leaf['answer']['choice'],'scores':json.dumps(leaf['answer']['probabilities']),'aggregateChoice':d['answer']['choice'] if 'permutations' in d else '', 'aggregateMargin':d.get('margin',''),'tokenCount':leaf.get('tokenCount',''),'inferenceSource':leaf['inferenceSource'],'cacheOrigin':leaf.get('cacheOrigin','')})
 print(json.dumps(result['validation']));print(json.dumps(stats))
 for row in comparisons:print(json.dumps({k:v for k,v in row.items() if k not in ('A','B')}))
if __name__=='__main__':main()
