"""Validate fixed first-decision convergence and export family/component tables."""
import argparse,csv,json,collections,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('convergence',ROOT/'scripts/test-permutation-convergence.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--input',type=Path,required=True);a.add_argument('--out',type=Path,required=True);args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 source=json.loads((args.input/'summary.json').read_text());rows=[];leaves=[];new=hits=max_tokens=0
 for state in source['states']:
  month=state['month'];folder=args.input/month;packet=json.loads((folder/'packet.json').read_text());criteria=packet['criteria'];orders=c.family_orders(criteria);seen=set()
  meta=json.loads((folder/'manifest.json').read_text());assert c.p.e.m.file_digest(meta['source'])==meta['sourceSha256']
  for file,sha in meta['scripts'].items():assert c.p.e.m.file_digest(ROOT/file)==sha
  assert c.p.e.m.digest(json.loads((folder/'input.json').read_text()))==meta['pairedInputSha256']
  for family,r in state['families'].items():
   current={tuple(x) for x in r['orders']};assert seen.isdisjoint(current);seen.update(current);assert r['orders']==[list(x) for x in orders[family]]
   for i,leaf in enumerate(r['components']):
    assert leaf['state']==packet['state'] and list(leaf['question']['criteria'].items())==list(orders[family][i].items())
    max_tokens=max(max_tokens,leaf.get('tokenCount',0));is_new=leaf['inferenceSource']=='NEW_LOCAL_INFERENCE';new+=is_new;hits+=not is_new
    leaves.append({'month':month,'family':family,'orderIndex':i,'order':json.dumps(r['orders'][i]),'choice':leaf['answer']['choice'],'scores':json.dumps(leaf['answer']['probabilities']),'inferenceSource':leaf['inferenceSource'],'cacheOrigin':leaf.get('cacheOrigin','')})
   label,means,votes,margin=c.p.aggregate_answers(r['components'],criteria);assert (label,means,votes,margin)==(r['choice'],r['meanScores'],r['votes'],r['margin'])
   rows.append({'month':month,'kind':'family','name':family,'choice':label,'mission':r['description'].split(':',1)[0],'margin':margin,'components':len(r['components']),'scores':means})
  assert len(seen)==len(criteria)*6
  for names,r in state['pools'].items():
   components=[leaf for family in names for leaf in state['families'][family]['components']];label,means,votes,margin=c.p.aggregate_answers(components,criteria)
   assert (label,means,votes,margin)==(r['choice'],r['meanScores'],r['votes'],r['margin'])
   rows.append({'month':month,'kind':'pool','name':names,'choice':label,'mission':r['description'].split(':',1)[0],'margin':margin,'components':len(components),'scores':means})
 assert (new,hits)==(source['newModelInferences'],source['cacheReuses']);assert len(leaves)==72
 result={'rows':rows,'validation':{'componentEvaluations':72,'newModelInferences':new,'cacheReuses':hits,'maxTokens':max_tokens,'sourceAndLiveScriptsUnchanged':True,'pairwiseDisjointBalancedFamiliesPerState':6,'firstPlanOnly':True},'model':source['model']}
 (args.out/'results.json').write_text(json.dumps(result,indent=2))
 with (args.out/'convergence.csv').open('w',newline='',encoding='utf-8') as file:
  fields=['month','kind','name','choice','mission','margin','components','scores'];writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader()
  for r in rows:writer.writerow({**r,'scores':json.dumps(r['scores'])})
 with (args.out/'component-scores.csv').open('w',newline='',encoding='utf-8') as file:
  writer=csv.DictWriter(file,fieldnames=list(leaves[0]));writer.writeheader();writer.writerows(leaves)
 print(json.dumps(result['validation']))
 for r in rows:print(r['month'],r['kind'],r['name'],r['mission'],round(r['margin'],6))
if __name__=='__main__':main()
