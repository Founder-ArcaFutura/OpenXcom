# Persistent UFO defence experiment

This is a scripted native-engine experiment, `defend-area-v1`. It does not call a
model or change the monthly commander. The normal launcher explicitly disables
it. Existing orders are ignored when the experiment is disabled.

## Play the test

```powershell
.\scripts\run-tactical-inspection.ps1 -Save 'build/local/user/xcom1/Three off the ramp.sav' -Defend -Launch
```

The launcher creates an isolated copy, opens it with observation and recording,
and enables `-tacticalDefend true`. Original saves remain outside its directory.
On exit it generates a replay viewer. The same command without `-Defend` creates
a stock-AI control session. Both preserve the starting RNG; different player
actions can still produce different subsequent RNG and outcomes.

Suggested human test:

1. Hold XCOM's starting positions for two or three turns. Watch where aliens
   move and whether they retain their posts rather than continue wandering.
2. Advance normally toward the UFO. Watch which aliens switch to native combat,
   ambush or escape behavior after contact.
3. Save at first contact and again after the engagement. Finish the battle if
   useful; the recorder also retains partial sessions and separate reloads.

In the replay viewer, select an alien. Its **Area order** column shows role,
revision, and status. The yellow `POST` marker is its persistent destination;
the green requested-action target can differ while native AI handles contact.
Order identity is `unit ID:revision`, scoped to that saved battle branch.
Status is the last controller decision; the recorded position shows whether a
move has since reached its post before the next decision updates that status.

## Policy and constraints

Only active, original hostile, small, non-Leeroy units carrying a loaded firearm
are eligible, in UFO recovery or ground-assault missions. Psi-capable units and
waypoint-launcher users retain native control, including shared-contact attacks.
Other units and mission
types retain stock behavior. Missing UFO map identity also falls back to native
AI; there is no invented objective.

UFO blocks come from the saved map-layout grid. Guard posts are existing
guard-ranked route nodes inside that footprint. Perimeter posts are ordinary
ground-level tiles in a two-to-five-tile ring outside its bounding rectangle.
These are spatial anchors, not evaluated cover, firing lanes or crossfire.

Unit ID order provides a deterministic preference for roughly two-thirds guards
and the remainder screens among currently active hostiles. Existing assignments
persist. A guard without a reachable interior post tries the perimeter instead.
This is not a globally optimal assignment or an exact guaranteed role ratio.

Assignment rejects unsafe, occupied and invalid placements and spaces new posts
three tiles from other active alien orders. It tries at most 32 nearest candidates
per role with native pathfinding, verifying the exact endpoint. A destination may
require multiple turns. Movement remains native, with native TU/energy checks
and a snapshot reservation for firearm users; there is no teleportation or free
movement. Upon reaching a post the unit holds its remaining TU for reactions.
Old individual patrol destination reservations are released on assignment.

Visible enemies, enemy spotters, or an existing native combat/ambush/escape mode with known
enemies suspend the order and allow native behavior. Shared target memory alone
does not cancel quiet patrol orders. Injury below two-thirds health, unsafe current ground, and unavailable
firearm/ammunition also yield to native AI. A dangerous/destroyed post is
invalidated. An unreachable route falls back to native AI and expires after
three distinct blocked turns. The order may resume when the interruption clears.
Orders do not force an alien to ignore new contacts during movement.

Post, role, assignment turn, revision, status and blockage counters are saved in
the native AI module. Legacy saves default to no orders. Disabling the feature
retains the saved fields for later inspection but bypasses the order controller.
Native loading does not restore AI modules for dead, ignored, or player-controlled
units. Their orders are retired on reload; telemetry retains the earlier history.

The scorer uses own unit positions and map geometry, not enemy coordinates.
Native known-contact and occupancy/pathfinding behavior is retained. This is
not a certification of fog-of-war fairness or a replacement of native cheating,
memory, morale, psi, explosives, or reaction mechanics.

## Replay and compare

```powershell
# Catalogue development saves and isolated inspection sessions:
.\build\local\laya-venv\Scripts\python.exe scripts/catalog-tactical-saves.py

# Three real alien phases in stock and defence modes; XCOM holds position:
.\build\local\laya-venv\Scripts\python.exe scripts/compare-defend-area.py

# A different snapshot or one-to-six phases:
.\build\local\laya-venv\Scripts\python.exe scripts/compare-defend-area.py `
  --save 'build/local/user/xcom1/Groudn baddle.sav' --phases 3
```

The catalogue is read-only YAML metadata, not a replacement for native loading.
It deduplicates exact bytes and reports encounter labels as grouping hints.
The initial inventory contained 76 distinct saves, 22 battlescape snapshots and
21 UFO-defence candidates. Multiple snapshots/reloads from one encounter are
not independent experiments.

The comparison runs stock and defence from the same save and initial RNG. Within
each arm, recording off, telemetry only, and observer-plus-telemetry must agree
on final serialized battle state and RNG. Each player-side phase boundary saves
and reloads a disposable checkpoint in a fresh native process, checking orders
for all units eligible for native AI restoration. The harness
uses native action execution with a fixed accelerated animation cadence and
dismissed presentation overlays; XCOM holds, so this is not a complete tactical
benchmark. Premature battle completion or unsupported states stop the test and
retain its logs rather than becoming successful samples.

Reports contain movement steps, decisions, order transitions, and per-boundary
positions/statuses. Neither more movement nor more casualties alone establishes
better tactics. Initial saves remain unchanged; generated outputs are ignored
under `build/local`.

Telemetry adds `defendExperiment`, per-unit `order` objects, and
`ORDER_TRANSITION` events. `AI_DECISION.action.controller` distinguishes the
scripted controller from native handling. Other events describe state execution
or order snapshots and are not causal claims about combat results.

The build helper now guards AI-module and battle-controller layouts as well as
the campaign commander layout: stale object files can otherwise allocate the
wrong size while linking successfully. `setup-local.ps1 -BuildJobs 8` supports
a faster local rebuild; the default remains two compiler workers. The optional
`-EmbeddedDebug` switch sets native compiler/linker metadata to embedded debug
information, avoiding this machine's PDB-manager mismatch and repeated builds
caused by a missing compiler PDB. It does not change global environment settings. See
[tactical inspection](TACTICAL_INSPECTION.md) for this machine's embedded-debug
compiler workaround and capture limitations.

## Recorded validation (2026-11-02)

- `Three off the ramp`, three alien phases: both arms and all observation modes
  passed. Stock recorded 97 movement steps and three snapshots; defence recorded
  50 movement steps and no shots while XCOM held its starting positions. These
  differences are behavior, not a quality ranking.
- All five surviving aliens retained revision-one orders through turns 2–4.
  Four held their posts. Unit 1000002 continued toward `[14,13,0]` across turns,
  then reached it after a fresh-process resume into turn 5 with the same order ID.
- `Muton madness`, an existing contact case: both arms passed. The defended run
  recorded contact suspensions and retained three native snapshot decisions.
- `More things`, including a severely injured alien and a casualty: the injured
  alien used native control with `SUSPENDED_INJURY`. Living controllers survived
  reload checks; the dead alien's AI was retired by native loading as expected.
- Each arm checked final battle/RNG equality across recording off, telemetry,
  and observer modes. Native checkpoints were loaded and compared in fresh
  processes. Original/copy source integrity checks passed.
- Existing native suites passed 184 UFO and 173 TFTD checks. Viewer JavaScript
  and Python/PowerShell syntax passed; browser interaction remains unverified
  because local browser control is disabled in Work settings.

Final local comparison folders are
`build/local/defend-comparison-20261102-192029-989242` and
`build/local/defend-comparison-20261102-192106-568128`; resume and injury receipts
are under `build/local/tactical-turn-test-20261102-192149-963002` and
`build/local/tactical-turn-test-20261102-192237-436780` respectively. Their raw
captures and generated checkpoints remain local, outside the tracked source.
