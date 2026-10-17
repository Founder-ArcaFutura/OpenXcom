"""Monthly paired outcome-information test; sequential selection, no live changes."""
import argparse,copy,importlib.util,json,time
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('experiment',ROOT/'scripts/test-campaign-plans.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)

def geographic_filter(data):
 data=copy.deepcopy(data)
 regions={r['type']:r for r in yaml.safe_load((ROOT/'bin/standard/xcom1/regions.rul').read_text())['regions']}
 countries=yaml.safe_load((ROOT/'bin/standard/xcom1/countries.rul').read_text())['countries']
 def possible(region):
  rule=regions[region];rule=regions[rule.get('missionRegion',region)]
  for c in countries:
   lon,lat=c['labelLon'],c['labelLat']
   for left,right,bottom,top in rule.get('areas',[]):
    in_lon=left<=lon<right if left<=right else lon>=left or lon<right
    in_lat=bottom<lat<=top if lat>0 else bottom<=lat<top
    if in_lon and in_lat:return True
  return False
 old=data['knowledge']['candidates']
 removed=[c for c in old if c['mission']=='STR_ALIEN_INFILTRATION' and not possible(c['region'])]
 data['knowledge']['candidates']=[c for c in old if c not in removed]
 return data,removed

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 paths=[ROOT/'build/local/campaign-january-input.json',*[ROOT/'build/local/user/xcom1'/n for n in ('Post-March_again.sav','I forgot to save.sav','And into may.sav')]]
 inputs=[]
 for path in paths:
  sha=e.m.file_digest(path)
  if path.suffix=='.json':r=json.loads(path.read_text())
  else:
   s=list(yaml.safe_load_all(path.read_text()))[-1];r=[json.loads(x) for x in s['alienCommand']['audit'] if json.loads(x).get('kind')=='portfolio'][-1]
  data,removed=geographic_filter(r['input']);e.m.portfolio_input(data);inputs.append((path,sha,r,data,removed))
 agent,identity=e.m.load_agent(a.checkpoint,'cpu',e.m.V4_SHA256);summary=[]
 for path,sha,r,data,removed in inputs:
  out=a.out/r['gameTime'][:7];out.mkdir(exist_ok=True);(out/'input.json').write_text(json.dumps(data,indent=2))
  results=[]
  for contract,reverse in ((False,False),(True,False),(False,True),(True,True)):
   def choose(state,criteria,instructions):
    if reverse and 'SAVE' in criteria:criteria=dict(reversed(list(criteria.items())))
    return e.m.checked_choice(agent,state,criteria,instructions)
   start=time.perf_counter()
   try:result=e.plan(data,choose,False,True,False,contract)
   except ValueError as error:result={'status':'REJECTED','error':str(error)}
   result.update(contract=contract,planOptionOrder='reversed' if reverse else 'canonical',latencyMs=round((time.perf_counter()-start)*1000,2))
   name=('contract' if contract else 'baseline')+('-reversed' if reverse else '')
   (out/(name+'.json')).write_text(json.dumps(result,indent=2))
   results.append({k:result.get(k) for k in ('contract','planOptionOrder','operations','remainingProposed','error','latencyMs')})
   print(json.dumps({'decision':r['gameTime'],**results[-1]}),flush=True)
  assert e.m.file_digest(path)==sha,'Source changed'
  manifest={'source':str(path),'sourceSha256':sha,'sourceInputSha256':e.m.digest(r['input']),'pairedInputSha256':e.m.digest(data),'removedGeographicallyImpossibleInfiltrations':removed,'model':identity,'sourceUnchanged':True,'livePolicyChanged':False,'missionsExecuted':False,'newAPICalls':0,'onlyTreatment':'Conditional outcome fields added to PLAN state; no portfolio ranking, objectives summary or long pros/cons. Plan options reversed as a separate paired order check; target order unchanged.'}
  (out/'manifest.json').write_text(json.dumps(manifest,indent=2));summary.append({'decision':r['gameTime'],'results':results})
 (a.out/'summary.json').write_text(json.dumps(summary,indent=2))

if __name__=='__main__':main()
