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

def plan(data,choose,tradeoffs=True):
 budget,menu,beliefs,sitrep=m.portfolio_input(data)
 reports={b['region']:b['independentSources'] for b in beliefs}
 losses={g['region']:g['count'] for g in sitrep['lossAssignments']}
 search,basis=m.search_region_pool(sorted({c['region'] for c in menu if c['mission']=='STR_ALIEN_RETALIATION'}),{r:{} for r in reports},sitrep)
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
 return {'operations':selected,'plans':plans,'remainingProposed':remaining,'status':'PREDICTED' if selected else 'SAVE_RESOURCES','decisions':decisions}

