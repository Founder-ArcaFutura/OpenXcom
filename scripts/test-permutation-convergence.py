"""Six disjoint balanced families on two fixed ambiguous first PLAN decisions."""
import argparse,copy,itertools,json,random,time,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('permutation_probe',ROOT/'scripts/test-permutation-commander.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
NAMES=('A','B','C','D','E','F')
POOLS=('AB','CD','EF','ABCD','CDEF','ABCDEF')
def family_orders(criteria):
 keys=sorted(criteria);result={name:p.families(criteria,name) for name in ('A','B')};used={tuple(x) for name in result for x in result[name]}
 if len(keys)<4:raise ValueError('Six disjoint cyclic families require at least four choices')
 for name in NAMES[2:]:
  rng=random.Random(int(p.e.m.digest(['convergence-family-4119',name,keys])[:16],16))
  for attempt in range(10000):
   base=list(keys);rng.shuffle(base)
   if tuple(base) not in used:break
  else:raise ValueError('Cannot find disjoint family')
  orders=p.rotations(base);result[name]=[dict((k,criteria[k]) for k in order) for order in orders];used.update(tuple(x) for x in orders)
 return result

def seed_previous(cache):
 p.seed_cache(cache)
 for manifest in (ROOT/'build/local/permutation-commander-v1').glob('1999-*/manifest.json'):
  meta=json.loads(manifest.read_text());assert meta['model']['checkpointSha256']==p.e.m.V4_SHA256
  for name in ('scripts/campaign_plans.py','scripts/alien-command-model.py'):assert p.e.m.file_digest(ROOT/name)==meta['scripts'][name]
  for file in manifest.parent.glob('*.json'):
   if file.stem in ('input','manifest'):continue
   for d in json.loads(file.read_text()).get('decisions',[]):
    for r in d.get('permutations',[d]):
     q=r['question']
     if 'instructions' not in q:continue
     key=p.f.packet_key(r['state'],q['criteria'],q['instructions'])
     if key in cache:assert cache[key]['receipt']['answer']==r['answer']
     cache[key]={'receipt':r,'origin':str(file)}

def first_packet(data):
 class Captured(Exception):pass
 packet={}
 def choose(state,criteria,instructions):
  state,criteria=p.f.transform(state,criteria,data,p.f.configurations()[0]);packet.update(state=state,criteria=criteria,instructions=instructions);raise Captured()
 try:p.e.plan(copy.deepcopy(data),choose,False,True)
 except Captured:pass
 assert packet and 'SAVE' in packet['criteria'];return packet

def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--checkpoint',type=Path,required=True);a.add_argument('--out',type=Path,required=True);args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 inputs=[row for row in p.f.n.load_inputs() if row[2]['gameTime'][:7] in ('1999-02','1999-04')];assert len(inputs)==2
 cache={};seed_previous(cache);agent,identity=p.e.m.load_agent(args.checkpoint,'cpu',p.e.m.V4_SHA256);summary=[];new=hits=0
 for source,sha,original,data,removed in inputs:
  month=original['gameTime'][:7];out=args.out/month;out.mkdir(exist_ok=True);packet=first_packet(data);(out/'input.json').write_text(json.dumps(data,indent=2));(out/'packet.json').write_text(json.dumps(packet,indent=2))
  orders=family_orders(packet['criteria']);all_receipts={}
  for family in NAMES:
   receipts=[]
   for criteria in orders[family]:
    key=p.f.packet_key(packet['state'],criteria,packet['instructions'])
    if key in cache:
     entry=cache[key];r=copy.deepcopy(entry['receipt']);r.update(inferenceSource='EXACT_ORDERED_PACKET_CACHE',cacheOrigin=entry['origin']);hits+=1
    else:
     _,r=p.e.m.checked_choice(agent,packet['state'],criteria,packet['instructions']);r['inferenceSource']='NEW_LOCAL_INFERENCE';new+=1
     cache[key]={'receipt':copy.deepcopy(r),'origin':str(out/(family+'.json'))}
    receipts.append(r)
   all_receipts[family]=receipts;label,means,votes,margin=p.aggregate_answers(receipts,packet['criteria'])
   result={'family':family,'choice':label,'description':packet['criteria'][label],'meanScores':means,'votes':votes,'margin':margin,'orders':[list(x) for x in orders[family]],'components':receipts}
   (out/(family+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps({'month':month,'family':family,'choice':label,'margin':margin,'newModelInferences':new,'cacheReuses':hits}),flush=True)
   (args.out/'progress.json').write_text(json.dumps({'completedFamilies':sum(len(x['families']) for x in summary)+len(all_receipts),'plannedFamilies':12,'newModelInferences':new,'cacheReuses':hits},indent=2))
  pools={}
  for names in POOLS:
   receipts=[r for name in names for r in all_receipts[name]];label,means,votes,margin=p.aggregate_answers(receipts,packet['criteria']);pools[names]={'choice':label,'description':packet['criteria'][label],'meanScores':means,'votes':votes,'margin':margin,'componentCount':len(receipts)}
  (out/'pools.json').write_text(json.dumps(pools,indent=2));assert p.e.m.file_digest(source)==sha
  manifest={'source':str(source),'sourceSha256':sha,'pairedInputSha256':p.e.m.digest(data),'model':identity,'liveChanged':False,'APICalls':0,'firstPlanOnly':True,'scripts':{name:p.e.m.file_digest(ROOT/name) for name in ('scripts/test-permutation-convergence.py','scripts/test-permutation-commander.py','scripts/campaign_plans.py','scripts/alien-command-model.py')}}
  (out/'manifest.json').write_text(json.dumps(manifest,indent=2));summary.append({'month':month,'families':{name:json.loads((out/(name+'.json')).read_text()) for name in NAMES},'pools':pools})
 (args.out/'summary.json').write_text(json.dumps({'states':summary,'newModelInferences':new,'cacheReuses':hits,'model':identity},indent=2))
if __name__=='__main__':main()
