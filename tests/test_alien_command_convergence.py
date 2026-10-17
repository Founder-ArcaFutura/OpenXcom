import importlib.util,unittest,collections
from pathlib import Path
from test_alien_command_portfolio import packet
spec=importlib.util.spec_from_file_location('convergence',Path(__file__).resolve().parents[1]/'scripts/test-permutation-convergence.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
class ConvergenceTests(unittest.TestCase):
 def test_six_balanced_pairwise_disjoint_orbits(self):
  criteria={**{'P'+str(i):str(i) for i in range(5)},'SAVE':'Defer'};families=c.family_orders(criteria);seen=set()
  for name,orders in families.items():
   keys={tuple(x) for x in orders};self.assertTrue(seen.isdisjoint(keys));seen.update(keys)
   for position in range(6):self.assertEqual(collections.Counter(list(x)[position] for x in orders),collections.Counter(criteria.keys()))
  self.assertEqual(len(seen),36);self.assertEqual(families['A'],c.p.families(criteria,'A'));self.assertEqual(families['B'],c.p.families(criteria,'B'))
 def test_capture_is_first_plan_and_preserves_budget(self):
  data=packet();before=data['budget'].copy();p=c.first_packet(data)
  self.assertIn('SAVE',p['criteria']);self.assertIn('payout_limits',p['state']);self.assertEqual(data['budget'],before)
 def test_pool_component_counts(self):
  self.assertEqual([len(x)*6 for x in c.POOLS],[12,12,12,24,24,36])
if __name__=='__main__':unittest.main()
