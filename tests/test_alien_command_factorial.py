import importlib.util,json,unittest
from pathlib import Path
from test_alien_command_portfolio import packet
spec=importlib.util.spec_from_file_location('factorial',Path(__file__).resolve().parents[1]/'scripts/test-conquest-factorial.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
analysis_spec=importlib.util.spec_from_file_location('factorial_analysis',Path(__file__).resolve().parents[1]/'scripts/analyze-conquest-factorial.py');analysis=importlib.util.module_from_spec(analysis_spec);analysis_spec.loader.exec_module(analysis)
class FactorialTests(unittest.TestCase):
 def test_factorial_contrasts_recover_known_interaction(self):
  cells={f.code(c):{'value':3*int(c[f.FACTORS[0]])+2*int(c[f.FACTORS[1]])+4*int(c[f.FACTORS[0]])*int(c[f.FACTORS[1]])} for c in f.configurations()}
  effects=analysis.contrasts(cells,['value'])
  self.assertEqual(effects[f.FACTORS[0]]['value'],5)
  self.assertEqual(effects[f.FACTORS[1]]['value'],4)
  self.assertEqual(effects[' x '.join(f.FACTORS[:2])]['value'],4)
  self.assertEqual(effects[' x '.join(f.FACTORS)]['value'],0)

 def test_complete_balanced_design(self):
  configs=f.configurations();self.assertEqual(len(configs),16);self.assertEqual(len({f.code(c) for c in configs}),16)
  for name in f.FACTORS:self.assertEqual(sum(c[name] for c in configs),8)
 def test_endpoints_match_previous_probe_exactly(self):
  p=packet();criteria={'P0':f.e.PLANS['STR_ALIEN_HARVEST'][1]+'; cost 3','P1':f.e.PLANS['STR_ALIEN_RESEARCH'][1]+'; cost 2','SAVE':'Defer'}
  for config,arm in [(f.configurations()[0],'explicit_current'),(f.configurations()[-1],'hypothetical')]:
   self.assertEqual(f.transform('{"remaining":8}',criteria,p,config),f.n.transform('{"remaining":8}',criteria,p,arm))
 def test_each_factor_changes_only_its_reward_family(self):
  b=packet()['budget'];b['intelligence']=3;base=f.configurations()[0]
  expected={'remove_research_cash':{'STR_ALIEN_RESEARCH','STR_ALIEN_PROBE_MISSION'},'saturate_research':{'STR_ALIEN_RESEARCH','STR_ALIEN_PROBE_MISSION'},'productive_bonus':{'STR_ALIEN_HARVEST','STR_ALIEN_ABDUCTION'},'terror_reward':{'STR_ALIEN_TERROR','STR_ALIEN_SURFACE_ATTACK'}}
  for name in f.FACTORS:
   on={**base,name:True}
   changed={m for m in f.e.PLANS if f.reward_text(m,b,base)!=f.reward_text(m,b,on)}
   self.assertEqual(changed,expected[name])
 def test_cache_keeps_option_order(self):
  a={'P0':'A','SAVE':'Defer'};b=dict(reversed(list(a.items())))
  self.assertNotEqual(f.packet_key('state',a,'instruction'),f.packet_key('state',b,'instruction'))
  self.assertEqual(f.reorder(a,'seeded'),f.reorder(a,'seeded'));self.assertEqual(f.reorder({'R0':'EUROPE'},'reversed'),{'R0':'EUROPE'})
if __name__=='__main__':unittest.main()
