import importlib.util,unittest
from pathlib import Path
from test_alien_command_portfolio import packet
spec=importlib.util.spec_from_file_location('whole',Path(__file__).resolve().parents[1]/'scripts/test-whole-portfolios.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)

class WholePortfolioTests(unittest.TestCase):
 def test_candidates_legal_unique_and_include_before_and_defer(self):
  data=packet(10);before=[data['knowledge']['candidates'][0]]
  roster=w.candidates(data,before)
  self.assertTrue(any(r['operations']==before for r in roster));self.assertTrue(any(not r['operations'] for r in roster))
  keys=[tuple(sorted((o['mission'],o['region']) for o in r['operations'])) for r in roster]
  self.assertEqual(len(keys),len(set(keys)))
  for r in roster:self.assertEqual(w.validate(r['operations'],data),r['cost'])
 def test_order_change_does_not_change_options_or_selected_mapping(self):
  data=packet(10);roster=w.candidates(data,[data['knowledge']['candidates'][0]])
  states=[]
  def choose(state,criteria,ins):states.append((state,criteria));return roster[0]['id'],{}
  a=w.choose_whole(data,roster,choose,list(range(len(roster))))
  b=w.choose_whole(data,roster,choose,list(reversed(range(len(roster)))))
  self.assertEqual(a['operations'],b['operations']);self.assertEqual(states[0][0],states[1][0]);self.assertEqual(states[0][1],states[1][1])
 def test_invalid_portfolio_rejected(self):
  data=packet()
  with self.assertRaises(ValueError):w.validate([data['knowledge']['candidates'][0]]*2,data)
  with self.assertRaises(ValueError):w.choose_whole(data,w.candidates(data,[]),lambda *args:('INVALID',{}),[0])

if __name__=='__main__':unittest.main()
