import importlib.util,json,unittest
from pathlib import Path
from test_alien_command_portfolio import packet
from test_alien_command_plans import p
spec=importlib.util.spec_from_file_location('outcomes',Path(__file__).resolve().parents[1]/'scripts/test-outcome-contract.py')
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)

class OutcomeTests(unittest.TestCase):
 def test_contract_only_adds_outcome_information(self):
  states=[]
  def choose(state,criteria,instructions):states.append((json.loads(state),criteria,instructions));return 'SAVE',{}
  p.plan(packet(),choose,False,True,False,False)
  p.plan(packet(),choose,False,True,False,True)
  new=states[1][0].copy();self.assertIn('conditional_results',new);self.assertIn('once/parent',new.pop('outcome_limits'));new.pop('conditional_results')
  self.assertEqual(new,states[0][0]);self.assertEqual(states[0][1:],states[1][1:])
 def test_old_menu_filter_applied_without_mutating_source(self):
  data=packet();data['knowledge']['candidates']=[{'mission':'STR_ALIEN_INFILTRATION','region':r} for r in ('STR_ANTARCTICA','STR_EUROPE')]
  new,removed=o.geographic_filter(data)
  self.assertEqual(removed,[{'mission':'STR_ALIEN_INFILTRATION','region':'STR_ANTARCTICA'}])
  self.assertEqual(new['knowledge']['candidates'],[{'mission':'STR_ALIEN_INFILTRATION','region':'STR_EUROPE'}])
  self.assertEqual(len(data['knowledge']['candidates']),2)
 def test_contract_does_not_award_or_force_operations(self):
  data=packet();before=json.dumps(data,sort_keys=True)
  result=p.plan(data,lambda *args:('SAVE',{}),False,True,False,True)
  self.assertEqual(result['operations'],[]);self.assertEqual(before,json.dumps(data,sort_keys=True))

if __name__=='__main__':unittest.main()
