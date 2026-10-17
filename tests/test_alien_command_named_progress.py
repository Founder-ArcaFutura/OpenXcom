import importlib.util,json,unittest
from pathlib import Path
from test_alien_command_portfolio import packet
spec=importlib.util.spec_from_file_location('named',Path(__file__).resolve().parents[1]/'scripts/test-named-progression.py')
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)

class NamedProgressTests(unittest.TestCase):
 def test_named_values_change_no_other_state(self):
  data=packet();s={'lessons':{'progress':[0,0,0]},'remaining':8}
  r=json.loads(n.transform(json.dumps(s),data,'named'))
  self.assertEqual(r,{'lessons':{'progress':{'intelligence':0,'logistics':0,'adaptation':0}},'remaining':8})
 def test_paths_keep_alternatives_and_real_assault_limit(self):
  b=packet()['budget'];b.update(epochMonth=4,intelligence=1,logistics=1,adaptation=2)
  p=n.paths(b);self.assertEqual(p['BASE'],{'missing':{'logistics':1},'prepare':['HARVEST']})
  self.assertEqual(p['INFILTRATION'],{'missing':{},'prepare':[]});self.assertIn('UNAVAILABLE',p['BASE_ASSAULT'])
 def test_path_preparation_tracks_only_missing_axes(self):
  b=packet()['budget'];b.update(epochMonth=3,logistics=2,intelligence=0,adaptation=2)
  p=n.paths(b);self.assertEqual(p['BASE']['prepare'],[]);self.assertEqual(p['INFILTRATION']['prepare'],['RESEARCH'])

if __name__=='__main__':unittest.main()
