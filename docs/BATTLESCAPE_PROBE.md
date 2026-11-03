# Battlescape destination scaffold

For live turn capture and a separate omniscient display, see
[tactical inspection](TACTICAL_INSPECTION.md). That recorder observes the stock
AI; the scripted destination assignments below remain offline.

This is an offline native-engine experiment, separate from the monthly model.
It loads disposable copies of real UFO battle saves, compares patrol destinations
with a scripted shared defence, and exports JSON plus a map. It does not move
units, run combat, advance turns, call a model, or change live AI behavior.

## Run

The existing Windows engine objects and original-game resources must already be
staged by `scripts/setup-local.ps1`. The runner uses the local Python environment
but has no third-party Python dependencies.

```powershell
# Inventory the available battlescape save headers:
.\build\local\laya-venv\Scripts\python.exe scripts/probe-battlescape.py --list

# Build the native harness, run three saves with three seeds and one exact repeat:
.\build\local\laya-venv\Scripts\python.exe scripts/probe-battlescape.py --build --seeds 1 7 23 1

# Select a different UFO battle (repeat --save for more):
.\build\local\laya-venv\Scripts\python.exe scripts/probe-battlescape.py --save 'build/local/user/xcom1/Dawn radi.sav'
```

The default snapshots are `Groudn baddle.sav`, `Ground mutons.sav`, and
`surrounded.sav`. They contain six, eleven, and five active original hostile
units, respectively. The current runner targets the UFO master (`xcom1`). It
rejects Geoscape saves and battles without usable UFO objective anchors.

Each invocation creates a new ignored `build/local/tactical-probe-*` directory:

- `REPORT.md`: counts and interpretation limits.
- `map.html`: per-level alien positions and proposed destinations for both arms.
- `manifest.json`: source/binary hashes, save integrity checks, status, and repeated
  result checks. A native failure remains a failure; it is not silently skipped.
- Per-save/seed folders: copied source, native log, options, and
  `xcom1/tactical-probe.json` with roles, coordinates, costs, and native route
  directions in reverse traversal order.

## What is compared

The **patrol probe** retains an existing destination when present. Otherwise it
uses the native `getPatrolNode` selection and pathfinder with the scout/guard
classification and five-attempt fallback used by ordinary UFO patrol behavior.
It does not call `AIModule::think`: attacks, morale, psi, interrupts, mode changes,
and full turn scheduling are outside this probe. Ascending unit ID is the probe's
processing order, not a claim about the live battle's next selection order.

The **shared defence** sorts aliens by proximity to objective anchors. It assigns
the closest two thirds to guard posts and the remainder to an outside screen.
Guard posts use guard-ranked UFO footprint nodes. Screen posts use outside nodes
within eight tiles of an anchor, preferring roughly four-tile distance and short
routes. Assignments respect native placement, movement type/size, fire, danger,
node reservations, exact path endpoint, energy, and current TU minus a fixed
12-TU reserve. The reserve is not a weapon-specific reaction-fire guarantee.
New destinations are separated by at least three tiles in 3D tile coordinates.
When no valid post exists the unit holds its current position. An assigned post
may already be the unit's current position; the report counts actual moves
separately. Node allocation and campaign RNG are restored between arms.

## Save/load discovery

`Node::save` and `Node::load` omit `segment`. Consequently the original UFO versus
terrain node provenance is unavailable after loading these saves. The scaffold
does not invent it or alter the save format. It uses the saved
`flattenedMapTerrainNames[x][y]` grid, whose craft/UFO entries are rule IDs, to
identify the UFO footprint. Nodes of rank two or greater within that footprint
are objective anchors. JSON labels this source explicitly; a footprint is not an
exact reconstruction of original route segments, especially across map levels.

## Interpretation and next gate

The initial test found assigned posts for 4/6, 2/11, and 2/5 aliens; only one alien
in each snapshot needed movement to its post. All assigned posts were guards:
no outer-screen assignment fit these constraints. This is a restrictive first
heuristic, not evidence of improved tactics.

These are saved mid-battle states, including partially spent alien TU on player
turns. Budgets are not refreshed. Stock patrol destinations may span multiple
turns; shared posts must fit the immediate budget, so the counts cannot rank
the two approaches. Seeds perturb patrol selection; they are not independent
battles. Repeated save/seed outputs must agree exactly, and shared assignments
must remain independent of the patrol seed.

The native probe checks serialized battle state and campaign RNG before and
after both arms. The runner checks hashes of original and copied saves even
when a native process fails. This protects source saves; it does not certify a
fog-of-war policy. The assignment scorer receives no enemy coordinates, while
native occupancy and pathfinding still inspect loaded battle state.

The map is a route-node diagram with straight start/destination connectors,
not a terrain rendering or movement animation. Cover quality, facing, mutual
support, overlapping paths, and movement execution remain untested. Fallback
holders can also obstruct earlier assignments. Original units remain in place
throughout planning.

The next experiment should compare node anchors with reachable tile candidates
and allow persistent destinations approached over several turns. Then wire orders
into native alien-turn execution with contact interrupts and save/load persistence.
Only after that should matched seeds and a fixed player policy be used to compare
mission outcomes against full stock AI. Model selection comes after executable
orders have been demonstrated.

Validation on 2026-11-02: native harness built with the x64 Visual Studio 2019
toolchain; twelve save/seed probes passed, including exact repeats; the Geoscape
negative case was rejected with save hashes unchanged. Existing engine suites
also passed (184 UFO and 173 TFTD checks). No live AI change, inference, commit,
or push was performed.
