import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('compact',ROOT/'scripts/compact_command_probe.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class CompactContract(unittest.TestCase):
    def test_explicit_outcome_required(self):
        for status in ('SCOUT_LOST','DISRUPTED','COMPLETED'):
            with self.assertRaises(ValueError):c.outcome(status)
        self.assertEqual(c.outcome()['status'],'UNKNOWN')
        with self.assertRaises(ValueError):c.outcome('ASSUMED_FAILURE','receipt')

    def test_fixtures_and_packet_differences(self):
        if not (ROOT/'build/local/adaptation-native-v1/logistics-2/xcom1/strategy-input.json').exists():
            self.skipTest('Requires native fixture export')
        cases=c.cases();self.assertEqual(len(cases),8)
        packets={case['name']:c.packet(case) for case in cases}
        a=packets['heldout_target_STR_EUROPE'];b=packets['heldout_target_STR_NORTH_AFRICA']
        self.assertEqual(a['criteria'],b['criteria'])
        sa=json.loads(a['state']);sb=json.loads(b['state']);sa['interference']=sb['interference'];self.assertEqual(sa,sb)
        self.assertNotIn('INFILTRATION',packets['heldout_adaptation_1']['criteria'])
        self.assertIn('INFILTRATION',packets['heldout_adaptation_2']['criteria'])
        for case in cases:
            packet=packets[case['name']];self.assertIn(c.reference(packet)[0],packet['criteria'])
            self.assertEqual(c.briefing(case['data'])['outcome'],'UNKNOWN')
        baseline=json.loads(packets['heldout_outcome_UNKNOWN']['state'])
        for status in ('SCOUT_LOST','DISRUPTED','COMPLETED'):
            state=json.loads(packets['heldout_outcome_'+status]['state']);state['outcome']='UNKNOWN'
            self.assertEqual(state,baseline)

if __name__=='__main__':unittest.main()
