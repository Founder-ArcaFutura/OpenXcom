"""Full 2^4 offline reward-description factorial, with exact ordered-packet caching."""
import argparse,copy,itertools,json,random,time
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('incentive_probe',ROOT/'scripts/test-conquest-incentives.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
e=n.e
FACTORS=('remove_research_cash','saturate_research','productive_bonus','terror_reward')
ORDERS=('canonical','reversed','seeded')
def configurations():return [dict(zip(FACTORS,bits)) for bits in itertools.product((False,True),repeat=4)]
def code(config):return ''.join(str(int(config[k])) for k in FACTORS)
def reward_text(mission,budget,config):
 short=mission.removeprefix('STR_ALIEN_')
 if short in ('RESEARCH','PROBE_MISSION'):
  gain=int(budget['intelligence']<2) if config['saturate_research'] else 1
  return f"flight: +{0 if config['remove_research_cash'] else 1} resources, +{gain} intelligence"+('; intelligence cap 2' if config['saturate_research'] else '')
 return n.reward_text(mission,budget,config['productive_bonus'] if short in ('HARVEST','ABDUCTION') else config['terror_reward'] if short in ('TERROR','SURFACE_ATTACK') else False)
def transform(state,criteria,data,config):
 if config is None or 'SAVE' not in criteria:return state,dict(criteria)
 state,_=n.transform(state,criteria,data,'explicit_current');result={}
 for key,label in criteria.items():
  if key=='SAVE':result[key]=label;continue
  mission=next(m for m,p in e.PLANS.items() if label==p[1]+'; cost '+str(e.m.PORTFOLIO_COSTS[m]))
  result[key]=mission.removeprefix('STR_ALIEN_').replace('_',' ')+': '+reward_text(mission,data['budget'],config)+'; cost '+str(e.m.PORTFOLIO_COSTS[mission])
 return state,result

def reorder(criteria,order):
 if 'SAVE' not in criteria:return dict(criteria)
 items=list(criteria.items())
 if order=='reversed':items.reverse()
 elif order=='seeded':
  seed=int(e.m.digest(['factorial-order-1729',[k for k,v in items]])[:16],16)
  random.Random(seed).shuffle(items)
 elif order!='canonical':raise ValueError('Unknown order')
 return dict(items)
def packet_key(state,criteria,instructions):return e.m.digest([state,list(criteria.items()),instructions])
def seed_cache(cache):
 count=0
 for manifest in (ROOT/'build/local/conquest-incentives-v1').glob('1999-*/manifest.json'):
  meta=json.loads(manifest.read_text())
  if meta['model']['checkpointSha256']!=e.m.V4_SHA256:continue
  for name in ('scripts/campaign_plans.py','scripts/alien-command-model.py'):
   if meta['scripts'][name]!=e.m.file_digest(ROOT/name):raise ValueError('Prior cache live script mismatch')
  for file in manifest.parent.glob('*.json'):
   if file.stem in ('input','manifest'):continue
   for receipt in json.loads(file.read_text()).get('decisions',[]):
    q=receipt['question']
    if 'instructions' not in q:continue # Single eligible action requires no inference.
    key=packet_key(receipt['state'],q['criteria'],q['instructions'])
    if key in cache:assert cache[key]['receipt']['answer']==receipt['answer'],'Nonidentical prior answer for exact packet'
    cache[key]={'receipt':receipt,'origin':str(file)};count+=1
 return count

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 inputs=n.load_inputs();cache={};seed_count=seed_cache(cache)
 agent,identity=e.m.load_agent(a.checkpoint,'cpu',e.m.V4_SHA256);summary=[];calls=hits=0
 for source,sha,receipt,data,removed in inputs:
  out=a.out/receipt['gameTime'][:7];out.mkdir(exist_ok=True);(out/'input.json').write_text(json.dumps(data,indent=2))
  for order in ORDERS:
   for config in [None,*configurations()]:
    condition='live_wording' if config is None else code(config);stats={'newCalls':0,'cacheHits':0};start=time.perf_counter()
    def choose(state,criteria,instructions):
     nonlocal calls,hits
     state,criteria=transform(state,criteria,data,config);criteria=reorder(criteria,order);key=packet_key(state,criteria,instructions)
     if key in cache:
      entry=cache[key];r=copy.deepcopy(entry['receipt']);stats['cacheHits']+=1;hits+=1
      r['inferenceSource']='EXACT_ORDERED_PACKET_CACHE';r['cacheOrigin']=entry['origin']
      return r['answer']['choice'],r
     label,r=e.m.checked_choice(agent,state,criteria,instructions);calls+=1;stats['newCalls']+=1
     cache[key]={'receipt':copy.deepcopy(r),'origin':str(out/(condition+'-'+order+'.json'))}
     r['inferenceSource']='NEW_LOCAL_INFERENCE';return label,r
    try:
     result=e.plan(copy.deepcopy(data),choose,False,True);n.w.validate(result['operations'],data)
     assert result['remainingProposed']==data['budget']['remaining']-sum(e.m.PORTFOLIO_COSTS[o['mission']] for o in result['operations'])
    except ValueError as error:result={'status':'REJECTED','error':str(error)}
    for plan in result.get('plans',[]):
     plan.pop('pro',None);plan.pop('con',None)
     if config is not None:plan['experimentalRewardDescription']=reward_text(plan['mission'],data['budget'],config)
    result.update(condition=condition,factors=config,order=order,latencyMs=round((time.perf_counter()-start)*1000,2),**stats)
    (out/(condition+'-'+order+'.json')).write_text(json.dumps(result,indent=2))
    row={'decision':receipt['gameTime'],**{k:result.get(k) for k in ('condition','factors','order','operations','remainingProposed','status','error','latencyMs','newCalls','cacheHits')}}
    summary.append(row);(a.out/'progress.json').write_text(json.dumps({'completed':len(summary),'planned':255,'newCalls':calls,'cacheHits':hits,'last':row},indent=2))
    print(json.dumps({'completed':len(summary),'decision':receipt['gameTime'],'condition':condition,'order':order,'status':result['status'],'newCalls':stats['newCalls'],'cacheHits':stats['cacheHits']}),flush=True)
  assert e.m.file_digest(source)==sha,'Original source changed'
  (out/'manifest.json').write_text(json.dumps({'source':str(source),'sourceSha256':sha,'sourceInputSha256':e.m.digest(receipt['input']),'pairedInputSha256':e.m.digest(data),'removedInvalidGeography':removed,'model':identity,'liveChanged':False,'missionsExecuted':False,'APICalls':0,'scripts':{name:e.m.file_digest(ROOT/name) for name in ('scripts/test-conquest-factorial.py','scripts/test-conquest-incentives.py','scripts/campaign_plans.py','scripts/alien-command-model.py')}},indent=2))
 (a.out/'summary.json').write_text(json.dumps({'rows':summary,'model':identity,'newCalls':calls,'cacheHits':hits,'priorSeedReceipts':seed_count,'factors':FACTORS,'orders':ORDERS},indent=2))
if __name__=='__main__':main()
