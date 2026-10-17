"""Concrete native-capability plans; callers supply the validated model contract."""

m = None

PLANS={
 'STR_ALIEN_RETALIATION':('LOCATE_XCOM','Search for XCOM base','Discovery can enable a later devastating base assault.','Scouts may be destroyed before discovery; no income; assault currently unavailable.'),
 'STR_ALIEN_HARVEST':('BUILD_CAPACITY','Harvest to build capacity','Verified activity earns +2 pending income and +1 logistics.','Interception can prevent productive activity; unobserved regions are not proven safe.'),
 'STR_ALIEN_ABDUCTION':('BUILD_CAPACITY','Abduct to build capacity','Verified activity earns +2 pending income and +1 adaptation.','Interception can prevent gains; low reported exposure may reflect little observation.'),
 'STR_ALIEN_RESEARCH':('DEVELOP_INTELLIGENCE','Research to develop intelligence','Completed flight earns +1 pending income and +1 intelligence.','Cannot discover XCOM bases; craft can be intercepted.'),
 'STR_ALIEN_PROBE_MISSION':('DEVELOP_INTELLIGENCE','Probe to develop intelligence','Completed flight earns +1 pending income and +1 intelligence.','Cannot discover XCOM bases; craft can be intercepted.'),
 'STR_ALIEN_TERROR':('APPLY_PRESSURE','Terror to apply political pressure','Stock political pressure if the objective is delivered.','Craft/site exposed; no new income bonus; political vulnerability unknown.'),
 'STR_ALIEN_SURFACE_ATTACK':('APPLY_PRESSURE','Surface attack to apply pressure','Stock political pressure if the objective is delivered.','Craft/site exposed; no new income bonus; political vulnerability unknown.'),
 'STR_ALIEN_BASE':('BUILD_INFRASTRUCTURE','Build base: +1-2 income/month, progress in all tracks, local influence','Surviving base earns 1-2 resources/month, quarter-point in each progression track, and local influence.','Costs 6; benefits cease on destruction; supplies mature income.'),
 'STR_ALIEN_INFILTRATION':('SEEK_CONTROL','Infiltrate to seek national control','Can obtain national control under native rules.','Costs 6; recurring control income is not implemented.')}

def campaign_lessons(budget,beliefs,sitrep,ledger=None):
 successes=[]
 for activity in sitrep['verifiedActivities']:
  regions={o['region'] for o in sitrep['previousPortfolio']+sitrep['pendingOperations'] if o['mission']==activity['mission']}
  successes.append([activity['mission'].removeprefix('STR_ALIEN_'),next(iter(regions)).removeprefix('STR_') if len(regions)==1 else 'UNKNOWN_REGION',activity['count']])
 if ledger is not None:
  # Never guess a productive operation's location from another same-type parent.
  verified={}
  for op in ledger['operations']:
   if op['gainAt'].startswith(sitrep['period']):
    key=(op['mission'].removeprefix('STR_ALIEN_'),op['region'].removeprefix('STR_'))
    verified[key]=verified.get(key,0)+1
  successes=[[*key,count] for key,count in sorted(verified.items())]
 hotspots={b['region']:[b['independentSources'],0] for b in beliefs}
 for loss in sitrep['lossAssignments']:hotspots.setdefault(loss['region'],[0,0])[1]=loss['count']
 if ledger is not None:
  for loss in ledger['regionalLosses']:hotspots.setdefault(loss['region'],[0,0])[1]=max(hotspots.get(loss['region'],[0,0])[1],loss['count'])
 ordered=sorted(hotspots,key=lambda r:(-hotspots[r][1],-hotspots[r][0],r))
 result={'period':sitrep['period'],'productive':successes[:4],
  'resistance':[[r.removeprefix('STR_'),*hotspots[r]] for r in ordered[:4]],
  'other_hotspots':max(0,len(ordered)-4),'progress':[budget[k] for k in ('intelligence','logistics','adaptation')],
  'pending':[[o['mission'].removeprefix('STR_ALIEN_'),o['region'].removeprefix('STR_')] for o in sitrep['pendingOperations'][:4]],
  'other_pending':max(0,sitrep['pendingTotal']-4)}
 if ledger is not None:
  reviewed=sorted((op for op in ledger['operations'] if op['lastEventAt'].startswith(sitrep['period'])),key=lambda op:(op['lastEventAt'],op['missionId']),reverse=True)
  result['operations_cash_losses']=[[op['mission'].removeprefix('STR_ALIEN_'),op['region'].removeprefix('STR_'),op['lifecycle'],op['outcome'],op['cashEarned'],op['unavailable']] for op in reviewed[:2]]
  result['other_results']=len(reviewed)-min(2,len(reviewed))
  result['loss_window_months']=ledger['lossWindowMonths']
  result['ledger_truncated']=ledger['truncated'] or ledger['regionalLossesTruncated']
  # Fixed projection bounds keep six-operation late-campaign packets feasible.
  result['other_productive']=max(0,len(result['productive'])-2)
  result['productive']=result['productive'][:2]
  result['other_hotspots']+=max(0,len(result['resistance'])-3)
  result['resistance']=result['resistance'][:3]
  result['other_pending']+=max(0,len(result['pending'])-2)
  result['pending']=result['pending'][:2]
 return result

def campaign_objectives(budget,menu):
 def path(mission,requirements):
  missing={k:max(0,v-budget[k]) for k,v in requirements.items() if budget[k]<v}
  return {'missing':missing,'targets_available':any(c['mission']==mission for c in menu)}
 return {'national_control':path('STR_ALIEN_INFILTRATION',{'epochMonth':2,'adaptation':2,'intelligence':1}),
  'infrastructure':path('STR_ALIEN_BASE',{'epochMonth':1,'logistics':2}),
  'research':'Develop intelligence; cannot find bases. Extra intelligence is not a missing infiltration requirement once intelligence>=1.',
  'limits':'Prerequisites met is not mission success. Pacts have no recurring income; bases provide income, progression and local influence. Assault unavailable.'}

def conditional_outcomes(missions):
 delivered={
  'RESEARCH':'flight: +1 cash,+1 intelligence',
  'PROBE_MISSION':'flight: +1 cash,+1 intelligence',
  'HARVEST':'activity: +2 cash,+1 logistics',
  'ABDUCTION':'activity: +2 cash,+1 adaptation',
  'RETALIATION':'possible base discovery; no assault or cash',
  'TERROR':'native political pressure; no cash bonus',
  'SURFACE_ATTACK':'native political pressure; no cash bonus',
  'INFILTRATION':'possible country pact and base',
  'BASE':'possible base: 1-2 cash/month, gradual progress and local influence'}
 return {mission.removeprefix('STR_ALIEN_'):delivered[mission.removeprefix('STR_ALIEN_')] for mission in missions}

def plan(data,choose,tradeoffs=True,lessons=False,objectives=False,outcomes=False):
 budget,menu,beliefs,sitrep=m.portfolio_input(data)
 reports={b['region']:b['independentSources'] for b in beliefs}
 losses={g['region']:g['count'] for g in sitrep['lossAssignments']}
 ledger=data.get('operationLedger')
 if ledger is not None:
  for group in ledger['regionalLosses']:losses[group['region']]=max(losses.get(group['region'],0),group['count'])
 search_view=sitrep if ledger is None else {**sitrep,'lossAssignments':[{'region':r} for r in losses]}
 search,basis=m.search_region_pool(sorted({c['region'] for c in menu if c['mission']=='STR_ALIEN_RETALIATION'}),{r:{} for r in reports},search_view)
 if lessons and (reports or losses) and basis=='NO_MATCHING_EVIDENCE_EXPLORATION':
  search=[];basis='EVIDENCE_TARGETS_UNAVAILABLE_NO_UNSUPPORTED_EXPANSION'
 menu=[c for c in menu if c['mission']!='STR_ALIEN_RETALIATION' or c['region'] in search]
 selected=[];decisions=[];plans=[];remaining=budget['remaining']
 for slot in range(budget['maxOperations']):
  available=[c for c in menu if c not in selected and m.PORTFOLIO_COSTS[c['mission']]<=remaining]
  missions=sorted({c['mission'] for c in available})
  if not missions:break
  state={'goal':'Conquer Earth through executable investments. Balance future capacity, pressure and locating XCOM.',
   'remaining':remaining,'carry':budget['carryCap'],'expires_if_idle':max(0,remaining-budget['carryCap']),
   'loss_roles':sitrep['operationalReview']['loss_roles'],'pending_objectives':sitrep['operationalReview']['terror_objective_waves_pending'],
   'selected':[[p['goal'],p['region'].removeprefix('STR_')] for p in plans]}
  if ledger is not None:state['goal']='Conquer Earth. Balance capacity, pressure and locating XCOM.'
  if data.get('bases'):state['bases_count_income_influence']=[len(data['bases']),sum(b['income'] for b in data['bases']),max(b['influence'] for b in data['bases'])]
  if lessons:state['lessons']=campaign_lessons(budget,beliefs,sitrep,ledger)
  if objectives:state['objectives']=campaign_objectives(budget,available)
  if outcomes:
   state['conditional_results']=conditional_outcomes(missions)
   state['outcome_limits']='Verified rewards once/parent; cash next-month/capped. Odds/timing unknown. No recurring pact income; surviving bases earn income/progression/influence.'
  if tradeoffs:
   state['tradeoffs']={str(i):[PLANS[x][2],PLANS[x][3]] for i,x in enumerate(missions)}
   state['limits']='Repeated own losses suggest interference, not confirmed enemy base coordinates. Rewards require completion; capped bonus. No assault this month.'
  criteria={'P'+str(i):PLANS[x][1]+'; cost '+str(m.PORTFOLIO_COSTS[x]) for i,x in enumerate(missions)}
  criteria['SAVE']=f"Defer: carry {min(remaining,budget['carryCap'])}, forfeit {max(0,remaining-budget['carryCap'])}"
  label,receipt=choose(m.canonical(state),criteria,'Choose a concrete campaign investment or defer. Compare achievable gains and risks.')
  decisions.append({**receipt,'stage':'PLAN'})
  if label=='SAVE':break
  if label not in criteria:raise ValueError('Invalid plan choice')
  mission=missions[int(label[1:])]
  regions=sorted({c['region'] for c in available if c['mission']==mission})
  rows=[[r.removeprefix('STR_'),reports.get(r,0),losses.get(r,0)] for r in regions]
  state={'objective':PLANS[mission][0],'operation':mission,'regions_reports_assignment_losses':rows,
   'limits':'Report locations show XCOM reach, not bases. Assignment losses are uncertain clues. Zero reports is unknown exposure, not safety.'}
  if mission in ('STR_ALIEN_BASE','STR_ALIEN_INFILTRATION') and data.get('bases'):
   state['footholds']=[[b['region'],b['country'],b['influence']] for b in data['bases'][:6]]
  if ledger is not None:state['loss_window_months']=ledger['lossWindowMonths']
  if lessons:state['productive_history']=campaign_lessons(budget,beliefs,sitrep,ledger)['productive']
  if tradeoffs:state.update(pro=PLANS[mission][2],con=PLANS[mission][3])
  criteria={'R'+str(i):r.removeprefix('STR_').replace('_',' ') for i,r in enumerate(regions)}
  label,receipt=choose(m.canonical(state),criteria,'Choose a target suited to this objective. Search near evidence; productive missions balance gains against interference risk.')
  if label not in criteria:raise ValueError('Invalid target')
  region=regions[int(label[1:])]
  decisions.append({**receipt,'stage':'TARGET'})
  selected.append({'mission':mission,'region':region});remaining-=m.PORTFOLIO_COSTS[mission]
  plans.append({'goal':PLANS[mission][0],'mission':mission,'region':region,'cost':m.PORTFOLIO_COSTS[mission],
   'pro':PLANS[mission][2],'con':PLANS[mission][3],'reports':reports.get(region,0),'assignmentLosses':losses.get(region,0),
   'supportIds':sorted({i for b in beliefs if b['region']==region for i in b['evidenceIds']}|{i for g in sitrep['lossAssignments'] if g['region']==region for i in g['evidenceIds']}|{i for g in (ledger['regionalLosses'] if ledger else []) if g['region']==region for i in g['evidenceIds']}),
   'searchBasis':basis if mission=='STR_ALIEN_RETALIATION' else None,'safety':'UNKNOWN','gainStatus':'CONDITIONAL_NOT_REALIZED'})
 return {'operations':selected,'plans':plans,'remainingProposed':remaining,'status':'PREDICTED' if selected else 'SAVE_RESOURCES','decisions':decisions,
  **({'campaignObjectives':campaign_objectives(budget,menu)} if objectives else {}),
  **({'campaignAssessment':campaign_lessons(budget,beliefs,sitrep,ledger),'searchEligibility':basis,'assessmentLimits':'Productive gains are parent-linked when ledger present; craft loss is not whole-mission failure. Result cash is lifetime earned, not guaranteed next-month credit. Resistance is uncertain assignment evidence, not base coordinates. Pending coverage is partial.'} if lessons else {})}

