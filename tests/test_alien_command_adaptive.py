import copy
import json
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
probe = runpy.run_path(str(ROOT / 'scripts/test-adaptive-responses.py'))


class AdaptiveFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / 'build/local/adaptation-native-v1/logistics-1/xcom1/strategy-input.json').exists():
            raise unittest.SkipTest('Native adaptation fixtures have not been exported')
        cls.cases = {c['name']: c for c in probe['cases']()}

    def test_risk_changes_only_assignment_location(self):
        a = copy.deepcopy(self.cases['risk_AUSTRALASIA']['data'])
        b = self.cases['risk_NORTH_AMERICA']['data']
        a['sitrep']['lossAssignments'][0]['region'] = 'STR_NORTH_AMERICA'
        self.assertEqual(a, b)
        pa = probe['capture'](self.cases['risk_AUSTRALASIA'])
        pb = probe['capture'](self.cases['risk_NORTH_AMERICA'])
        self.assertEqual(pa['criteria'], pb['criteria'])
        self.assertNotEqual(pa['state'], pb['state'])

    def test_native_gate_adds_only_bases(self):
        a, b = probe['native_inputs']()
        added = [c for c in b['knowledge']['candidates'] if c not in a['knowledge']['candidates']]
        self.assertEqual(len(added), 12)
        self.assertTrue(all(c['mission'] == 'STR_ALIEN_BASE' for c in added))

    def test_named_gate_and_role_reach_packet(self):
        for level in (1, 2):
            packet = probe['capture'](self.cases[f'gate_named_capability_{level}'])
            self.assertEqual(json.loads(packet['state'])['capability']['base_available'], level == 2)
        a = probe['capture'](self.cases['role_PREPARATION'])
        b = probe['capture'](self.cases['role_OBJECTIVE_CARRIER'])
        self.assertEqual(a['criteria'], b['criteria'])
        self.assertNotEqual(a['state'], b['state'])


if __name__ == '__main__':
    unittest.main()
