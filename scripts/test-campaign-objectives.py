"""Frozen-input objective-summary comparison; no live service/campaign mutation."""
import argparse,importlib.util,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('experiment',ROOT/'scripts/test-campaign-plans.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--save',type=Path,action='append',required=True);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();import yaml
 inputs=[]
 for path in a.save:
  sha=e.m.file_digest(path);s=list(yaml.safe_load_all(path.read_text(encoding='utf-8')))[-1]
  r=[json.loads(x) for x in s['alienCommand']['audit'] if json.loads(x).get('kind')=='portfolio'][-1]
  inputs.append((path,sha,r))
 agent,identity=e.m.load_agent(a.checkpoint,'cpu',e.m.V4_SHA256)
 for path,sha,r in inputs:
  out=a.out/path.stem;out.mkdir(parents=True,exist_ok=True)
  for variant,enabled in [('baseline',False),('objectives',True)]:
   start=time.perf_counter()
   try:result=e.plan(r['input'],lambda s,c,i:e.m.checked_choice(agent,s,c,i),False,True,enabled)
   except ValueError as error:result={'status':'REJECTED','error':str(error)}
   result.update(variant=variant,latencyMs=round((time.perf_counter()-start)*1000,2),**identity)
   (out/(variant+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
   print(json.dumps({'decision':r['gameTime'],**{k:result.get(k) for k in ('variant','operations','remainingProposed','error','latencyMs')}}),flush=True)
  assert e.m.file_digest(path)==sha,'Source save changed'
  (out/'manifest.json').write_text(json.dumps({'sourceSave':str(path.resolve()),'sourceSha256':sha,'inputSha256':e.m.digest(r['input']),'decision':r['gameTime'],'sourceUnchanged':True,'executedMissions':False,'livePolicyChanged':False},indent=2))

if __name__=='__main__':main()
