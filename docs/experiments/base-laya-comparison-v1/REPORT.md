# Publisher-base Laya versus career-tuned Laya

Completed 17 October 2026. **The publisher's English base checkpoint chose the same option as the career checkpoint in 31 of 32 aggregate decisions.** It reproduced the loss-region targeting pattern and the sensitivity to capability presentation. Swapping checkpoints did not resolve the strategic-judgment problem in these diagnostics.

This revises the earlier hypothesis: career-specific relevance training is not necessary for the observed behavior to occur. The result does not identify an internal mechanism or establish that Laya cannot make useful strategic decisions. Common model training, representation, question wording, choice keys, runtime and missing decision-relevant information remain possible contributors.

## Model and controls

Downloaded the publisher's [English root checkpoint](https://huggingface.co/convaiinnovations/laya/tree/7b928d828b7b0e022f929d9bd2e44165aa270148), pinned revision `7b928d828b7b0e022f929d9bd2e44165aa270148`. Its model card describes a ModernBERT-large decision model; this is a general-purpose decision checkpoint, not an untrained encoder. The publisher also cautions about limited zero-shot decision performance and the need for domain evaluation. Those publisher benchmarks are not XCOM evidence.

- Base weights SHA256: `891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c`, 842,609,210 bytes; verified against publisher LFS metadata.
- Career comparator SHA256: `bcbb891d21cf081a9d7a941b97f8b0f10cf3dac7473b4b9450fab0d07b885175`.
- Both use the same installed Laya 0.1.6 runtime, Torch 2.10.0+cpu, four CPU threads and pinned ModernBERT architecture/tokenizer metadata. Encoder, head layers, 512-token context, 192-token head budget and temperature configurations match exactly. Base weights loaded with strict architecture checks. This deliberately holds the runtime fixed rather than testing the newest SDK.
- Replayed the exact ordered packets from compact-command-v1 and adaptive-responses-v2: 16 diagnostic cases, two ordering families each, 32 aggregate decisions, **238 new base-model component inferences**. Career scores come from existing receipts. Every paired packet hash, option order and token count matched; no rewritten prompts, selected permutations, truncation or reward changes.
- All packets were preflighted before prediction; maximum sequence length 460 tokens. No inference failures or paid inference/API calls.

The published base has not been established as the exact ancestral checkpoint of the career model. This is a checkpoint comparison, not a controlled causal ablation of career fine-tuning.

## Results

| Suite | Same choice across checkpoints | Base A/B agreement | Career A/B agreement |
|---|---:|---:|---:|
| Compact briefing | 15/16 aggregates | 8/8 cases | 7/8 cases |
| Earlier matched adaptation | 16/16 aggregates | 7/8 cases | 7/8 cases |

These counts are descriptive robustness measures, not accuracy or independent campaign samples. The paired synthetic states and ordering families are correlated by design.

**Harvest targeting:** In the compact contract both checkpoints choose Europe when Europe has the five assigned losses, and North Africa when the losses move there. Base winning margins remain substantial: 0.5427–0.6224 versus career 0.6400–0.6998. These are uncalibrated classifier score gaps, not estimated probabilities of mission success. The model follows the interference-bearing region rather than demonstrating risk avoidance for this harvest objective. In the earlier representation both checkpoints instead retain Australasia, including when eight losses are assigned there. Within each pair only the assigned-loss region changes; across suites the representation, labels and scenario also differ, so these results cannot isolate one wording effect.

**Progression:** In the compact adaptation/infiltration gate pair, both choose base construction at either adaptation level. In the earlier logistics/base pair, both choose harvest below the gate; above it family A chooses base and B infiltration. Adding named capability context to that earlier packet produces abduction at both levels in both checkpoints. Base absence below the gate is engine/contract enforcement, not model judgment. An unlocked investment is optional; choosing a different legal investment is not inherently a failure.

**Operational outcomes:** Both retain terror under the compact scout-loss, disrupted-objective and completed-objective categories. The single cross-checkpoint disagreement is UNKNOWN outcome in family B: base chooses terror (margin 0.01556), career chooses base search (margin 0.00450). The base is more consistent across these two families on this case, but no campaign evidence demonstrates that its choice is better. In the earlier role/pending-wave pair both checkpoints choose harvest regardless of lost craft role.

The rule reference and synthetic outcome limitations remain unchanged. Agreement with that policy is not ground-truth accuracy. Whole-objective outcomes in the compact cases are fabricated explicit receipts, not actual native telemetry. No full portfolios or alternate campaign trajectories were executed.

## Artifacts and validation

- [choices.csv](choices.csv): all 32 paired aggregate choices and margins.
- [scores.csv](scores.csv): full aggregate base/career score vectors.
- [component-scores.csv](component-scores.csv): each ordered component's paired scores and packet hash.
- [results.json](results.json), [checks.json](checks.json): checkpoint/source/script provenance and recomputation checks.
- Raw receipts and frozen source hashes: `build/local/base-laya-comparison-v1`.
- Downloaded checkpoint, model card, config and download receipt: `build/local/base-laya-checkpoint`.

Analysis recomputed aggregate means, votes and winners; checked exact component pairing and tokenization; verified downloaded weights and source/script hashes. All 102 Python tests passed. Diff whitespace checks passed with an existing line-ending warning. The original Pre-Junes save, career staging weights, live planners and native executable were not changed. The live commander still uses its previous checkpoint.

## Implication

Do not interpret the earlier loss-region behavior as evidence specifically against career tuning: the publisher base exhibits it too. The next branch should target the distinction between identifying relevant evidence and evaluating an action's consequences. Domain training remains a hypothesis to test, not a demonstrated remedy; prompt/key controls or an alternate decision model could help distinguish the remaining explanations. Preserve these scenarios as development diagnostics and reserve separate untouched evaluation cases before training. No live checkpoint switch is supported by this comparison.
