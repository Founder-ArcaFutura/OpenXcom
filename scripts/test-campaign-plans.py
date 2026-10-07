"""Read-only test of concrete objectives, executable operations and campaign tradeoffs."""
import argparse
import importlib.util
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('model',ROOT/'scripts/alien-command-model.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

spec_plans=importlib.util.spec_from_file_location('campaign_plans',ROOT/'scripts/campaign_plans.py')
planner=importlib.util.module_from_spec(spec_plans);spec_plans.loader.exec_module(planner)
planner.m=m
PLANS=planner.PLANS
plan=planner.plan

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--receipt',type=Path,required=True,action='append');p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 agent,identity=m.load_agent(a.checkpoint,'cpu',m.V4_SHA256);a.out.mkdir(parents=True,exist_ok=True)
 for source in a.receipt:
  before=m.file_digest(source);data=json.loads(source.read_text(encoding='utf-8-sig'))['input']
  out=a.out/source.stem if len(a.receipt)>1 else a.out;out.mkdir(parents=True,exist_ok=True)
  for name,tradeoffs in [('concrete_plans',False),('plans_with_tradeoffs',True)]:
   start=time.perf_counter();result=plan(data,lambda s,c,i:m.checked_choice(agent,s,c,i),tradeoffs)
   result.update(variant=name,latencyMs=round((time.perf_counter()-start)*1000,2),**identity)
   (out/(name+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
   print(json.dumps({'period':data['sitrep']['period'],**{k:result[k] for k in ('variant','operations','remainingProposed','latencyMs')}}),flush=True)
  if before!=m.file_digest(source):raise RuntimeError('Source changed')
  (out/'manifest.json').write_text(json.dumps({'sourceReceipt':str(source.resolve()),'sourceSha256':before,'inputSha256':m.digest(data),'originalUnchanged':True,'executedMissions':False,'livePolicyChanged':False,'version':'concrete-campaign-plans-v1','planSource':'Deterministic native-capability templates; model chooses plans and targets.'},indent=2),encoding='utf-8')

if __name__=='__main__':main()
