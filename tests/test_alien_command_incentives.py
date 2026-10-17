import copy,importlib.util,json,unittest
from pathlib import Path
from test_alien_command_portfolio import packet
spec=importlib.util.spec_from_file_location('incentives',Path(__file__).resolve().parents[1]/'scripts/test-conquest-incentives.py')
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
class IncentiveProbeTests(unittest.TestCase):
 def test_baseline_identity_and_target_packets_untouched(self):
  p=packet();state='{"remaining":8}';criteria={'P0':n.e.PLANS['STR_ALIEN_HARVEST'][1]+'; cost 3','SAVE':'Defer'}
  self.assertEqual(n.transform(state,criteria,p,'baseline'),(state,criteria))
  for arm in n.ARMS:self.assertEqual(n.transform(state,{'R0':'EUROPE'},p,arm),(state,{'R0':'EUROPE'}))
 def test_explicit_arms_share_state_and_preserve_ids_and_input(self):
  p=packet();before=copy.deepcopy(p);criteria={'P0':n.e.PLANS['STR_ALIEN_HARVEST'][1]+'; cost 3','SAVE':'Defer'}
  a=n.transform('{"remaining":8}',criteria,p,'explicit_current');b=n.transform('{"remaining":8}',criteria,p,'hypothetical')
  self.assertEqual(a[0],b[0]);self.assertEqual(list(a[1]),list(criteria));self.assertEqual(a[1]['SAVE'],criteria['SAVE'])
  self.assertIn('+2 resources',a[1]['P0']);self.assertIn('+3 resources',b[1]['P0']);self.assertEqual(p,before)
 def test_saturated_hypothetical_research_does_not_claim_live_payouts(self):
  p=packet();p['budget']['intelligence']=3
  self.assertIn('+0 resources, +0 intelligence',n.reward_text('STR_ALIEN_RESEARCH',p['budget'],True))
  self.assertIn('+1 resources, +1 intelligence',n.reward_text('STR_ALIEN_RESEARCH',p['budget'],False))
 def test_terror_reward_requires_success_not_site_creation(self):
  text=n.reward_text('STR_ALIEN_TERROR',packet()['budget'],True)
  self.assertIn('successful terror outcome',text);self.assertIn('defeat pays zero',text)
if __name__=='__main__':unittest.main()
