import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('budget',ROOT/'scripts'/'alien-command-budget.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
POLICY=json.loads((ROOT/'config'/'alien-command-budget.json').read_text())
def fact(i,event,mission=1,name='STR_ALIEN_RESEARCH',time='1999-01-02 00:00:00'):
 return {'schemaVersion':1,'id':i,'kind':'budget_fact','event':event,'missionId':mission,'mission':name,'gameTime':time}
class BudgetTests(unittest.TestCase):
 def run_budget(self,events,asof='1999-02-01 00:00:00',active=()): return b.evaluate(events,list(active),asof,POLICY)
 def test_monthly_growth_and_bounded_carry(self):
  rows=self.run_budget([])['monthly'];self.assertEqual(rows[0]['baseAllocation'],8);self.assertEqual(rows[1]['baseAllocation'],9);self.assertEqual(rows[1]['carryIn'],4)
 def test_bonus_arrives_next_month_once_per_mission(self):
  r=self.run_budget([fact(1,'MISSION_COMMITTED'),fact(2,'RESEARCH_FLIGHT_COMPLETED'),fact(3,'RESEARCH_FLIGHT_COMPLETED')]);self.assertEqual(r['monthly'][0]['earnedBonus'],0);self.assertEqual(r['monthly'][1]['earnedBonus'],1);self.assertEqual(r['progress']['intelligence'],1)
 def test_loss_does_not_refund_or_earn_bonus(self):
  e=fact(2,'ignored');e.update(kind='interception',admission='REPORTER_LOST');r=self.run_budget([fact(1,'MISSION_COMMITTED'),e]);self.assertEqual(r['monthly'][0]['committed'],2);self.assertEqual(r['verifiedGainMissionCount'],0)
 def test_surviving_contact_is_not_completed_research(self):
  e=fact(2,'ignored');e.update(kind='interception',admission='ADMITTED');self.assertEqual(self.run_budget([fact(1,'MISSION_COMMITTED'),e])['verifiedGainMissionCount'],0)
 def test_search_and_assault_have_separate_costs_and_prerequisites(self):
  search=fact(2,'BASE_SEARCH_COMMITTED',name='STR_ALIEN_RETALIATION');search['sourceUfoId']=20
  assault=fact(3,'BASE_ASSAULT_COMMITTED',name='STR_ALIEN_RETALIATION');assault['sourceUfoId']=21
  r=self.run_budget([fact(1,'MISSION_COMMITTED',name='STR_ALIEN_RETALIATION'),search,assault]);self.assertEqual(r['monthly'][0]['committed'],8);self.assertEqual(r['receipts'][1]['event'],'SEARCH_COST');self.assertEqual(r['receipts'][1]['eligibility'],'WOULD_ALLOW');self.assertIn('CAPABILITY_LOCKED',r['receipts'][2]['reasons'])
 def test_search_once_but_each_assault_ufo_costs(self):
  events=[fact(1,'MISSION_COMMITTED',name='STR_ALIEN_RETALIATION')]
  for i,event in enumerate(['BASE_SEARCH_COMMITTED','BASE_SEARCH_COMMITTED','BASE_ASSAULT_COMMITTED','BASE_ASSAULT_COMMITTED'],2):
   e=fact(i,event,name='STR_ALIEN_RETALIATION');e['sourceUfoId']=100+i;events.append(e)
  self.assertEqual(self.run_budget(events)['monthly'][0]['committed'],14)
 def test_direct_assault_does_not_pay_for_unperformed_search(self):
  e=fact(2,'BASE_ASSAULT_COMMITTED',name='STR_ALIEN_RETALIATION');e['sourceUfoId']=100
  self.assertEqual(self.run_budget([fact(1,'MISSION_COMMITTED',name='STR_ALIEN_RETALIATION'),e])['monthly'][0]['committed'],6)
 def test_known_deployment_can_be_priced_without_inventing_parent_start(self):
  e=fact(1,"BASE_SEARCH_COMMITTED",name="STR_ALIEN_RETALIATION");e["sourceUfoId"]=100
  r=self.run_budget([e]);self.assertEqual(r["monthly"][0]["committed"],2);self.assertFalse(r["coverageComplete"])
 def test_allowance_growth_tapers_over_eighteen_months(self):
  for d in range(5):
   r=b.evaluate([],[],'2001-01-01 00:00:00',POLICY,difficulty=d)
   self.assertEqual(r['monthly'][17]['baseAllocation'],r['monthly'][24]['baseAllocation'])
  self.assertGreater(b.evaluate([],[],'1999-01-01 00:00:00',POLICY,difficulty=4)['monthly'][0]['baseAllocation'],b.evaluate([],[],'1999-01-01 00:00:00',POLICY,difficulty=0)['monthly'][0]['baseAllocation'])
 def test_duplicate_start_and_decision_are_not_double_charged(self):
  e={'schemaVersion':1,'id':2,'kind':'decision','gameTime':'1999-01-02 00:00:00','execution':{'status':'MISSION_CREATED','missionId':1,'mission':'STR_ALIEN_RESEARCH'}};self.assertEqual(self.run_budget([fact(1,'MISSION_COMMITTED'),e])['monthly'][0]['committed'],2)
 def test_insufficient_capacity_reported_without_hiding_actual_cost(self):
  r=self.run_budget([fact(i,'MISSION_COMMITTED',i,'STR_ALIEN_TERROR') for i in range(1,4)]);self.assertEqual(r['monthly'][0]['remaining'],-4);self.assertIn('INSUFFICIENT_ALLOCATION',r['receipts'][-1]['reasons']);self.assertEqual(r['monthly'][1]['carryIn'],0)
 def test_capability_needs_progress_and_calendar(self):
  self.assertNotIn('assault_fleet',b.unlocked(POLICY,{'intelligence':2,'logistics':1},1));self.assertIn('assault_fleet',b.unlocked(POLICY,{'intelligence':2,'logistics':1},2));self.assertNotIn('assault_fleet',b.unlocked(POLICY,{},2))
 def test_missing_historical_start_is_unknown(self):
  r=self.run_budget([],active=[{'uniqueID':5,'type':'STR_ALIEN_RETALIATION'}]);self.assertFalse(r['coverageComplete']);self.assertEqual(r['monthly'][1]['committed'],0)
 def test_unbound_gain_does_not_fabricate_reward(self):
  r=self.run_budget([fact(1,'RESEARCH_FLIGHT_COMPLETED')]);self.assertEqual(r['verifiedGainMissionCount'],0);self.assertFalse(r['coverageComplete'])
 def test_duplicate_audit_id_rejected(self):
  with self.assertRaises(ValueError):self.run_budget([fact(1,'MISSION_COMMITTED'),fact(1,'MISSION_COMMITTED')])
 def test_future_event_rejected(self):
  with self.assertRaises(ValueError):self.run_budget([fact(1,'MISSION_COMMITTED',time='1999-03-01 00:00:00')])
 def test_invalid_policy_rejected(self):
  p=copy.deepcopy(POLICY);p['allocation']['carryDenominator']=0
  with self.assertRaises(ValueError):b.evaluate([],[],'1999-01-01 00:00:00',p)
 def test_tftd_calendar_starts_in_2040(self):
  r=b.evaluate([],[],"2040-02-01 00:00:00",POLICY,2040);self.assertEqual(len(r["monthly"]),2);self.assertEqual(r["monthly"][0]["month"],"2040-01");self.assertEqual(r["monthly"][1]["baseAllocation"],9)
 def test_unpriced_operation_exposes_coverage_gap(self):
  r=self.run_budget([fact(1,'MISSION_COMMITTED',name='MOD_OPERATION')]);self.assertFalse(r['coverageComplete']);self.assertEqual(r['coverageWarnings'][0]['reason'],'UNPRICED_OPERATION')
if __name__=='__main__':unittest.main()
