import importlib.util,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('model',Path(__file__).resolve().parents[1]/'scripts'/'alien-command-model.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def packet(budget=8):
 return {'schemaVersion':1,'budget':{'policyVersion':'monthly-portfolio-v1','epochMonth':1,'difficulty':4,'remaining':budget,'pendingBonus':0,'intelligence':0,'logistics':0,'adaptation':0,'maxOperations':3,'assaultAvailable':False,'terrorRewardVerified':False,'allowance':11,'carryCap':5,'nextAllowance':12,'nextBonusCap':6},'sitrep':{'schemaVersion':1,'period':'1999-01','coverage':'PARTIAL_FLEET_OUTCOMES','previousStrategy':'UNSPECIFIED','previousPortfolio':[],'previousReceiptId':0,'assets':{'deployed':0,'returned':0,'unavailable':0},'lossAssignments':[],'contacts':[],'verifiedActivities':[],'pendingOperations':[],'pendingTotal':0,'pendingTruncated':False,'enemyRecovery':'UNKNOWN','missionSuccess':'NOT_INFERRED_FROM_ACTIVITY_OR_DISAPPEARANCE','operationalReview':{'loss_roles':{'PREPARATION':0,'SEARCH':0,'OBJECTIVE_CARRIER':0,'UNKNOWN':0},'terror_objective_waves_pending':0,'rolling_results':[['1999-01',0,0]],'limits':'Partial own telemetry. Pending objective is not success; scout loss is not mission failure.','roleSupport':[],'pendingProgress':[]}},'knowledge':{'menuSource':'STATIC_RULESET_ONLY','candidates':[{'mission':m,'region':r} for m in ['STR_ALIEN_RESEARCH','STR_ALIEN_HARVEST','STR_ALIEN_TERROR'] for r in ['STR_EUROPE','STR_NORTH_AFRICA']],'beliefs':[],'evidence':[]}}
class PortfolioTests(unittest.TestCase):
 def test_search_prefers_reported_regions_to_loss_assignments(self):
  regions=['STR_ARCTIC','STR_EUROPE','STR_NORTH_AFRICA']
  pool,basis=m.search_region_pool(regions,{'STR_EUROPE':{'reporters':1}},{'lossAssignments':[{'region':'STR_NORTH_AFRICA'}]})
  self.assertEqual(pool,['STR_EUROPE']);self.assertEqual(basis,'SURVIVING_INTERCEPTION_REPORTS')
 def test_search_loss_fallback_and_no_evidence_exploration(self):
  regions=['STR_ARCTIC','STR_NORTH_AFRICA']
  pool,basis=m.search_region_pool(regions,{}, {'lossAssignments':[{'region':'STR_NORTH_AFRICA'}]})
  self.assertEqual(pool,['STR_NORTH_AFRICA']);self.assertEqual(basis,'RECENT_LOSS_ASSIGNMENTS_UNCERTAIN')
  self.assertEqual(m.search_region_pool(regions,{}, {'lossAssignments':[]})[0],regions)
 def test_exhausted_search_clues_do_not_open_unrelated_regions(self):
  p=packet(10)
  p['knowledge']['candidates']=[{'mission':'STR_ALIEN_RETALIATION','region':r} for r in ['STR_ARCTIC','STR_NORTH_AFRICA']]
  s=p['sitrep'];s['assets']['unavailable']=1;s['lossAssignments']=[{'region':'STR_NORTH_AFRICA','count':1,'evidenceIds':[1]}]
  s['operationalReview']['loss_roles']['UNKNOWN']=1;s['operationalReview']['rolling_results']=[['1999-01',1,0]]
  result=m.plan_portfolio(p,lambda state,criteria,ins:(next(iter(criteria)),{}))
  self.assertEqual(result['operations'],[{'mission':'STR_ALIEN_RETALIATION','region':'STR_NORTH_AFRICA'}])
  self.assertEqual(result['decisions'][-1]['targetingBasis'],'RECENT_LOSS_ASSIGNMENTS_UNCERTAIN')
 def test_three_operations_whole_budget(self):
  def choose(state,criteria,ins): return next(iter(criteria)),{}
  result=m.plan_portfolio(packet(10),choose)
  self.assertEqual(len(result['operations']),3);self.assertGreaterEqual(result['remainingProposed'],0)
  self.assertEqual(len({tuple(c.values()) for c in result['operations']}),3)
 def test_save_valid_without_reports(self):
  result=m.plan_portfolio(packet(),lambda state,criteria,ins:('SAVE' if 'SAVE' in criteria else next(iter(criteria)),{}))
  self.assertEqual(result['status'],'SAVE_RESOURCES');self.assertEqual(result['remainingProposed'],8)
 def test_affordability(self):
  result=m.plan_portfolio(packet(2),lambda state,criteria,ins:(next(iter(criteria)),{}))
  self.assertEqual(len(result['operations']),1);self.assertEqual(result['remainingProposed'],0)
 def test_unpriced_rejected(self):
  p=packet();p['knowledge']['candidates'][0]['mission']='STR_SECRET'
  with self.assertRaises(ValueError):m.plan_portfolio(p,lambda *args:('SAVE',{}))
 def test_hidden_input_rejected(self):
  p=packet();p['knowledge']['bases']=[1]
  with self.assertRaises(ValueError):m.portfolio_input(p)
 def test_duplicate_rejected(self):
  p=packet();p['knowledge']['candidates'].append(p['knowledge']['candidates'][0])
  with self.assertRaises(ValueError):m.portfolio_input(p)
 def test_bad_choice_rejected(self):
  with self.assertRaises(ValueError):m.plan_portfolio(packet(),lambda *args:('INVALID',{}))
 def test_strategy_drives_mixed_portfolio_context(self):
  states=[]
  def choose(state,criteria,ins):
   states.append(json.loads(state))
   return ('RESOURCE_ACQUISITION' if 'RESOURCE_ACQUISITION' in criteria else next(iter(criteria))),{}
  result=m.plan_portfolio(packet(10),choose)
  self.assertEqual(result['strategy'],'RESOURCE_ACQUISITION')
  self.assertEqual(result['decisions'][0]['stage'],'STRATEGY')
  self.assertTrue(all(s.get('strategy')=='RESOURCE_ACQUISITION' for s in states[1:]))
 def test_unverified_capture_claim_rejected(self):
  p=packet();p['sitrep']['enemyRecovery']='XCOM_CAPTURE_CONFIRMED'
  with self.assertRaises(ValueError):m.portfolio_input(p)
 def test_unknown_hidden_sitrep_fields_rejected(self):
  p=packet();p['sitrep']['xcomResearch']=['ALIEN_ALLOYS']
  with self.assertRaises(ValueError):m.portfolio_input(p)
 def test_no_affordable_operation_does_not_invent_strategy(self):
  result=m.plan_portfolio(packet(0),lambda *args:(_ for _ in ()).throw(AssertionError('Unexpected inference')))
  self.assertEqual(result['strategy'],'NO_FEASIBLE_OPERATION')
  self.assertEqual(result['operations'],[])
 def test_wrong_loss_counts_rejected(self):
  p=packet();p['sitrep']['assets']['unavailable']=1
  with self.assertRaises(ValueError):m.portfolio_input(p)
 def test_role_counts_cannot_invent_losses(self):
  p=packet();p['sitrep']['operationalReview']['loss_roles']['OBJECTIVE_CARRIER']=1
  with self.assertRaises(ValueError):m.portfolio_input(p)
 def test_hidden_role_context_rejected(self):
  p=packet();p['sitrep']['operationalReview']['capturedByXcom']=True
  with self.assertRaises(ValueError):m.portfolio_input(p)
 def test_deferral_states_explicit_forfeiture(self):
  states=[]
  def choose(state,criteria,ins):
   states.append((json.loads(state),criteria))
   return ('SAVE' if 'SAVE' in criteria else next(iter(criteria))),{}
  result=m.plan_portfolio(packet(13),choose)
  self.assertEqual(result['operations'],[])
  self.assertIn('carry 5, forfeit 8',states[-1][1]['SAVE'])
  self.assertIn('operational_review',states[0][0])
  self.assertIn('operational_review',states[-1][0])
if __name__=='__main__':unittest.main()
