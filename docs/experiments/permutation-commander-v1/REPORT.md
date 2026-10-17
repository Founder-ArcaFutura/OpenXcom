# Permutation-mean commander: less complete deferral, residual family sensitivity

Completed 25 offline portfolios from five recorded February-June states. All use explicit descriptions of existing native rewards, with no reward buffs. Three single-order controls are compared with two balanced cyclic permutation families. All portfolios are legal; no input-limit failure occurred (maximum 469/512 tokens). Original saves and model/planner/runner scripts were hash-checked unchanged. No live commander, native rule, checkpoint weight or campaign state was changed.

## Result

Both aggregate families choose operations in all five states and fill the available operation slots. In the same explicit-current controls, reversed order defers everything in three states and seeded order in one; canonical order already operates in all five. This is a useful mitigation of the observed execution/deferral split. It does not prove that acting is always better than deferring.

The two aggregate families agree on the first mission type in 4/5 states, but on the exact full portfolio, unordered operation set and mission mix in only 1/5 (March). February differs by harvest versus terror; April-May-June differ by harvest versus abduction. Every action occupies every position in both families, so balancing marginal position does not remove all ordering/context interactions.

Family A reproduces the canonical single-order control's unordered operation set in all five states (February has a different creation order). Thus it is not selecting a demonstrably better portfolio than the favorable canonical control; it provides a different procedure whose outcome is less dependent on one presentation order in the tested deferral cases. Family B is not chosen after inspecting its results.

## Monthly mission mixes

H=harvest, A=abduction, T=terror, S=base search, I=infiltration. SAVE means complete deferral. These are commitments in offline model output, not actual executed or successful missions.

| Decision | Canonical single | Reversed single | Seeded single | Aggregate A | Aggregate B |
|---|---|---|---|---|---|
| 1999-02 | 1T + 2H | 3H | 2S + 1T | 2H + 1T | 1H + 2T |
| 1999-03 | 3H | SAVE | 3H | 3H | 3H |
| 1999-04 | 2H + 2A | SAVE | 2S + 2A | 2H + 2A | 3A + 1H |
| 1999-05 | 4H | SAVE | SAVE | 4H | 3H + 1A |
| 1999-06 | 4H | 2I | 2S + 1I + 1A | 4H | 3H + 1A |

## Spending and complete deferral

Each arm sees the same five fixed budgets, totaling 108 resources. More spending or mission diversity is not a conquest-quality metric.

| Arm | Complete deferral | Operations selected | Resources spent |
|---|---:|---:|---:|
| single_canonical | 0/5 | 18 | 55 |
| single_reversed | 3/5 | 5 | 21 |
| single_seeded | 1/5 | 14 | 40 |
| aggregate_A | 0/5 | 18 | 55 |
| aggregate_B | 0/5 | 18 | 56 |

Aggregation does not solve excess banked resources or establish strategic pressure. June still retains 18 of 30 resources after spending 12 and filling all four slots. Neither aggregate chooses infiltration in these states, and neither selects terror in May or June. Harvesting could prepare the missing logistics prerequisite, but a subsequent move into bases is not simulated. Direct bases remain unavailable in all supplied states, and a separate funded base assault remains unavailable.

## What was averaged

For each PLAN decision, family A evaluates all rotations of canonical IDs; family B evaluates all rotations of a deterministically shuffled ordering outside A's cyclic orbit. For identical options with at least three actions, the families have disjoint ordered-packet sets. Each action, including SAVE, occupies every position once per family. The mean returned score for each stable action ID determines the choice; exact ties use sorted stable IDs. TARGET decisions retain their original order. No quota, spend minimum or new abstention threshold is imposed.

These scores are uncalibrated. Arithmetic averaging is a policy heuristic, not an estimate of mission success or expected utility. Within-family invariance from reusing the same full rotation set is mathematical; only agreement across the distinct families is an empirical sensitivity check. One separate family is not a broad sample of all n! orders or unseen campaign states.

## Component disagreement and small margins

Only 4 of 36 aggregate PLAN decisions have the same winner in every component permutation. February's first decision is close between harvest and terror: A's mean-score gap is 0.003850; B's is 0.000567. In April the first mission type differs (A harvest, B abduction). These are score gaps, not confidence or error probabilities. The raw components must remain visible if aggregation is ever used live.

## Compute and latency

- 211 new local model inferences, 2 uncached automatic singleton decisions and 128 exact ordered-packet decision reuses.
- About 8 minutes of measured portfolio evaluation on the existing CPU runtime, excluding checkpoint loading. No API calls or GPU/runtime installation.
- A cold aggregate portfolio here requires 18-32 model calls, versus roughly 6-8 for a filled single-order portfolio. CPU game latency would materially increase. May A took about 61 seconds despite 8 cache reuses; June B about 63 seconds despite 4. These are offline timings, not measured in-game performance.
- Prior records reused as exact controls/components are not independent model samples. Cache identity includes state, ordered criteria and instructions; checkpoint and live code fingerprints are checked.

## Recommendation

Keep reward buffs offline. Retain explicit native outcome descriptions and permutation aggregation as experimental candidates: aggregation reduced the extreme deferral sensitivity on these snapshots, but did not establish reliable final portfolio selection or sustained conquest pressure. A bounded next check could measure convergence across additional disjoint families on the ambiguous February and April states, while reviewing target-risk choices separately. Do not select a family merely because it produces more terror or spending.

Any later live trial should expose component disagreement and account for CPU inference staging/latency. It should evaluate actual delivered harvests and whether unlocked base construction is then used, rather than assuming these fixed snapshots predict an alternate campaign. This test alone does not justify claiming the commander has learned strategic judgment.

## Saved tables and provenance

- [Portfolio table](portfolios.csv): all 25 rows with spend, remaining resources, mission mix, first PLAN choice and smallest aggregate margin.
- [Component score table](component-scores.csv): all 341 evaluated/reused/automatic components, ordered action IDs, scores, aggregate choice, source and cache origin.
- [Detailed results](results.json): arm totals, family agreement and validation.
- [Preregistered protocol](PROTOCOL.md). Raw full questions, criteria, component receipts and source/model manifests: build/local/permutation-commander-v1/<month>/.
- Runner: scripts/test-permutation-commander.py. Analyzer: scripts/analyze-permutation-commander.py.
- 94 Python tests passed, including position balance, family disjointness, ID-aligned means, SAVE eligibility and rejection of invalid component scores. Every stored aggregate mean/vote/margin was independently recalculated and verified.
