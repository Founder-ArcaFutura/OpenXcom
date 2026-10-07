"""Read-only specialist/commander comparison using an exact native input receipt."""
import argparse
import importlib.util
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('commander',ROOT/'scripts/alien-command-model.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

ROLES={
 'RESISTANCE':({'STR_ALIEN_RETALIATION'},'Locate XCOM operating areas. Reports are stronger than assignment losses; radar reach is not a base coordinate.'),
 'POLITICAL':({'STR_ALIEN_TERROR','STR_ALIEN_SURFACE_ATTACK','STR_ALIEN_INFILTRATION'},'Find opportunities for political pressure. Little contact may mean little observation, not weak resistance. Political vulnerability is unknown.'),
 'ECONOMIC':({'STR_ALIEN_HARVEST','STR_ALIEN_ABDUCTION','STR_ALIEN_BASE','STR_ALIEN_SUPPLY'},'Find productive deployment opportunities. Verified activities support gains; absent losses do not establish safety.')}

def advise(data,choose):
 budget,menu,beliefs,sitrep=m.portfolio_input(data)
 reports={b['region']:b['independentSources'] for b in beliefs}
 losses={g['region']:g['count'] for g in sitrep['lossAssignments']}
 assessments={};receipts=[]
 for role,(missions,purpose) in ROLES.items():
  regions=sorted({c['region'] for c in menu if c['mission'] in missions and m.PORTFOLIO_COSTS[c['mission']]<=budget['remaining']})
  if role=='RESISTANCE':
   regions,basis=m.search_region_pool(regions,{r:{'reporters':n} for r,n in reports.items()},sitrep)
   if basis=='NO_MATCHING_EVIDENCE_EXPLORATION':regions=[]
  else:
   # Current admitted DTO has no regional exposure denominator, political
   # outcome or productive outcome attribution. Do not invent safe targets.
   regions=[];basis='MISSING_REGIONAL_OUTCOME_AND_EXPOSURE_EVIDENCE'
  if not regions:
   receipts.append({'advisor':role,'source':'EVIDENCE_GATE','status':'UNKNOWN','basis':basis})
  recommendations=[]
  for rank in range(2):
   if not regions:break
   rows=[[r.removeprefix('STR_'),reports.get(r,0),losses.get(r,0)] for r in regions]
   state=m.canonical({'advisor':role,'purpose':purpose,'period':sitrep['period'],'regions_reports_assignment_losses':rows,
    'coverage':'Partial. Zero reports is not observed safety. Loss location/cause and political vulnerability unknown.',
    'pending':[[o['mission'].removeprefix('STR_ALIEN_'),o['region'].removeprefix('STR_')] for o in sitrep['pendingOperations'] if o['mission'] in missions]})
   criteria={'R'+str(i):r.removeprefix('STR_').replace('_',' ') for i,r in enumerate(regions)}
   criteria['UNKNOWN']='Insufficient evidence to recommend a region'
   label,receipt=choose(state,criteria,'Recommend the best remaining region for your advisory role, or acknowledge insufficient evidence.')
   receipts.append({**receipt,'advisor':role,'rank':rank+1,'basis':basis})
   if label=='UNKNOWN':break
   if label not in criteria:raise ValueError('Invalid advisor region')
   region=regions.pop(int(label[1:]))
   recommendations.append({'region':region,'reports':reports.get(region,0),'assignmentLosses':losses.get(region,0),
    'certainty':'HYPOTHESIS','politicalVulnerability':'UNKNOWN','supportIds':sorted({i for b in beliefs if b['region']==region for i in b['evidenceIds']}|{i for g in sitrep['lossAssignments'] if g['region']==region for i in g['evidenceIds']})})
  assessments[role]=recommendations
 return assessments,receipts

def advisory_portfolio(data,choose,with_advice=True):
 assessments,receipts=advise(data,choose) if with_advice else ({},[])
 summaries={k:[[r['region'].removeprefix('STR_'),r['reports'],r['assignmentLosses'],'HYPOTHESIS'] for r in rows] or ['UNKNOWN'] for k,rows in assessments.items()}
 def command(state,criteria,instructions):
  original=json.loads(state)
  # Commander sees the task/budget contract, small advisory conclusions and
  # pending counts. Detailed regional evidence stays in specialist receipts.
  keys=('goal','budget','carry_limit','expires_if_idle','progress','strategy','remaining','next_allowance','pending_bonus','next_bonus_cap','selected','operations','deferral','objective','search_basis')
  compact={k:original[k] for k in keys if k in original}
  if with_advice:compact['advice']=summaries
  compact['limits']='Advisory hypotheses; no confirmed base or political vulnerability. No reports does not mean safety.'
  if 'sitrep' in original:
   compact['last_month']={k:original['sitrep'][k] for k in ('previous_strategy','assets','completed_activities','pending')}
  if 'recent_results' in original:compact['recent_results']=original['recent_results']
  return choose(m.canonical(compact),criteria,instructions)
 result=m.plan_portfolio(data,command)
 return {**result,'advisors':assessments,'advisorDecisions':receipts}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--receipt',type=Path,required=True);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();before=m.file_digest(a.receipt)
 receipt=json.loads(a.receipt.read_text(encoding='utf-8-sig'));data=receipt.get('input',receipt)
 agent,identity=m.load_agent(a.checkpoint,'cpu',m.V4_SHA256)
 a.out.mkdir(parents=True,exist_ok=True)
 for name,planner in [('single_commander',m.plan_portfolio),('compact_commander',lambda data,choose:advisory_portfolio(data,choose,False)),('specialist_advisors',advisory_portfolio)]:
  start=time.perf_counter()
  result=planner(data,lambda state,criteria,instructions:m.checked_choice(agent,state,criteria,instructions))
  result.update(variant=name,latencyMs=round((time.perf_counter()-start)*1000,2),**identity)
  (a.out/(name+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
  print(json.dumps({k:result.get(k) for k in ('variant','strategy','operations','remainingProposed','latencyMs','advisors')}),flush=True)
 if before!=m.file_digest(a.receipt):raise RuntimeError('Source receipt changed')
 (a.out/'manifest.json').write_text(json.dumps({'sourceReceipt':str(a.receipt.resolve()),'sourceSha256':before,'inputSha256':m.digest(data),'originalUnchanged':True,'executedMissions':False,'livePolicyChanged':False,'sharedCheckpoint':True,'experimentVersion':'specialist-advisors-v2','targetingConstraint':'search-evidence-v5 retained'},indent=2),encoding='utf-8')

if __name__=='__main__':main()
