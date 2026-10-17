"""Test named state and short capability paths separately from rewards/portfolio ranking."""
import argparse,importlib.util,json,time
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('outcome_test',ROOT/'scripts/test-outcome-contract.py')
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
e=o.e

def paths(budget):
 def missing(requirements):return {k:v-budget[k] for k,v in requirements.items() if budget[k]<v}
 base=missing({'epochMonth':1,'logistics':2})
 control=missing({'epochMonth':2,'adaptation':2,'intelligence':1})
 return {'BASE':{'missing':base,'prepare':(['HARVEST'] if 'logistics' in base else [])},
  'INFILTRATION':{'missing':control,'prepare':(['ABDUCTION'] if 'adaptation' in control else [])+(['RESEARCH'] if 'intelligence' in control else [])},
  'BASE_ASSAULT':'UNAVAILABLE; search can discover only'}

def transform(state,data,mode):
 value=json.loads(state)
 if mode!='baseline' and 'lessons' in value:
  value['lessons']['progress']={k:data['budget'][k] for k in ('intelligence','logistics','adaptation')}
  if mode=='named_paths':value['capability_paths']=paths(data['budget'])
 return e.m.canonical(value)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 sources=[ROOT/'build/local/campaign-january-input.json',*[ROOT/'build/local/user/xcom1'/n for n in ('Post-March_again.sav','I forgot to save.sav','And into may.sav')]]
 inputs=[]
 for path in sources:
  sha=e.m.file_digest(path)
  if path.suffix=='.json':r=json.loads(path.read_text())
  else:
   s=list(yaml.safe_load_all(path.read_text()))[-1];r=[json.loads(x) for x in s['alienCommand']['audit'] if json.loads(x).get('kind')=='portfolio'][-1]
  data,removed=o.geographic_filter(r['input']);e.m.portfolio_input(data);inputs.append((path,sha,r,data,removed))
 agent,identity=e.m.load_agent(a.checkpoint,'cpu',e.m.V4_SHA256);summary=[]
 for path,sha,r,data,removed in inputs:
  out=a.out/r['gameTime'][:7];out.mkdir(exist_ok=True);(out/'input.json').write_text(json.dumps(data,indent=2));results=[]
  for reverse in (False,True):
   for mode in ('baseline','named','named_paths'):
    def choose(state,criteria,instructions):
     if reverse and 'SAVE' in criteria:criteria=dict(reversed(list(criteria.items())))
     return e.m.checked_choice(agent,transform(state,data,mode),criteria,instructions)
    start=time.perf_counter()
    try:result=e.plan(data,choose,False,True)
    except ValueError as error:result={'status':'REJECTED','error':str(error)}
    result.update(mode=mode,planOptionOrder='reversed' if reverse else 'canonical',latencyMs=round((time.perf_counter()-start)*1000,2))
    name=mode+('-reversed' if reverse else '');(out/(name+'.json')).write_text(json.dumps(result,indent=2))
    compact={k:result.get(k) for k in ('mode','planOptionOrder','operations','remainingProposed','error','latencyMs')};results.append(compact);print(json.dumps({'decision':r['gameTime'],**compact}),flush=True)
  assert e.m.file_digest(path)==sha,'Source changed'
  (out/'manifest.json').write_text(json.dumps({'source':str(path),'sourceSha256':sha,'pairedInputSha256':e.m.digest(data),'sourceInputSha256':e.m.digest(r['input']),'removed':removed,'model':identity,'sourceUnchanged':True,'livePolicyChanged':False,'missionsExecuted':False,'newAPICalls':0,'interventions':'baseline; named progression only; named progression plus compact missing-prerequisite/preparatory-mission paths. Same sequential choices, no reward contract, no portfolio ranking. PLAN order is a separate paired check.'},indent=2))
  summary.append({'decision':r['gameTime'],'results':results})
 (a.out/'summary.json').write_text(json.dumps(summary,indent=2))

if __name__=='__main__':main()
