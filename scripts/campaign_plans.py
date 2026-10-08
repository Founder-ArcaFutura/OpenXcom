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
 'STR_ALIEN_BASE':('BUILD_INFRASTRUCTURE','Establish alien infrastructure','Establishes a base under native rules.','Costs 6; recurring base income is not implemented.'),
 'STR_ALIEN_INFILTRATION':('SEEK_CONTROL','Infiltrate to seek national control','Can obtain national control under native rules.','Costs 6; recurring control income is not implemented.')}

def campaign_lessons(budget,beliefs,sitrep):
 successes=[]
 for activity in sitrep['verifiedActivities']:
  regions={o['region'] for o in sitrep['previousPortfolio']+sitrep['pendingOperations'] if o['mission']==activity['mission']}
  successes.append([activity['mission'].removeprefix('STR_ALIEN_'),next(iter(regions)).removeprefix('STR_') if len(regions)==1 else 'UNKNOWN_REGION',activity['count']])
 hotspots={b['region']:[b['independentSources'],0] for b in beliefs}
 for loss in sitrep['lossAssignments']:hotspots.setdefault(loss['region'],[0,0])[1]=loss['count']
 ordered=sorted(hotspots,key=lambda r:(-hotspots[r][1],-hotspots[r][0],r))
 return {'period':sitrep['period'],'productive':successes[:4],
  'resistance':[[r.removeprefix('STR_'),*hotspots[r]] for r in ordered[:4]],
  'other_hotspots':max(0,len(ordered)-4),'progress':[budget[k] for k in ('intelligence','logistics','adaptation')],
  'pending':[[o['mission'].removeprefix('STR_ALIEN_'),o['region'].removeprefix('STR_')] for o in sitrep['pendingOperations'][:4]],
  'other_pending':max(0,sitrep['pendingTotal']-4)}

def plan(data,choose,tradeoffs=True,lessons=False):
 budget,menu,beliefs,sitrep=m.portfolio_input(data)
 reports={b['region']:b['independentSources'] for b in beliefs}
 losses={g['region']:g['count'] for g in sitrep['lossAssignments']}
 search,basis=m.search_region_pool(sorted({c['region'] for c in menu if c['mission']=='STR_ALIEN_RETALIATION'}),{r:{} for r in reports},sitrep)
 if lessons and (reports or losses) and basis=='NO_MATCHING_EVIDENCE_EXPLORATION':
  search=[];basis='EVIDENCE_TARGETS_UNAVAILABLE_NO_UNSUPPORTED_EXPANSION'
 menu=[c for c in menu if c['mission']!='STR_ALIEN_RETALIATION' or c['region'] in search]
 selected=[];decisions=[];plans=[];remaining=budget['remaining']
 for slot in range(3):
  available=[c for c in menu if c not in selected and m.PORTFOLIO_COSTS[c['mission']]<=remaining]
  missions=sorted({c['mission'] for c in available})
  if not missions:break
  state={'goal':'Conquer Earth through executable investments. Balance future capacity, pressure and locating XCOM.',
   'remaining':remaining,'carry':budget['carryCap'],'expires_if_idle':max(0,remaining-budget['carryCap']),
   'loss_roles':sitrep['operationalReview']['loss_roles'],'pending_objectives':sitrep['operationalReview']['terror_objective_waves_pending'],
   'selected':[[p['goal'],p['region'].removeprefix('STR_')] for p in plans]}
  if lessons:state['lessons']=campaign_lessons(budget,beliefs,sitrep)
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
  if lessons:state['productive_history']=campaign_lessons(budget,beliefs,sitrep)['productive']
  if tradeoffs:state.update(pro=PLANS[mission][2],con=PLANS[mission][3])
  criteria={'R'+str(i):r.removeprefix('STR_').replace('_',' ') for i,r in enumerate(regions)}
  label,receipt=choose(m.canonical(state),criteria,'Choose a target suited to this objective. Search near evidence; productive missions balance gains against interference risk.')
  if label not in criteria:raise ValueError('Invalid target')
  region=regions[int(label[1:])]
  decisions.append({**receipt,'stage':'TARGET'})
  selected.append({'mission':mission,'region':region});remaining-=m.PORTFOLIO_COSTS[mission]
  plans.append({'goal':PLANS[mission][0],'mission':mission,'region':region,'cost':m.PORTFOLIO_COSTS[mission],
   'pro':PLANS[mission][2],'con':PLANS[mission][3],'reports':reports.get(region,0),'assignmentLosses':losses.get(region,0),
   'supportIds':sorted({i for b in beliefs if b['region']==region for i in b['evidenceIds']}|{i for g in sitrep['lossAssignments'] if g['region']==region for i in g['evidenceIds']}),
   'searchBasis':basis if mission=='STR_ALIEN_RETALIATION' else None,'safety':'UNKNOWN','gainStatus':'CONDITIONAL_NOT_REALIZED'})
 return {'operations':selected,'plans':plans,'remainingProposed':remaining,'status':'PREDICTED' if selected else 'SAVE_RESOURCES','decisions':decisions,
  **({'campaignAssessment':campaign_lessons(budget,beliefs,sitrep),'searchEligibility':basis,'assessmentLimits':'Productive activity is verified; unique recorded assignment suggests region, not full mission success. Resistance rows are reporters and assignment losses, not base coordinates. Pending coverage is partial.'} if lessons else {})}

