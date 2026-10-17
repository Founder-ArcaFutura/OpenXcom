"""Offline permutation-mean PLAN policy with disjoint balanced order families."""
import argparse,copy,itertools,json,math,random,time,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('factorial_probe',ROOT/'scripts/test-conquest-factorial.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
e=f.e
ARMS=('single_canonical','single_reversed','single_seeded','aggregate_A','aggregate_B')
def rotations(keys):return [keys[i:]+keys[:i] for i in range(len(keys))]
def families(criteria,family):
 keys=sorted(criteria)
 if family=='B' and len(keys)>2:
  orbit={tuple(x) for x in rotations(keys)}
  rng=random.Random(int(e.m.digest(['permutation-holdout-2903',keys])[:16],16))
  for attempt in range(1000):
   base=list(keys);rng.shuffle(base)
   if tuple(base) not in orbit:keys=base;break
  else:raise ValueError('Cannot create distinct permutation family')
 elif family!='A' and not (family=='B' and len(keys)<=2):raise ValueError('Unknown family')
 return [dict((key,criteria[key]) for key in order) for order in rotations(keys)]
def aggregate_answers(receipts,criteria):
 keys=sorted(criteria);means={k:0. for k in keys};votes={k:0 for k in keys}
 for receipt in receipts:
  ps=receipt['answer']['probabilities']
  if set(ps)!=set(keys) or any(not math.isfinite(v) or not 0<=v<=1 for v in ps.values()) or abs(sum(ps.values())-1)>.01:raise ValueError('Invalid component probabilities')
  for k in keys:means[k]+=ps[k]/len(receipts)
  votes[receipt['answer']['choice']]+=1
 ranked=sorted(keys,key=lambda k:(-means[k],k))
 return ranked[0],means,votes,means[ranked[0]]-means[ranked[1]] if len(keys)>1 else 1.
def seed_cache(cache):
 count=f.seed_cache(cache)
 for manifest in (ROOT/'build/local/conquest-factorial-v1').glob('1999-*/manifest.json'):
  meta=json.loads(manifest.read_text());assert meta['model']['checkpointSha256']==e.m.V4_SHA256
  for name in ('scripts/campaign_plans.py','scripts/alien-command-model.py'):assert meta['scripts'][name]==e.m.file_digest(ROOT/name)
  for path in manifest.parent.glob('*.json'):
   if path.stem in ('input','manifest'):continue
   for r in json.loads(path.read_text()).get('decisions',[]):
    q=r['question']
    if 'instructions' not in q:continue
    key=f.packet_key(r['state'],q['criteria'],q['instructions'])
    if key in cache:assert cache[key]['receipt']['answer']==r['answer']
    cache[key]={'receipt':r,'origin':str(path)};count+=1
 return count

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 inputs=f.n.load_inputs();cache={};seed_count=seed_cache(cache);agent,identity=e.m.load_agent(a.checkpoint,'cpu',e.m.V4_SHA256)
 rows=[];totals={'newModelInferences':0,'automaticDecisions':0,'cacheReuses':0}
 for source,sha,original,data,removed in inputs:
  out=a.out/original['gameTime'][:7];out.mkdir(exist_ok=True);(out/'input.json').write_text(json.dumps(data,indent=2))
  for arm in ARMS:
   stats={k:0 for k in totals};start=time.perf_counter()
   def infer(state,criteria,instructions):
    key=f.packet_key(state,criteria,instructions)
    if key in cache:
     entry=cache[key];r=copy.deepcopy(entry['receipt']);r.update(inferenceSource='EXACT_ORDERED_PACKET_CACHE',cacheOrigin=entry['origin']);stats['cacheReuses']+=1;totals['cacheReuses']+=1
     return r
    label,r=e.m.checked_choice(agent,state,criteria,instructions)
    kind='automaticDecisions' if r.get('source')=='ONLY_ELIGIBLE_CHOICE' else 'newModelInferences'
    stats[kind]+=1;totals[kind]+=1;cache[key]={'receipt':copy.deepcopy(r),'origin':str(out/(arm+'.json'))};r['inferenceSource']='AUTOMATIC' if kind=='automaticDecisions' else 'NEW_LOCAL_INFERENCE';return r
   def choose(state,criteria,instructions):
    state,criteria=f.transform(state,criteria,data,f.configurations()[0])
    if 'SAVE' not in criteria or arm.startswith('single_'):
     order=arm.removeprefix('single_') if arm.startswith('single_') else 'canonical'
     ordered=f.reorder(criteria,order);r=infer(state,ordered,instructions);return r['answer']['choice'],r
    family=arm[-1];orders=families(criteria,family);receipts=[infer(state,ordered,instructions) for ordered in orders]
    label,means,votes,margin=aggregate_answers(receipts,criteria)
    return label,{'state':state,'question':{'type':'choice','instructions':instructions,'criteria':criteria},'answer':{'choice':label,'probabilities':means},'source':'PERMUTATION_MEAN_UNCALIBRATED','family':family,'margin':margin,'votes':votes,'permutations':receipts,'permutationKeys':[list(x) for x in orders],'tokenCount':max(r.get('tokenCount',0) for r in receipts)}
   try:
    result=e.plan(copy.deepcopy(data),choose,False,True);f.n.w.validate(result['operations'],data)
    assert result['remainingProposed']==data['budget']['remaining']-sum(e.m.PORTFOLIO_COSTS[o['mission']] for o in result['operations'])
   except ValueError as error:result={'status':'REJECTED','error':str(error)}
   result.update(arm=arm,latencyMs=round((time.perf_counter()-start)*1000,2),**stats)
   (out/(arm+'.json')).write_text(json.dumps(result,indent=2))
   row={'decision':original['gameTime'],**{k:result.get(k) for k in ('arm','operations','remainingProposed','status','error','latencyMs',*totals)}}
   rows.append(row);(a.out/'progress.json').write_text(json.dumps({'completed':len(rows),'planned':25,'totals':totals,'last':row},indent=2));print(json.dumps(row),flush=True)
  assert e.m.file_digest(source)==sha
  (out/'manifest.json').write_text(json.dumps({'source':str(source),'sourceSha256':sha,'pairedInputSha256':e.m.digest(data),'removedInvalidGeography':removed,'model':identity,'scripts':{name:e.m.file_digest(ROOT/name) for name in ('scripts/test-permutation-commander.py','scripts/test-conquest-factorial.py','scripts/test-conquest-incentives.py','scripts/campaign_plans.py','scripts/alien-command-model.py')},'liveChanged':False,'missionsExecuted':False,'APICalls':0},indent=2))
 (a.out/'summary.json').write_text(json.dumps({'rows':rows,'totals':totals,'priorSeedReceipts':seed_count,'model':identity},indent=2))
if __name__=='__main__':main()
