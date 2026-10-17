"""Frozen monthly comparison: current sequential Laya versus whole legal portfolios."""
import argparse,importlib.util,json,random,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('experiment',ROOT/'scripts/test-campaign-plans.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)

def eligible(data):
 b,menu,beliefs,s=e.m.portfolio_input(data)
 reports={x['region']:x['independentSources'] for x in beliefs}
 regions,basis=e.m.search_region_pool(sorted({x['region'] for x in menu if x['mission']=='STR_ALIEN_RETALIATION'}),reports,s)
 if (reports or s['lossAssignments']) and basis=='NO_MATCHING_EVIDENCE_EXPLORATION':regions=[]
 return [x for x in menu if x['mission']!='STR_ALIEN_RETALIATION' or x['region'] in regions]

def validate(ops,data):
 menu=eligible(data);b=data['budget']
 if len(ops)>b['maxOperations'] or len({(o['mission'],o['region']) for o in ops})!=len(ops):raise ValueError('Invalid portfolio count/duplicate')
 if any(o not in menu for o in ops):raise ValueError('Ineligible operation')
 spent=sum(e.m.PORTFOLIO_COSTS[o['mission']] for o in ops)
 if spent>b['remaining']:raise ValueError('Over budget')
 return spent

def candidates(data,baseline):
 b,_,beliefs,s=e.m.portfolio_input(data);menu=eligible(data)
 reports={x['region']:x['independentSources'] for x in beliefs};losses={x['region']:x['count'] for x in s['lossAssignments']}
 productive=e.planner.campaign_lessons(b,beliefs,s)['productive']
 motifs={'capacity':['HARVEST','ABDUCTION','RESEARCH','HARVEST','ABDUCTION','RESEARCH'],
  'control':['INFILTRATION','HARVEST','ABDUCTION','RESEARCH','INFILTRATION','HARVEST'],
  'pressure':['TERROR','HARVEST','INFILTRATION','RESEARCH','ABDUCTION','TERROR'],
  'information':['RETALIATION','RESEARCH','RESEARCH','ABDUCTION','RESEARCH','HARVEST']}
 result=[];seen=set()
 def add(ops,source):
  validate(ops,data);key=tuple(sorted((o['mission'],o['region']) for o in ops))
  if key not in seen:seen.add(key);result.append({'id':'C'+str(len(result)),'source':source,'operations':ops,'cost':validate(ops,data)})
 for name,types in motifs.items():
  ops=[];remaining=b['remaining']
  for short in types:
   if len(ops)>=b['maxOperations']:break
   mission='STR_ALIEN_'+short
   options=[o for o in menu if o['mission']==mission and o not in ops and e.m.PORTFOLIO_COSTS[mission]<=remaining]
   if not options:continue
   def priority(o):
    r=o['region']
    if short=='RETALIATION':return (-reports.get(r,0),-losses.get(r,0),r)
    successful=any(x[0]==short and x[1]==r.removeprefix('STR_') for x in productive)
    return (losses.get(r,0),reports.get(r,0),not successful,r)
   chosen=min(options,key=priority);ops.append(chosen);remaining-=e.m.PORTFOLIO_COSTS[mission]
  if ops:add(ops,name)
 add(baseline,'current_sequential_output');add([],'defer')
 return result

def choose_whole(data,roster,choose,order):
 b,_,beliefs,s=e.m.portfolio_input(data)
 state={'goal':'Conquer Earth. Choose one complete executable portfolio.',
  'remaining':b['remaining'],'carry_limit':b['carryCap'],'capacity':b['maxOperations'],
  'lessons':e.planner.campaign_lessons(b,beliefs,s),
  'limits':'Rewards conditional; no base assault or recurring pact/base income. No reports is not safety.',
  'legend':'R research; H harvest; A abduction; I infiltration; S base search; T terror; B base. N/S/C/SE mean North/South/Central/South East.'}
 names={'RESEARCH':'R','HARVEST':'H','ABDUCTION':'A','INFILTRATION':'I','RETALIATION':'S','TERROR':'T','BASE':'B'}
 def region_name(region):
  return region.removeprefix('STR_').replace('SOUTH_EAST','SE').replace('NORTH','N').replace('SOUTHERN','S').replace('SOUTH','S').replace('CENTRAL','C').replace('_',' ').title().replace('Se ','SE ')
 criteria={}
 for index in order:
  c=roster[index]
  criteria[c['id']]=(f"Cost {c['cost']}: "+'; '.join(names[o['mission'].removeprefix('STR_ALIEN_')]+' '+region_name(o['region']) for o in c['operations'])) if c['operations'] else f"Defer; carry {min(b['remaining'],b['carryCap'])}, forfeit {max(0,b['remaining']-b['carryCap'])}"
 label,receipt=choose(e.m.canonical(state),criteria,'Select one portfolio to advance conquest using the observed campaign results.')
 if label not in criteria:raise ValueError('Invalid portfolio selection')
 c=next(x for x in roster if x['id']==label);validate(c['operations'],data)
 return {'selectedId':label,'source':c['source'],'operations':c['operations'],'remaining':b['remaining']-c['cost'],'decision':receipt,'displayOrder':[roster[i]['id'] for i in order]}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();import yaml
 paths=[ROOT/'build/local/campaign-january-input.json',*[ROOT/'build/local/user/xcom1'/x for x in ('Post-March_again.sav','I forgot to save.sav','And into may.sav')]]
 inputs=[]
 for path in paths:
  sha=e.m.file_digest(path)
  if path.suffix=='.json':receipt=json.loads(path.read_text())
  else:
   s=list(yaml.safe_load_all(path.read_text()))[-1];receipt=[json.loads(x) for x in s['alienCommand']['audit'] if json.loads(x).get('kind')=='portfolio'][-1]
  e.m.portfolio_input(receipt['input']);inputs.append((path,sha,receipt))
 a.out.mkdir(parents=True,exist_ok=True)
 agent,identity=e.m.load_agent(a.checkpoint,'cpu',e.m.V4_SHA256)
 summaries=[]
 for path,sha,receipt in inputs:
  data=receipt['input'];out=a.out/receipt['gameTime'][:7];out.mkdir(exist_ok=True)
  choose=lambda s,c,i:e.m.checked_choice(agent,s,c,i)
  started=time.perf_counter();baseline=e.m.plan_concrete_portfolio(data,choose);validate(baseline['operations'],data)
  baseline['latencyMs']=round((time.perf_counter()-started)*1000,2)
  (out/'before.json').write_text(json.dumps(baseline,indent=2))
  roster=candidates(data,baseline['operations']);(out/'candidates.json').write_text(json.dumps(roster,indent=2))
  orders=[list(range(len(roster))),list(reversed(range(len(roster)))),list(range(1,len(roster)))+[0]]
  results=[]
  for index,order in enumerate(orders):
   started=time.perf_counter()
   try:result=choose_whole(data,roster,choose,order)
   except ValueError as error:result={'status':'REJECTED','error':str(error)}
   result['latencyMs']=round((time.perf_counter()-started)*1000,2);results.append(result)
  (out/'after.json').write_text(json.dumps(results,indent=2))
  rng=random.Random(42);random_control=roster[rng.randrange(len(roster))]
  manifest={'source':str(path),'sourceSha256':sha,'inputSha256':e.m.digest(data),'sourceUnchanged':e.m.file_digest(path)==sha,'decision':receipt['gameTime'],'completedMonth':data['sitrep']['period'],'model':identity,'livePolicyChanged':False,'missionsExecuted':False,'randomCandidateControl':random_control,'candidateGeneration':'Four fixed motifs plus current sequential output and defer; exposure-ranked targets; no LLM transcripts used.'}
  assert manifest['sourceUnchanged'];(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
  summary={'decision':receipt['gameTime'],'before':baseline['operations'],'beforeRemaining':baseline['remainingProposed'],'after':[{'source':r.get('source'),'operations':r.get('operations'),'remaining':r.get('remaining'),'error':r.get('error')} for r in results]}
  summaries.append(summary);print(json.dumps(summary),flush=True)
 (a.out/'summary.json').write_text(json.dumps(summaries,indent=2))

if __name__=='__main__':main()
