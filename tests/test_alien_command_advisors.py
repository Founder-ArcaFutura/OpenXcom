import importlib.util
import json
from pathlib import Path
import unittest
from test_alien_command_portfolio import packet

spec=importlib.util.spec_from_file_location('advisors',Path(__file__).resolve().parents[1]/'scripts/test-command-advisors.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def supported_packet():
 p=packet()
 p['knowledge']['candidates']=[{'mission':'STR_ALIEN_RETALIATION','region':r} for r in ['STR_ARCTIC','STR_NORTH_AFRICA']]
 s=p['sitrep'];s['assets']['unavailable']=1;s['lossAssignments']=[{'region':'STR_NORTH_AFRICA','count':1,'evidenceIds':[7]}]
 s['operationalReview']['loss_roles']['UNKNOWN']=1;s['operationalReview']['rolling_results']=[['1999-01',1,0]]
 return p

class AdvisorTests(unittest.TestCase):
 def test_advisors_can_abstain(self):
  advice,receipts=a.advise(packet(),lambda *args:('UNKNOWN',{}))
  self.assertTrue(all(not rows for rows in advice.values()))
  self.assertEqual({r['advisor'] for r in receipts},set(a.ROLES))
 def test_unsupported_roles_gate_without_model_call(self):
  advice,receipts=a.advise(packet(),lambda *args:(_ for _ in ()).throw(AssertionError('Unsupported inference')))
  self.assertTrue(all(r['source']=='EVIDENCE_GATE' for r in receipts))
 def test_search_advisor_cannot_choose_unsupported_arctic(self):
  def choose(state,criteria,ins):
   self.assertNotIn('ARCTIC',criteria.values())
   return next(iter(criteria)),{}
  advice,_=a.advise(supported_packet(),choose)
  self.assertEqual(advice['RESISTANCE'][0]['region'],'STR_NORTH_AFRICA')
  self.assertEqual(advice['RESISTANCE'][0]['supportIds'],[7])
 def test_ranked_regions_unique_and_no_invented_support(self):
  advice,_=a.advise(packet(),lambda state,criteria,ins:(next(iter(criteria)),{}))
  for rows in advice.values():
   self.assertEqual(len({r['region'] for r in rows}),len(rows))
   for row in rows:
    self.assertEqual(row['supportIds'],[])
    self.assertEqual(row['politicalVulnerability'],'UNKNOWN')
 def test_commander_receives_summary_without_detailed_evidence(self):
  states=[]
  def choose(state,criteria,ins):
   s=json.loads(state);states.append(s)
   return ('UNKNOWN' if 'advisor' in s else 'SAVE' if 'SAVE' in criteria else next(iter(criteria))),{}
  result=a.advisory_portfolio(packet(),choose)
  self.assertEqual(result['operations'],[])
  commanders=[s for s in states if 'advisor' not in s]
  self.assertTrue(all('advice' in s for s in commanders))
  self.assertTrue(all('surviving_reports' not in s and 'own_losses_by_assignment' not in s and 'operational_review' not in s for s in commanders))
 def test_bad_advisor_choice_rejected(self):
  with self.assertRaises(ValueError):a.advise(supported_packet(),lambda *args:('BAD',{}))

if __name__=='__main__':unittest.main()
