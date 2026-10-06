import importlib.util,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('model',Path(__file__).resolve().parents[1]/'scripts'/'alien-command-model.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def packet(budget=8):
 return {'schemaVersion':1,'budget':{'policyVersion':'monthly-portfolio-v1','epochMonth':1,'difficulty':4,'remaining':budget,'pendingBonus':0,'intelligence':0,'logistics':0,'adaptation':0,'maxOperations':3,'assaultAvailable':False,'terrorRewardVerified':False,'allowance':11,'carryCap':5,'nextAllowance':12,'nextBonusCap':6},'knowledge':{'menuSource':'STATIC_RULESET_ONLY','candidates':[{'mission':m,'region':r} for m in ['STR_ALIEN_RESEARCH','STR_ALIEN_HARVEST','STR_ALIEN_TERROR'] for r in ['STR_EUROPE','STR_NORTH_AFRICA']],'beliefs':[],'evidence':[]}}
class PortfolioTests(unittest.TestCase):
 def test_three_operations_whole_budget(self):
  def choose(state,criteria,ins): return next(iter(criteria)),{}
  result=m.plan_portfolio(packet(10),choose)
  self.assertEqual(len(result['operations']),3);self.assertGreaterEqual(result['remainingProposed'],0)
  self.assertEqual(len({tuple(c.values()) for c in result['operations']}),3)
 def test_save_valid_without_reports(self):
  result=m.plan_portfolio(packet(),lambda *args:('SAVE',{}))
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
if __name__=='__main__':unittest.main()
