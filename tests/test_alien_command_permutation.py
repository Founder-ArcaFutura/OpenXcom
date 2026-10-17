import importlib.util,unittest,collections
from pathlib import Path
spec=importlib.util.spec_from_file_location('permutation_probe',Path(__file__).resolve().parents[1]/'scripts/test-permutation-commander.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class PermutationTests(unittest.TestCase):
 def test_balanced_disjoint_families(self):
  criteria={'P0':'A','P1':'B','P2':'C','SAVE':'Defer'}
  a=p.families(criteria,'A');b=p.families(criteria,'B')
  self.assertTrue({tuple(x) for x in a}.isdisjoint({tuple(x) for x in b}))
  for family in (a,b):
   for position in range(4):self.assertEqual(collections.Counter(list(x)[position] for x in family),collections.Counter(criteria.keys()))
  self.assertEqual(p.families(dict(reversed(list(criteria.items()))),'A'),a)
 def test_mean_selection_aligns_by_id(self):
  rows=[{'P0':.7,'P1':.2,'SAVE':.1},{'SAVE':.1,'P1':.8,'P0':.1},{'P1':.1,'P0':.1,'SAVE':.8}]
  rs=[{'answer':{'choice':max(row,key=row.get),'probabilities':row}} for row in rows]
  choice,means,votes,margin=p.aggregate_answers(rs,rows[0])
  self.assertEqual(choice,'P1');self.assertAlmostEqual(means['P1'],1.1/3);self.assertEqual(votes,{'P0':1,'P1':1,'SAVE':1});self.assertGreater(margin,0)
 def test_save_is_not_suppressed(self):
  row={'P0':.1,'SAVE':.9};rs=[{'answer':{'choice':'SAVE','probabilities':row}}]*2
  self.assertEqual(p.aggregate_answers(rs,row)[0],'SAVE')
 def test_two_actions_have_no_disjoint_family(self):
  c={'P0':'Action','SAVE':'Defer'};self.assertEqual(p.families(c,'A'),p.families(c,'B'))
 def test_invalid_components_are_rejected(self):
  with self.assertRaises(ValueError):p.aggregate_answers([{'answer':{'choice':'P0','probabilities':{'P0':float('nan'),'SAVE':.2}}}],{'P0':'A','SAVE':'Defer'})
if __name__=='__main__':unittest.main()
