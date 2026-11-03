# Human playtest: perimeter defence and a stationary interior guard

Preserved on 2026-11-02 from isolated session
`tactical-session-20261102-193021-461`. The starting checkpoint was
`Three off the ramp.sav`; the participant saved the completed run as
`Test complete.sav`. Original session files were copied and hash-checked without
alteration. The implementation was uncommitted when this evidence was collected.

## Finding

This run demonstrates a narrower but useful capability: the scripted aliens
formed and retained a perimeter around their UFO, with interior guard assignments,
instead of continuing ordinary map patrols. Their persistent destinations remained
meaningful across several turns. On contact, at least one travelling guard yielded
to native fighting and movement behavior.

The participant's assessment was that the aliens "formed a perimeter and attempted
to defend the UFO" rather than patrolling various map sectors. This is participant
observation, supported by the recorded orders and positions. It is not evidence of
model learning, optimal defence, deliberate covering fire, or improved win rate.

## Preserved segments

| Segment | Turns | Records | Last event |
|---|---|---:|---|
| [First capture](captures/tactical-17936658222308450.jsonl) | 1–4 | 168 | `STATE_RESOLVED` |
| [Second capture](captures/tactical-17936658869354966.jsonl) | 4–7 | 228 | `BATTLE_FINISH` |

These are two battle-load segments, not one uninterrupted replay. The overlap at
turn 4 must not be counted as independent combat evidence or simply concatenated
into a single timeline. There are 396 raw records across the retained segments.

The participant was testing a prepared defence: waiting before advancing, then
playing more normally/aggressively. That description is participant-reported;
there was no frozen player policy or matched human control trajectory. Observer
vision was enabled, native debug mode disabled, and the scripted defence option
enabled. No learned model selected tactical orders in this test.

The completed segment ends with 13 active XCOM units and no active hostile units,
from 14 and five respectively at its start. This run establishes the observed
positioning and persistence, with the alien force ultimately overcome. It does
not establish increased difficulty or a higher alien win rate.

## Concrete observations

- Unit 1000000 held the interior post `[15,17,0]` under order `1000000:1`.
  Its captured AI decisions were `NONE / HOLDING`; it remained facing direction
  2 (east) through its turn-5 decisions and had empty cached visible-contact lists.
  It selected no active combat action before being killed. This does not by
  itself exclude every possible reaction-fire event.
- Unit 1000002 retained a multi-turn guard destination at `[14,13,0]`. On turn 4,
  contact suspended that order and native AI selected movement and a snapshot,
  followed by further movement. This demonstrates a working interruption in that
  case, not universal interruption correctness.
- Perimeter units held posts rather than repeatedly selecting new patrol sectors.
  Raw event snapshots retain their positions, facing, TU, role, order revision,
  contacts, and health for inspection.

The interior guard is an important limitation alongside the positive perimeter
result. Current `HOLDING` behavior specifies a coordinate but lacks a watch sector,
TU-costed scanning, and explicit reassessment after a nearby breach or casualty.
A useful position can therefore become a passive or poorly oriented guard post.
Preserve this case as a regression target before changing that behavior.

## Evidence and reproduction boundary

- [Derived decision and unit summary](summary.json) is recomputable from the raw
  captures. Empty cached contacts are not a complete reconstruction of native AI
  knowledge, which can also include sharing, memory and special mechanics.
- [Provenance](provenance.json) records source hashes, Git HEAD, captured files,
  and the exact list of snapshotted implementation files.
- [Archive seal](archive-seal.json) identifies the local ZIP and SHA-256 digest.
  The complete local package contains initial/final/autosaves, both raw captures,
  session options and launch script, native log, a standalone viewer, current
  executable/dependency DLLs, and a snapshot of the uncommitted implementation.
- Original-game resource assets are not bundled. The existing native runtime's
  resource staging is still required to execute the game.

The executable and source copies were captured after the playtest. A capture-time
executable hash was not recorded, so the post-run binary snapshot must not be
presented as an independently attested capture-time identity. The session flags,
protocol, native records and post-run source snapshot are retained separately.

The archive is local, and this report/evidence remains uncommitted. Preservation
does not imply publication or permission to change the captured run.
