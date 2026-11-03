# Observe and record alien turns

Observation defaults to stock AI. Add `-Defend` to the isolated launcher for the
separate [persistent UFO defence experiment](DEFEND_AREA_EXPERIMENT.md).

The development engine supports two independent opt-in flags:

- `-tacticalTelemetry true`: write an omniscient JSONL capture for each battle
  load, including battles created by landing from a Geoscape save.
- `-tacticalObserver true`: show terrain and all units on the main tactical map,
  suppress hidden-movement masking, and follow hidden alien movement. This is
  a display override. It does not enable native debug/manual alien control or
  set tile discovery, unit visibility, or AI knowledge.

Use a separate session for human play with revealed information. The observer
affects the human player's decisions and presentation speed, even though the
tested native decisions and results remain unchanged. The minimap and player
target-selection rules retain their normal behavior.

## Start an isolated inspection session

From `G:\OpenXcom`:

```powershell
.\scripts\run-tactical-inspection.ps1 -Save 'build/local/user/xcom1/Three off the ramp.sav' -Launch
```

The launcher copies the source into a new `build/local/tactical-session-*` folder,
creates a `launch.ps1`, and opens `inspection-start.sav` automatically. Its saves,
options, screenshots, and captures stay in that session. The original source is
hashed before and after. Original saves are never passed to the game as its user
directory. Omit `-Launch` to prepare the session without opening a window.

Pass any pre-landing Geoscape save instead to inspect a new battle from its
beginning: load, land, equip, and play normally. No campaign reset is required.
`-Game TFTD` selects the other master; tactical parity tests currently use UFO
saves, while the existing engine suites pass for both masters.

The isolated launcher disables monthly model execution and retains the saved RNG
on load. Keep the session focused on the landing/battle; advancing months in this
copy uses the ordinary scheduler. It creates a separate capture every time a
battle is loaded, so reloading is not mistaken for an uninterrupted timeline.
`-NormalVision` keeps recording on but uses ordinary fog and hidden movement.

For the existing development campaign, `scripts/run-local.ps1` also accepts
`-TacticalTelemetry` and `-TacticalObserver`, including alongside `-Portfolio`.
That route uses the usual development user directory; the isolated launcher is
preferred for experiments.

After a game launched with `-Launch` closes, the wrapper builds a standalone
`review/index.html`. To rebuild the viewer while a game is running or after
reopening its `launch.ps1`:

```powershell
.\build\local\laya-venv\Scripts\python.exe scripts/view-tactical-telemetry.py `
  --capture-dir 'build/local/tactical-session-<timestamp>/xcom1' `
  --out 'build/local/tactical-session-<timestamp>/review'
```

Open the resulting `index.html` locally. No server, model, account, or network
connection is required. The viewer includes capture selection, event stepping,
side-boundary navigation, level selection, unit selection, movement trails,
requested targets, patrol destinations, visible-contact lists, and raw records.
`summary.json` counts events, actions, and reported state-result messages. The
viewer omits an interrupted final JSONL line with a warning; corrupt complete
records fail visibly. A session ending without a finish hook is marked partial.

## Capture contract

Each record contains a sequence number, mission, turn, active side, RNG state,
observer/debug/native-cheating flags, and snapshots of all units: faction and
original faction, position, facing, status, health, stun, morale, TU, energy,
player visibility, cached visible-unit IDs, AI mode, and from/to patrol nodes.
Side codes are player 0, hostile 1, neutral 2. AI modes are patrol 0, ambush 1,
combat 2, escape 3; -1 means no AI module.

Events are:

| Event | Meaning |
|---|---|
| `BATTLE_OPEN` | Native battle controller constructed; includes terrain and route nodes |
| `SIDE_END` | Immediately before native side transition, after preceding queued turn-end effects |
| `SIDE_START` | Immediately after native side transition; turn-screen hooks may still follow |
| `SIDE_READY` | NextTurn constructor completed its environmental/reinforcement hooks |
| `AI_DECISION` | Final proposed action from `handleAI`, before action-state scheduling |
| `MOVE_STEP` | A native movement step reached standing status, before remaining post-movement effects/reactions |
| `STATE_RESOLVED` | A queued battle state completed `deinit`; later states may still resolve effects |
| `BATTLE_FINISH` / `BATTLE_ABORT` | The corresponding battle finish hook was entered; does not by itself identify the winner |

Test captures additionally contain `TEST_RENDER_CHECK` and `TEST_COMPLETE`.

Proposal records include actor, action code/name, target, weapon type, facing and
final-action flags. Resolved-state records include the state's result message;
they do not dereference potentially consumed weapon items. These are native
facts, not generated tactical explanations. Empty result text does not prove a
hit, successful movement, or objective completion. Health/position changes in
later snapshots provide the observed effects, without causal attribution.

Terrain is exported at battle open and side boundaries as sparse arrays
`[x,y,z,mask,smoke,fire]`; mask bits are floor 1, west wall 2, north wall 4, object 8.
The viewer is a schematic map, not a rendering of cover strength. Terrain changes
between those snapshots are not reconstructed. Route nodes include ID, position,
rank, patrol desirability, and links. Original node segment IDs remain absent
from legacy saves, as described in [the destination scaffold](BATTLESCAPE_PROBE.md).

Cached contacts are not all information available to native AI: native sharing,
memory, psi and cheating behavior still apply. The omniscient capture is never
fed back to the AI. It does not call target selection, FOV recalculation, or RNG
generation. File failures warn in the native log and stop capture while gameplay
continues. Writes flush per record; reloading creates another file.

## Validation and next experiment

```powershell
.\scripts\setup-local.ps1
# Rebuild/link the harness using existing real-engine objects:
& 'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe' `
  tests/AlienCommandTests.vcxproj /p:Configuration=Release /p:Platform=x64 /p:PreferredToolArchitecture=x64
.\build\local\laya-venv\Scripts\python.exe scripts/test-tactical-telemetry.py `
  --save 'build/local/user/xcom1/Muton madness.sav'
```

This machine's PDB manager reported a toolchain mismatch during compilation.
Successful builds used process-scoped `_CL_=/Z7` and `_LINK_=/DEBUG:NONE`, restored
afterward, to embed compiler debug information and avoid that PDB-manager path.
No global toolchain configuration or dependency installation was changed.

The native turn harness uses real movement, attack, reaction and turn machinery
on disposable copies. XCOM holds its turn. An accelerated, fixed animation/draw
cadence advances doors and explosion flashes; presentation overlays are dismissed
by the test. This is one native alien phase, not autonomous campaign play or an
exact reproduction of interactive wall-clock timing.

Six UFO snapshots, including a turn-one landing-site save, were compared with
observation off, telemetry only, and telemetry plus observer rendering. All
eighteen runs matched their paired final
serialized battle state and RNG. Cases included patrols, movement steps, snapshots
and aimed shots. Original saves remained unchanged. The existing native engine
suites passed 184 UFO and 173 TFTD checks. Observer screenshots were rendered and
inspected. Local browser control was disabled, so replay-viewer interactions
could not be checked in a browser; its JavaScript is syntax-checked.

The default records stock tactical behavior. The optional defence experiment
adds scripted orders; neither mode introduces a learned tactical policy. A useful next collection is a
fresh landing through first contact and several hostile turns, followed by the
same inspection of persistent scripted orders on a separate copy.
