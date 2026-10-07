"""Read-only checkpoint experiment; never installs an experimental live policy."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import time
import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("commander", ROOT / "scripts/alien-command-model.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def owned_context(save, receipt, rules):
    """Reconstruct roles only for missions observed continuously since assignment."""
    cutoff = receipt["id"]
    events = [json.loads(x) if isinstance(x, str) else x for x in save["alienCommand"]["audit"]]
    events = [e for e in events if e["id"] < cutoff]
    assigned = {e["missionId"] for e in events if e["kind"] == "own_operation" and e["event"] == "MISSION_ASSIGNED"}
    deployed = {}
    for e in events:
        if e["kind"] == "own_operation" and e["event"] == "CRAFT_DEPLOYED":
            deployed.setdefault(e["missionId"], []).append(e)
    craft_roles = {}
    support = []
    active = {m["uniqueID"]: m for m in save.get("alienMissions", [])}
    for mid in assigned:
        records = deployed.get(mid, [])
        if not records:
            continue
        rule = rules.get(records[0]["mission"])
        if not rule:
            continue
        waves = [(wave["ufo"], bool(wave.get("objective", False))) for wave in rule["waves"] for _ in range(wave["count"])]
        if len(records) > len(waves):
            continue  # A looping/modded mission needs explicit native wave telemetry.
        mission = active.get(mid)
        expected = sum(w["count"] for w in rule["waves"][:mission["nextWave"]]) + mission.get("nextUfoCounter", 0) if mission else len(waves)
        if len(records) != expected:
            continue  # Incomplete telemetry cannot establish a craft's wave role.
        for event, (craft, objective) in zip(records, waves):
            role = "SEARCH" if event["mission"] == "STR_ALIEN_RETALIATION" else "OBJECTIVE_CARRIER" if objective else "PREPARATION"
            craft_roles[event["sourceUfoId"]] = (craft, role)
            support.append(event["id"])
    losses = {"PREPARATION": 0, "SEARCH": 0, "OBJECTIVE_CARRIER": 0, "UNKNOWN": 0}
    seen = set()
    loss_craft = []
    for e in events:
        if e["kind"] != "own_operation" or e["event"] != "CRAFT_UNAVAILABLE" or not e["gameTime"].startswith(receipt["input"]["sitrep"]["period"]):
            continue
        uid = e["sourceUfoId"]
        if uid in seen:
            continue
        seen.add(uid)
        craft, role = craft_roles.get(uid, ("UNKNOWN", "UNKNOWN"))
        losses[role] += 1
        loss_craft.append({"craft": craft, "role": role, "receiptId": e["id"]})
    expected = receipt["input"]["sitrep"]["assets"]["unavailable"]
    if len(seen) > expected:
        raise ValueError("Owned losses exceed native sitrep")
    losses["UNKNOWN"] += expected - len(seen)
    pending = []
    pending_ids = {o["missionId"] for o in receipt["input"]["sitrep"]["pendingOperations"]}
    for mission in save.get("alienMissions", []):
        if mission["uniqueID"] not in pending_ids or mission["type"] != "STR_ALIEN_TERROR":
            continue
        rule = rules[mission["type"]]
        objective_pending = any(w.get("objective", False) for w in rule["waves"][mission["nextWave"]:])
        pending.append({"missionId": mission["uniqueID"], "region": mission["region"], "objectiveWavePending": objective_pending})
    history = [e["input"]["sitrep"] for e in events if e["kind"] == "portfolio"][-1:] + [receipt["input"]["sitrep"]]
    context = {"loss_roles": losses, "terror_objective_waves_pending": sum(p["objectiveWavePending"] for p in pending),
               "rolling_results": [[s["period"], s["assets"]["unavailable"], sum(g["count"] for g in s["verifiedActivities"])] for s in history],
               "limits": "Partial own telemetry. Pending objective is not success; scout loss is not mission failure."}
    return context, {"provenance": "OWN_ASSIGNMENT_AND_DEPLOYMENT_ORDER_PLUS_STOCK_WAVES", "deploymentReceiptIds": support,
                     "lossCraft": loss_craft, "pendingTerrorOperations": pending,
                     "limitation": "Role reconstruction is an offline stock-rules experiment; native explicit craft/wave telemetry is required before live use."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    before = model.file_digest(args.save)
    docs = list(yaml.safe_load_all(args.save.read_text(encoding="utf-8")))
    stamp = docs[0]["time"]
    if stamp["day"] != 1 or stamp["hour"] != 0 or stamp["minute"] > 1:
        raise ValueError("Use a boundary save within the first two minutes; later mission state would leak future progress")
    save = docs[-1]
    receipts = [json.loads(x) for x in save["alienCommand"]["audit"] if json.loads(x)["kind"] == "portfolio"]
    receipt = receipts[-1]
    if receipt["gameTime"][:7] != f'{stamp["year"]:04}-{stamp["month"]:02}':
        raise ValueError("Latest portfolio is not from this boundary")
    rules_path = ROOT / "bin/standard/xcom1/alienMissions.rul"
    rules = {r["type"]: r for r in yaml.safe_load(rules_path.read_text())["alienMissions"]}
    context, provenance = owned_context(save, receipt, rules)
    # Keep this historical four-way experiment comparable after the live
    # policy gained the new fields: baseline prompts still reproduce v3.
    if "operationalReview" not in receipt["input"]["sitrep"]:
        progress=[]
        pending_ids={o["missionId"] for o in receipt["input"]["sitrep"]["pendingOperations"]}
        for mission in save.get("alienMissions",[]):
            if mission["uniqueID"] in pending_ids:
                waves=rules[mission["type"]]["waves"]
                progress.append({"missionId":mission["uniqueID"],"nextWave":mission["nextWave"],"totalWaves":len(waves),"objectiveWavePending":any(w.get("objective",False) for w in waves[mission["nextWave"]:])})
        receipt["input"]["sitrep"]["operationalReview"]={**context,"roleSupport":[],"pendingProgress":progress}
    agent, identity = model.load_agent(args.checkpoint, "cpu", model.V4_SHA256)
    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    for variant in ("baseline", "defer_only", "context_only", "context_and_defer"):
        def choose(state, criteria, instructions):
            data = json.loads(state)
            criteria = dict(criteria)
            data.pop("operational_review",None)
            data.pop("deferral",None)
            if "SAVE" in criteria:
                criteria["SAVE"]="Reserve remaining resources; end this month's operations."
                instructions="Select an operation to advance the chosen strategy; mixed objectives are valid. Compare deployment against saving and expiring allowance."
            if "context" in variant and ("sitrep" in data or "recent_results" in data):
                data["operational_review"] = context
            if "defer" in variant and "SAVE" in criteria:
                remaining, cap = data["remaining"], data["carry_limit"]
                criteria["SAVE"] = f"Defer investment: carry {min(remaining, cap)}, forfeit {max(0, remaining-cap)}; no new missions."
                data["deferral"] = "Money alone cannot unlock bases/infiltration; verified productive activity earns prerequisites."
                instructions = "Choose investment or deferral. Compare affordable productive missions against carry, forfeiture and pending commitments; do not invent future gains."
            return model.checked_choice(agent, model.canonical(data), criteria, instructions)
        started = time.perf_counter()
        try:
            result = model.plan_portfolio(copy.deepcopy(receipt["input"]), choose)
        except ValueError as error:
            result = {"status": "INPUT_REJECTED", "error": str(error)}
        result.update(variant=variant, latencyMs=round((time.perf_counter()-started)*1000, 2), **identity)
        (args.out / f"{variant}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        results.append(result)
        print(json.dumps({k: result.get(k) for k in ("variant", "strategy", "status", "operations", "remainingProposed", "error")}), flush=True)
    after = model.file_digest(args.save)
    if before != after:
        raise RuntimeError("Source save changed during experiment")
    manifest = {"sourceSave": str(args.save.resolve()), "sourceSha256": before, "originalUnchanged": True,
                "rulesSha256": model.file_digest(rules_path), "inputSha256": model.digest(receipt["input"]),
                "context": context, "provenance": provenance, "executedMissions": False, "livePolicyChanged": False,
                "baselineChoiceMatchesRecorded": results[0].get("decisions") == json.loads(receipt["response"]).get("decisions")}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
