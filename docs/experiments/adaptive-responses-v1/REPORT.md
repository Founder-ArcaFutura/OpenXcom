# Matched adaptation diagnostics

Completed 17 October 2026. The commander responds to some changed facts, but these probes do not demonstrate a reliably adaptive strategic policy. Presentation remains a material determinant of its choices. No reward buffs or live campaign changes were made.

## Results

Each cell below is one first investment choice, or one target choice conditional on a forced harvest objective. A and B are balanced cyclic ordering families with disjoint permutation orbits. They are robustness checks, not independent training seeds or campaign trials.

| Intervention | Family A | Family B |
|---|---|---|
| Eight assigned losses in Australasia: harvest target | Australasia | Australasia |
| Same eight losses moved to North America | Australasia | Australasia |
| Logistics 1, compressed reward labels | Harvest | Harvest |
| Logistics 2, same labels; native base options unlocked | Base | Infiltration |
| Logistics 1, additional named capability context | Abduction | Abduction |
| Logistics 2, additional named capability context | Abduction | Abduction |
| One preparation scout lost; objective wave pending | Harvest | Harvest |
| One objective carrier lost; no further objective wave | Harvest | Harvest |

**Location: partial score response, no demonstrated retargeting.** Australasia's mean score fell from 0.2374 to 0.1782 in A, and 0.2394 to 0.1823 in B when the losses moved there from North America. It nevertheless remained first. North America's own loss penalty was inconsistent: its score increased slightly in A (0.0948 to 0.0972) and decreased in B (0.0961 to 0.0843) when it received the losses. Assignment losses are uncertain clues, and the fixture supplies neither survival odds nor expected utility; avoiding a particular region is not an established optimal answer. HARVEST itself was forced for this diagnostic and earns no model-selection credit.

**Capability: partial response, presentation-sensitive.** The native engine produced 56 versus 68 legal mission-region candidates, adding 12 base candidates at logistics two. Cash, other capabilities and observations were identical. Base absence below the threshold is engine enforcement, not model judgment. Under compressed labels both families changed from harvesting to a conquest investment after unlock, but disagreed between base and infiltration. Adding named capability context instead produced abduction at both levels. This additional context changes both state representation and harvest wording; it does not isolate one individual wording effect. Different option counts also prevent treating score changes as calibrated absolute preference gains.

**Operational role: no demonstrated change in first investment.** Both families chose harvest under both loss roles. Scores changed modestly; unchanged argmax does not prove the model ignored the evidence. The rendered packet contains the role counts and pending-objective count, but not all native per-craft support or wave details. Neither variant asserts that an entire terror operation failed. The DTO cannot currently carry verified whole-objective defeat, so that stronger test remains unavailable.

## Provenance and checks

- Eight diagnostic inputs, two families each: 116 component evaluations, comprising 88 new CPU inferences and 28 exact ordered-packet cache reuses. Fixed supplied career-domain checkpoint, not fine-tuned for XCOM. Zero paid API calls. Maximum observed packet length 460 tokens.
- Native preparation used a copied Pre-Junes save and a scripted SAVE response to cross the boundary without new funded missions. Logistics variants were exported by the native engine. These are synthetic controls, not alternate observed player histories or full learned portfolios.
- Input contract validation, intended-difference checks, aggregate recomputation and original source hash verification passed. Original Pre-Junes SHA256 remains `d095e3dd2850ee74751309d8a7570356aff20577b12916b434a3345f296d3ec7`. All 100 Python tests passed; diff whitespace checks passed apart from an existing line-ending warning.
- The first attempt's eight-option reward packet exceeded the fixed model token budget. Partial results remain in `build/local/adaptive-responses-v1`; the preregistered amendment uses consistently compressed PLAN reward labels in `build/local/adaptive-responses-v2`. No truncation or reward changes were used. TARGET receipts are identical and reused. These compressed labels are experimental, not installed live.
- Synthetic role support is marked as explicit telemetry to exercise the schema, but is fabricated for the diagnostic, not actual engine-observed loss evidence. Whole-mission outcomes remain unknown.

## Files and next step

[scores.csv](scores.csv) contains all aggregate option scores, votes and winners; [component-scores.csv](component-scores.csv) retains each ordering's scores. [results.json](results.json) records summary vectors, interventions and checkpoint/source/script hashes. Raw input, exact rendered packets and component receipts remain in `build/local/adaptive-responses-v2`. The initial failure and native preparation logs are retained separately.

Do not adopt an incentive buff from this result. First define a compact, stable operational context that fits every legal menu, and test it on held-out states. Add explicit verified objective outcomes before testing learning from defeat. If presentation robustness improves but useful conditional behavior remains weak, these matched cases can become training/evaluation examples with separate held-out cases. Actual strategic quality and playability still require executed campaign comparisons.
