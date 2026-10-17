"""Matched synthetic adaptation diagnostics, grounded in native-exported legal menus."""
import argparse,copy,json,importlib.util,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('permutation_probe',ROOT/'scripts/test-permutation-commander.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class Captured(Exception):pass

def native_inputs():
 root=ROOT/'build/local/adaptation-native-v1'
 a=json.loads((root/'logistics-1/xcom1/strategy-input.json').read_text());b=json.loads((root/'logistics-2/xcom1/strategy-input.json').read_text())
 for data in (a,b):p.e.m.portfolio_input(data)
 da=copy.deepcopy(a);db=copy.deepcopy(b);da['budget']['logistics']=db['budget']['logistics'];da['knowledge']['candidates']=db['knowledge']['candidates']
 assert da==db,'Native capability pair changes additional facts'
 assert a['budget']['logistics']==1 and b['budget']['logistics']==2
 old=a['knowledge']['candidates'];new=b['knowledge']['candidates'];assert all(c in new for c in old)
 assert all(c['mission']=='STR_ALIEN_BASE' for c in new if c not in old)
 return a,b

def loss_variant(data,region,count,role='UNKNOWN'):
 data=copy.deepcopy(data);s=data['sitrep'];s['assets']['unavailable']=count
 s['lossAssignments']=[{'region':region,'count':count,'evidenceIds':list(range(900001,900001+count))}]
 review=s['operationalReview'];review['loss_roles']={r:(count if r==role else 0) for r in review['loss_roles']};review['roleSupport']=[]
 review['rolling_results'][-1]=[s['period'],count,sum(g['count'] for g in s['verifiedActivities'])]
 data['knowledge']['beliefs']=[];data['knowledge']['evidence']=[];s['contacts']=[]
 p.e.m.portfolio_input(data);return data

def cases():
 before,after=native_inputs();result=[]
 for region in ('STR_AUSTRALASIA','STR_NORTH_AMERICA'):
  data=loss_variant(before,region,8)
  assert any(c=={'mission':'STR_ALIEN_HARVEST','region':region} for c in data['knowledge']['candidates'])
  result.append({'name':'risk_'+region.removeprefix('STR_'),'pair':'risk','stage':'TARGET_HARVEST','encoding':'compact','data':data,'intervention':{'assignedLossRegion':region,'ownAssignedLosses':8,'contactBeliefs':0}})
 for encoding in ('compact','named_capability'):
  for level,data in ((1,before),(2,after)):
   result.append({'name':f'gate_{encoding}_{level}','pair':'capability','stage':'PLAN','encoding':encoding,'data':copy.deepcopy(data),'intervention':{'logistics':level,'baseCandidates':sum(c['mission']=='STR_ALIEN_BASE' for c in data['knowledge']['candidates']),'cashHeldFixed':True}})
 for role in ('PREPARATION','OBJECTIVE_CARRIER'):
  data=loss_variant(before,'STR_NORTH_AMERICA',1,role);s=data['sitrep'];review=s['operationalReview'];pending=role=='PREPARATION'
  review['roleSupport']=[{'lossReceiptId':900101,'role':role,'craftType':'STR_MEDIUM_SCOUT' if pending else 'STR_TERROR_SHIP','source':'EXPLICIT_NATIVE_TELEMETRY'}]
  s['previousPortfolio']=[{'mission':'STR_ALIEN_TERROR','region':'STR_NORTH_AMERICA'}]
  s['pendingOperations'].append({'missionId':99001,'mission':'STR_ALIEN_TERROR','region':'STR_NORTH_AMERICA'});s['pendingTotal']+=1
  review['pendingProgress'].append({'missionId':99001,'nextWave':1 if pending else 4,'totalWaves':4,'objectiveWavePending':pending})
  review['terror_objective_waves_pending']=int(pending)
  # A parent can remain active while other craft survive, even after its last objective wave.
  data['knowledge']['candidates']=[c for c in data['knowledge']['candidates'] if c!={'mission':'STR_ALIEN_TERROR','region':'STR_NORTH_AMERICA'}]
  p.e.m.portfolio_input(data)
  result.append({'name':'role_'+role,'pair':'operational_role','stage':'PLAN','encoding':'compact','data':data,'intervention':{'lostRole':role,'furtherObjectiveWavePending':pending,'wholeMissionOutcome':'UNKNOWN'}})
 return result

def capture(case):
 packet={};data=case['data']
 def choose(state,criteria,instructions):
  if case['stage']=='TARGET_HARVEST' and 'SAVE' in criteria:
   key=next(k for k,v in criteria.items() if v==p.e.PLANS['STR_ALIEN_HARVEST'][1]+'; cost 3')
   return key,{'source':'FORCED_OBJECTIVE_FOR_TARGET_DIAGNOSTIC'}
  state,criteria=p.f.transform(state,criteria,data,p.f.configurations()[0])
  if 'SAVE' in criteria:
   short={
    'ABDUCTION':'ABDUCTION: productive +2 cash, +1 adaptation; cost 3',
    'HARVEST':'HARVEST: productive +2 cash, +1 logistics; bases need logistics 2; cost 3',
    'RESEARCH':'RESEARCH: productive +1 cash, +1 intelligence; cost 2',
    'BASE':'BASE: surviving +1-2 cash/month, progress, local influence; cost 6',
    'INFILTRATION':'INFILTRATION: possible pact and base (+1-2 cash/month); cost 6',
    'TERROR':'TERROR: delivered objective pressures nations; no cash; cost 4',
    'RETALIATION':'RETALIATION: possible base discovery; no cash; assault unavailable; cost 2'}
   for key,label in list(criteria.items()):
    kind=label.split(':')[0]
    if kind in short:criteria[key]=short[kind]
  if case['encoding']=='named_capability':
   value=json.loads(state);b=data['budget'];value['capability']={'intelligence':b['intelligence'],'logistics':b['logistics'],'adaptation':b['adaptation'],'base_missing_logistics':max(0,2-b['logistics']),'base_available':b['logistics']>=2};state=p.e.m.canonical(value)
   for key,label in list(criteria.items()):
    if label.startswith('HARVEST:'):criteria[key]=label.replace('bases need logistics 2','bases already unlocked' if b['logistics']>=2 else 'one logistics short of bases')
  packet.update(state=state,criteria=criteria,instructions=instructions);raise Captured()
 try:p.e.plan(copy.deepcopy(data),choose,False,True)
 except Captured:pass
 assert packet;return packet

def seed(cache):
 p.seed_cache(cache)
 for file in (ROOT/'build/local/adaptive-responses-v1').glob('*/*.json'):
  row=json.loads(file.read_text())
  for r in row.get('components',[]):
   q=r['question'];cache[p.f.packet_key(r['state'],q['criteria'],q['instructions'])]={'receipt':r,'origin':str(file)}
 for manifest in (ROOT/'build/local/permutation-commander-v1').glob('1999-*/manifest.json'):
  meta=json.loads(manifest.read_text());assert meta['model']['checkpointSha256']==p.e.m.V4_SHA256
  for name in ('scripts/campaign_plans.py','scripts/alien-command-model.py'):assert meta['scripts'][name]==p.e.m.file_digest(ROOT/name)
  for file in manifest.parent.glob('*.json'):
   if file.stem in ('manifest','input'):continue
   for d in json.loads(file.read_text()).get('decisions',[]):
    for r in d.get('permutations',[d]):
     q=r['question']
     if 'instructions' in q:cache[p.f.packet_key(r['state'],q['criteria'],q['instructions'])]={'receipt':r,'origin':str(file)}

def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--checkpoint',type=Path,required=True);a.add_argument('--out',type=Path,required=True);args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 fixtures=cases();cache={};seed(cache);agent,identity=p.e.m.load_agent(args.checkpoint,'cpu',p.e.m.V4_SHA256);rows=[];new=hits=0
 for case in fixtures:
  data=case['data'];packet=capture(case);out=args.out/case['name'];out.mkdir(exist_ok=True);(out/'input.json').write_text(json.dumps(data,indent=2));(out/'packet.json').write_text(json.dumps(packet,indent=2))
  for family in ('A','B'):
   receipts=[];orders=p.families(packet['criteria'],family)
   for criteria in orders:
    key=p.f.packet_key(packet['state'],criteria,packet['instructions'])
    if key in cache:
     entry=cache[key];r=copy.deepcopy(entry['receipt']);r.update(inferenceSource='EXACT_ORDERED_PACKET_CACHE',cacheOrigin=entry['origin']);hits+=1
    else:
     _,r=p.e.m.checked_choice(agent,packet['state'],criteria,packet['instructions']);new+=1;r['inferenceSource']='NEW_LOCAL_INFERENCE';cache[key]={'receipt':copy.deepcopy(r),'origin':str(out/(family+'.json'))}
    receipts.append(r)
   label,means,votes,margin=p.aggregate_answers(receipts,packet['criteria']);row={'case':case['name'],'pair':case['pair'],'stage':case['stage'],'encoding':case['encoding'],'intervention':case['intervention'],'family':family,'choice':label,'description':packet['criteria'][label],'meanScores':means,'votes':votes,'margin':margin,'components':receipts,'orders':[list(x) for x in orders]}
   (out/(family+'.json')).write_text(json.dumps(row,indent=2));rows.append(row)
   (args.out/'progress.json').write_text(json.dumps({'completed':len(rows),'planned':16,'newModelInferences':new,'cacheReuses':hits},indent=2));print(json.dumps({k:row[k] for k in ('case','family','description','margin')}),flush=True)
 sources=[ROOT/'build/local/user/xcom1/Pre-Junes.sav',*[ROOT/'build/local/adaptation-native-v1'/f'logistics-{i}/xcom1/strategy-input.json' for i in (1,2)]]
 manifest={'model':identity,'sources':{str(path):p.e.m.file_digest(path) for path in sources},'scripts':{str(path):p.e.m.file_digest(ROOT/path) for path in ('scripts/test-adaptive-responses.py','scripts/test-permutation-commander.py','scripts/campaign_plans.py','scripts/alien-command-model.py')},'syntheticVariants':True,'verifiedDefeatTested':False,'fullPortfoliosGenerated':False,'liveChanged':False,'APICalls':0,'newModelInferences':new,'cacheReuses':hits}
 (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2));(args.out/'summary.json').write_text(json.dumps({'rows':rows,'manifest':manifest},indent=2))
if __name__=='__main__':main()
