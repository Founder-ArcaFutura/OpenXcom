"""Offline reward-description sensitivity probe; never changes native campaign mechanics."""
import argparse,copy,importlib.util,json,time
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
o=module('outcome_probe',ROOT/'scripts/test-outcome-contract.py');e=o.e
w=module('whole_probe',ROOT/'scripts/test-whole-portfolios.py')
ARMS=('baseline','explicit_current','hypothetical')

def reward_text(mission,budget,hypothetical=False):
 short=mission.removeprefix('STR_ALIEN_')
 research_gain=int(budget['intelligence']<2) if hypothetical else 1
 descriptions={
  'RESEARCH':f'flight: +{0 if hypothetical else 1} resources, +{research_gain} intelligence'+('; intelligence cap 2' if hypothetical else ''),
  'PROBE_MISSION':f'flight: +{0 if hypothetical else 1} resources, +{research_gain} intelligence'+('; intelligence cap 2' if hypothetical else ''),
  'HARVEST':f'productive activity: +{3 if hypothetical else 2} resources, +1 logistics; logistics 2 unlocks bases',
  'ABDUCTION':f'productive activity: +{3 if hypothetical else 2} resources, +1 adaptation',
  'TERROR':('successful terror outcome: +6 resources, +2 local influence; defeat pays zero' if hypothetical else 'delivered objective: native political pressure; no resource bonus'),
  'SURFACE_ATTACK':('successful attack outcome: +6 resources, +2 local influence; defeat pays zero' if hypothetical else 'delivered objective: native political pressure; no resource bonus'),
  'RETALIATION':'possible base discovery; no resources; separate assault unavailable',
  'INFILTRATION':'possible country pact and base; base earns 1-2 resources/month',
  'BASE':'surviving base: 1-2 resources/month, gradual progress and local influence'}
 return descriptions[short]

def transform(state,criteria,data,arm):
 if arm=='baseline' or 'SAVE' not in criteria:return state,dict(criteria)
 value=json.loads(state)
 value['payout_limits']='Conditional gains; failure pays zero. Resource bonuses next month/capped. Odds unknown; influence is not an automatic pact.'
 result={}
 for key,label in criteria.items():
  if key=='SAVE':result[key]=label;continue
  # Same action IDs/order as shared planner; only the descriptions change.
  mission=next(m for m,p in e.PLANS.items() if label==p[1]+'; cost '+str(e.m.PORTFOLIO_COSTS[m]))
  result[key]=mission.removeprefix('STR_ALIEN_').replace('_',' ')+': '+reward_text(mission,data['budget'],arm=='hypothetical')+'; cost '+str(e.m.PORTFOLIO_COSTS[mission])
 return e.m.canonical(value),result

def load_inputs():
 paths=[ROOT/'build/local/campaign-january-input.json',*[ROOT/'build/local/user/xcom1'/n for n in ('Post-March_again.sav','I forgot to save.sav','And into may.sav','Post-june.sav')]]
 inputs=[]
 for path in paths:
  sha=e.m.file_digest(path)
  if path.suffix=='.json':receipt=json.loads(path.read_text())
  else:
   save=list(yaml.safe_load_all(path.read_text()))[-1]
   receipt=[json.loads(x) for x in save['alienCommand']['audit'] if json.loads(x).get('kind')=='portfolio'][-1]
  data,removed=o.geographic_filter(receipt['input']);e.m.portfolio_input(data)
  inputs.append((path,sha,receipt,data,removed))
 return inputs

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 a.out.mkdir(parents=True,exist_ok=True);inputs=load_inputs()
 agent,identity=e.m.load_agent(a.checkpoint,'cpu',e.m.V4_SHA256);summary=[]
 for path,sha,receipt,data,removed in inputs:
  out=a.out/receipt['gameTime'][:7];out.mkdir(exist_ok=True);(out/'input.json').write_text(json.dumps(data,indent=2))
  for reverse in (False,True):
   for arm in ARMS:
    def choose(state,criteria,instructions):
     state,criteria=transform(state,criteria,data,arm)
     if reverse and 'SAVE' in criteria:criteria=dict(reversed(list(criteria.items())))
     return e.m.checked_choice(agent,state,criteria,instructions)
    start=time.perf_counter()
    try:
     result=e.plan(copy.deepcopy(data),choose,False,True)
     w.validate(result['operations'],data)
     assert result['remainingProposed']==data['budget']['remaining']-sum(e.m.PORTFOLIO_COSTS[x['mission']] for x in result['operations'])
    except ValueError as error:result={'status':'REJECTED','error':str(error)}
    result.update(arm=arm,planOptionOrder='reversed' if reverse else 'canonical',latencyMs=round((time.perf_counter()-start)*1000,2))
    # Shared planner pro/con metadata describes live rules, not hypothetical payouts.
    for plan in result.get('plans',[]):
     plan.pop('pro',None);plan.pop('con',None)
     plan['experimentalRewardDescription']=reward_text(plan['mission'],data['budget'],arm=='hypothetical')
    (out/(arm+('-reversed' if reverse else '')+'.json')).write_text(json.dumps(result,indent=2))
    row={'decision':receipt['gameTime'],**{k:result.get(k) for k in ('arm','planOptionOrder','operations','remainingProposed','status','error','latencyMs')}}
    summary.append(row);print(json.dumps(row),flush=True)
  assert e.m.file_digest(path)==sha,'Source changed'
  (out/'manifest.json').write_text(json.dumps({'source':str(path),'sourceSha256':sha,'sourceInputSha256':e.m.digest(receipt['input']),'pairedInputSha256':e.m.digest(data),'removedInvalidGeography':removed,'model':identity,'scripts':{n:e.m.file_digest(ROOT/n) for n in ('scripts/test-conquest-incentives.py','scripts/campaign_plans.py','scripts/alien-command-model.py')},'sourceUnchanged':True,'livePolicyChanged':False,'missionsExecuted':False,'APICalls':0,'counterfactualCampaignSimulated':False},indent=2))
 (a.out/'summary.json').write_text(json.dumps(summary,indent=2))
if __name__=='__main__':main()
