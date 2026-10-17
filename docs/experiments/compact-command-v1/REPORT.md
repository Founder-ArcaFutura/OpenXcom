# Compact briefing and rule-reference probe

Completed 17 October 2026. The compact contract fits comfortably and A/B families agree on seven of eight cases. This does not establish useful strategic judgment: harvest targeting follows the region with assigned losses, and explicit objective categories do not produce a differentiated investment choice. These results do not justify another layer of advisors or a live rollout.

## What was implemented

`scripts/compact_command_probe.py` defines an experimental briefing with named capabilities, prerequisites, commitments, regional interference, reviewed operation/outcome, cash/carry and common reward uncertainty/timing. Fixed action labels state native costs and conditional consequences. It also implements a frozen transparent reference policy using the same rendered information and legal option set. No reward values were changed.

Outcome source records distinguish UNKNOWN, SCOUT_LOST, DISRUPTED and COMPLETED. Disrupted denotes an explicitly verified prevented objective; completed denotes a verified delivered objective, not campaign victory. Non-unknown records require evidence. The model sees the category and reviewed operation, not a reasoning narrative or provenance identifier. No observed campaign supplies verified whole-objective receipts: these categories are synthetic contract tests. The default adapter returns UNKNOWN and never manufactures objective defeat from disappearing craft. **Native objective-receipt emission and live planner wiring are not implemented by this experiment.**

New scenario regions and a different progression gate were frozen before inference. These are researcher-designed holdouts from earlier examples, not a blinded benchmark or independent campaign sample. No packet wording was revised after observing results.

## Decisions

| Synthetic scenario | Laya family A | Laya family B | Rule reference |
|---|---|---|---|
| Harvest target; five assigned losses in Europe | Europe | Europe | Australasia |
| Same losses moved to North Africa | North Africa | North Africa | Australasia |
| Adaptation 1; infiltration unavailable | Base | Base | Base |
| Adaptation 2; infiltration available | Base | Base | Base |
| Previous terror outcome unknown | Terror | Base search | Base |
| Previous terror: scout lost, objective outcome unspecified | Terror | Terror | Base |
| Previous terror objective explicitly disrupted | Terror | Terror | Harvest |
| Previous terror objective explicitly completed | Terror | Terror | Base |

### Responsiveness versus quality

**Location: strong responsiveness, questionable investment interpretation.** The selected target follows the changed loss location in both families. Top-to-second score gaps are 0.6400–0.6998, although these are uncalibrated classifier scores, not success probabilities. This contrasts with the reference's explicit preference for less assigned interference. The reference's Australasia answer follows alphabetical tie-breaking among zero-loss regions, not proof that Australasia is safe or optimal. These inputs offer uncertain assignment losses, not interception rates, expected utility or enemy base coordinates. Deliberately entering a contested region can be strategically justified; the probe provides no explicit reason to do that for a capacity-seeking harvest.

The pattern is consistent with selecting the region most salient in the briefing, but this experiment cannot establish the internal mechanism. The new contract also changes wording and option identifiers relative to earlier experiments; cross-experiment differences cannot be attributed to named capabilities alone. Within this location pair, only the loss region changes.

**Capability: legal and consistent, but no demonstrated gate-driven change.** Both model and rule select base construction on both sides of the adaptation/infiltration threshold. Bases were already available at logistics two. Infiltration becomes a legal additional choice, not a required gold answer. Its absence below the threshold is a contract gate, not model intelligence. This probe filters the existing native-exported candidate menu using the documented adaptation prerequisite; it does not claim a fresh native-engine replay of this gate. Different option counts also confound direct probability comparison.

**Outcomes: no distinct investment response demonstrated.** Both families choose terror after scout loss, disruption and completion. Scores do respond: terror's winning gap is largest after completion (A 0.5285, B 0.3827), compared with disruption (A 0.3847, B 0.2099). The unknown-outcome case disagrees across families, with B's base-search lead only 0.0045. Repeating terror after a setback or success is not inherently irrational. These results demonstrate neither that outcomes were ignored nor that the model has learned useful lessons. Outcome categories are short semantic labels, not a detailed account of losses, survival odds or the cause of disruption. Their semantics are an experimental contract, not established domain training.

The reference fills missing capability tracks, avoids duplicating commitments, then prefers persistent conquest investments. For disrupted objectives it favors rebuilding. Those are declared design choices rather than expert labels, so matching it is not an accuracy measure. It too makes unchanged choices across several interventions. There is no utility score or claim of optimal play.

## Validation and artifacts

- 8 scenarios × 2 ordering families = 16 aggregate decisions; 122 new local CPU component inferences. Same career-domain checkpoint SHA256 `bcbb891d21cf081a9d7a941b97f8b0f10cf3dac7473b4b9450fab0d07b885175`; no domain fine-tuning or API calls.
- Every packet passed a full token-budget check before prediction. Maximum observed sequence length 319, below 512. No silent truncation or inference failures.
- All 102 Python tests passed. Tests cover receipt requirements, default unknown outcomes, intended pair differences, capability legality and reference output membership. Analysis recomputed aggregate means/votes/winners and verified component orderings, script/source hashes and original Pre-Junes hash. Diff whitespace checks passed with an existing line-ending warning.
- Original save unchanged: `d095e3dd2850ee74751309d8a7570356aff20577b12916b434a3345f296d3ec7`. No live prompts, engine executable, missions, rewards or campaign state were modified. No full portfolios or campaign trajectories were generated.
- [scores.csv](scores.csv): all aggregate scores and votes; [component-scores.csv](component-scores.csv): each permutation score and packet hash; [results.json](results.json): choices, interventions' case identifiers and provenance; [checks.json](checks.json): recomputation summary. Full synthetic source inputs, packets, rule decisions frozen before inference and raw receipts are in `build/local/compact-command-v1`.

## Recommendation

Keep this compact contract as an offline candidate, and stop adding advisors for now. The loss-region targeting pattern is a concrete diagnostic for a domain-training or alternate-model branch. Before training, preserve these cases as development examples and create a separate untouched evaluation set; do not train on them and then report them as held out. Compare against the transparent rule policy without treating it as ground truth. Real objective receipts and executed campaign comparisons remain necessary to test whether either approach produces an adaptive, playable opponent.
