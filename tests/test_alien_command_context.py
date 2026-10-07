import copy
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("experiment", Path(__file__).resolve().parents[1] / "scripts/test-commander-context.py")
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


def fixture():
    events = [{"kind": "own_operation", "id": i, "event": event, "missionId": 1, "mission": "STR_ALIEN_TERROR",
               "sourceUfoId": craft, "gameTime": "1999-02-01 00:00:00"}
              for i, event, craft in [(1, "MISSION_ASSIGNED", 0), (2, "CRAFT_DEPLOYED", 10), (3, "CRAFT_UNAVAILABLE", 10),
                                       (4, "CRAFT_DEPLOYED", 11), (5, "CRAFT_UNAVAILABLE", 11)]]
    save = {"alienCommand": {"audit": [json.dumps(e) for e in events]},
            "alienMissions": [{"uniqueID": 1, "type": "STR_ALIEN_TERROR", "region": "STR_NORTH_AFRICA", "nextWave": 2, "nextUfoCounter": 0}]}
    receipt = {"id": 6, "input": {"sitrep": {"period": "1999-02", "assets": {"unavailable": 2}, "verifiedActivities": [], "pendingOperations": [{"missionId": 1}]}}}
    rules = {"STR_ALIEN_TERROR": {"waves": [{"ufo": "STR_MEDIUM_SCOUT", "count": 1}, {"ufo": "STR_LARGE_SCOUT", "count": 1}, {"ufo": "STR_TERROR_SHIP", "count": 1, "objective": True}]}}
    return save, receipt, rules


class ContextTests(unittest.TestCase):
    def test_scout_losses_leave_objective_pending(self):
        context, provenance = experiment.owned_context(*fixture())
        self.assertEqual(context["loss_roles"]["PREPARATION"], 2)
        self.assertEqual(context["loss_roles"]["OBJECTIVE_CARRIER"], 0)
        self.assertEqual(context["terror_objective_waves_pending"], 1)
        self.assertEqual([x["craft"] for x in provenance["lossCraft"]], ["STR_MEDIUM_SCOUT", "STR_LARGE_SCOUT"])

    def test_missing_deployment_coverage_preserves_unknown(self):
        save, receipt, rules = fixture()
        save["alienCommand"]["audit"] = [x for x in save["alienCommand"]["audit"] if json.loads(x)["id"] != 2]
        context, _ = experiment.owned_context(save, receipt, rules)
        self.assertEqual(context["loss_roles"]["UNKNOWN"], 2)

    def test_hidden_player_state_does_not_change_context(self):
        save, receipt, rules = fixture()
        before = experiment.owned_context(save, receipt, rules)
        changed = copy.deepcopy(save)
        changed.update(bases=[{"lon": 1}], research=["LASERS"], funds=100000000)
        self.assertEqual(experiment.owned_context(changed, receipt, rules), before)

    def test_future_telemetry_is_excluded(self):
        save, receipt, rules = fixture()
        before = experiment.owned_context(save, receipt, rules)
        event = json.loads(save["alienCommand"]["audit"][-1]); event.update(id=7, sourceUfoId=90)
        save["alienCommand"]["audit"].append(json.dumps(event))
        self.assertEqual(experiment.owned_context(save, receipt, rules), before)


if __name__ == "__main__":
    unittest.main()
