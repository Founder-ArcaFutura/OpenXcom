# Conquest incentive probe: changes choices, does not establish a robust strategy

Thirty real local-checkpoint portfolios were produced from five frozen historical decision states (February–June), across three conditions and two PLAN option orders. All 30 are legal and fit the strict model limits; the largest packet is 475/512 tokens. Original source hashes and model/planner/experiment script hashes were independently rechecked. No saves, live prompts, engine mechanics, model weights or campaign outcomes were modified. No API calls were made. Eighty-four Python tests passed.

## Conditions

The preregistered [protocol](PROTOCOL.md) fixes the reward table and limitations. Baseline uses current shared v9 wording. Explicit-current changes only PLAN descriptions and a short common conditional-payout limitation, while retaining live rewards. Hypothetical uses that same format but proposes no research cash, research intelligence gains only below two, harvest/abduction +3 resources, and successful terror +6 resources/+2 local influence. Defeated terror earns zero; merely creating a site does not qualify. Costs, cash available now, legal menus, target packets, evidence, operation caps and pending missions are identical across paired conditions. Impossible infiltration geography is corrected equally in all arms.

The hypothetical scheme bundles several changes; this experiment cannot isolate research saturation, research cash removal, productive-mission pay, and terror reward effects from one another. The explicit-current comparison helps distinguish richer descriptions from proposed reward numbers, but cannot establish semantic understanding.

## Normal PLAN order

| Decision | Baseline | Explicit current rewards | Hypothetical rewards |
|---|---|---|---|
| February 1 | 3 harvest | Terror + 2 harvest | 2 terror + harvest |
| March 1 | 3 abduction | 3 harvest | 2 terror + harvest |
| April 1 | Harvest + 2 search + research | 2 harvest + 2 abduction | 2 harvest + 2 terror |
| May 1 | Abduction + 3 research | 4 harvest | 4 harvest |
| June 1 | 4 research | 4 harvest | 4 harvest |

June harvest targets in the raw receipts should be evaluated against interference evidence, not interpreted as proven safe economic investment. The TARGET prompt is deliberately unchanged, so this test does not add a regional political-vulnerability model or success odds.

## Reversed PLAN order

| Decision | Baseline | Explicit current rewards | Hypothetical rewards |
|---|---|---|---|
| February 1 | Harvest + 2 research | 3 harvest | 2 terror + harvest |
| March 1 | Save everything | Save everything | Save everything |
| April 1 | Save everything | Save everything | Save everything |
| May 1 | One abduction, then defer | Save everything | Save everything |
| June 1 | Research + 3 abduction | 2 infiltration, then defer | Search + 3 infiltration |

Exact full-portfolio agreement between the two tested orders is 0/5 baseline, 0/5 explicit-current, and 1/5 hypothetical (February). These are paired deterministic probes, not independent trials or estimates of statistical reliability. More stable choices would not automatically mean better play, and different sensible portfolios need not be failures; however, operation versus total deferral remains a material interface sensitivity.

Across both orders: baseline selects 11 research, 5 harvest, 8 abduction and 2 searches; explicit-current selects 18 harvest, 2 abduction, 2 infiltration and 1 terror; hypothetical selects 13 harvest, 8 terror, 3 infiltration and 1 search. Total spend across the ten fixed-state/order probes is 65, 76 and 91 respectively, from 216 available in each arm. These totals are descriptive only: more spending, terror, variety or agreement is not a conquest-quality score.

## Interpretation

There is evidence of responsiveness to the reward contract: the research-heavy normal-order June result disappears under explicit-current wording alone, and hypothetical rewards introduce terror into several earlier normal-order portfolios. A fixed research-only tendency is therefore not inevitable. But the hypothesis of balanced, sustained conquest is not demonstrated. May and June normal-order hypothetical choices are all harvest, June contains no terror in either order, and reversed March–May still defer everything. This could be a different preference basin or lexical/positional sensitivity rather than long-term planning.

The classifier is not training on these rewards. It remains the same career-trained checkpoint; only input descriptions change. In particular, these results do not prove that the native campaign would deliver the stated rewards, that terror has positive expected value, or that any chosen portfolio beats the live campaign.

All five recorded states lack logistics two, so direct base construction is unavailable throughout. Explicit harvest descriptions mention that gate. Infiltration becomes available in May and June and can establish a base, but no alternate mission outcome or resulting passive economy is simulated. There is no funded base-assault action. These constraints remain part of the restricted strategic space.

## Next step

Keep this scheme offline. A useful next test is a component ablation (research cash removal alone, research saturation alone, terror reward alone) over several fixed option permutations, including the observed June state. Check harvest-to-base preparation and political investment, and preserve target-risk evidence. Select a candidate for native outcome implementation only after that comparison; do not tune repeatedly until it happens to select terror or force a mission quota.

Once a candidate is implemented, compare actual delivered objectives and political/economic trajectories. The current five snapshots belong to one observed campaign, not a sequential counterfactual campaign. A changed February could invalidate every later observed state as a prediction of that alternate history.

Raw decision states, criteria, probabilities and source/model manifests: build/local/conquest-incentives-v1/<decision-month>/. Machine-readable summary: [results.json](results.json). Engine and live service remain v9.
