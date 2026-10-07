import importlib.util
import json
from pathlib import Path
import unittest
from test_alien_command_portfolio import packet

spec=importlib.util.spec_from_file_location('plans',Path(__file__).resolve().parents[1]/'scripts/test-campaign-plans.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class CampaignPlanTests(unittest.TestCase):
 def test_selected_objective_keeps_actual_operation(self):
  def choose(state,criteria,ins):
   if any('Harvest' in v for v in criteria.values()):return next(k for k,v in criteria.items() if 'Harvest' in v),{}
   if 'SAVE' in criteria:return 'SAVE',{}
   return next(iter(criteria)),{}
  result=p.plan(packet(8),choose)
  self.assertEqual(len(result['operations']),2)
  self.assertTrue(all(x['goal']=='BUILD_CAPACITY' and x['mission']=='STR_ALIEN_HARVEST' for x in result['plans']))
  self.assertEqual(result['remainingProposed'],2)
  self.assertTrue(all(x['safety']=='UNKNOWN' and x['gainStatus']=='CONDITIONAL_NOT_REALIZED' for x in result['plans']))
 def test_tradeoff_control_differs_only_in_explicit_context(self):
  captured=[]
  def choose(state,criteria,ins):
   captured.append(json.loads(state));return 'SAVE',{}
  p.plan(packet(),choose,False);p.plan(packet(),choose,True)
  self.assertNotIn('tradeoffs',captured[0]);self.assertIn('tradeoffs',captured[1])
  self.assertEqual(captured[0]['remaining'],captured[1]['remaining'])
 def test_search_does_not_promise_an_immediate_assault(self):
  description=p.PLANS['STR_ALIEN_RETALIATION']
  self.assertIn('later',description[2]);self.assertIn('assault currently unavailable',description[3])
 def test_invalid_choice_fails(self):
  with self.assertRaises(ValueError):p.plan(packet(),lambda *args:('BAD',{}))
 def test_live_wrapper_uses_simple_tested_packets(self):
  left=[];right=[]
  def choose(log):
   def call(state,criteria,ins):
    log.append((state,criteria,ins))
    return next(iter(criteria)),{}
   return call
  expected=p.plan(packet(),choose(left),False)
  actual=p.m.plan_concrete_portfolio(packet(),choose(right))
  self.assertEqual(left,right);self.assertEqual(actual['operations'],expected['operations'])
  self.assertEqual(actual['strategySource'],'DERIVED_SPEND_LABEL_NOT_MODEL_STRATEGY')
 def test_live_defer_is_compatible_and_does_not_invent_plans(self):
  actual=p.m.plan_concrete_portfolio(packet(),lambda *args:('SAVE',{}))
  self.assertEqual(actual['operations'],[]);self.assertEqual(actual['remainingProposed'],8)
  self.assertEqual(actual['strategySource'],'COMPATIBILITY_LABEL_NO_NEW_OPERATIONS')
 def test_live_infeasible_skips_inference(self):
  actual=p.m.plan_concrete_portfolio(packet(0),lambda *args:(_ for _ in ()).throw(AssertionError('Unexpected inference')))
  self.assertEqual(actual['strategy'],'NO_FEASIBLE_OPERATION');self.assertEqual(actual['operations'],[])

if __name__=='__main__':unittest.main()
