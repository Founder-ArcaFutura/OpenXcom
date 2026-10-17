# Mission outcomes: implemented mechanics and proposed planner contract

This document separates facts from forecasts. The engine already implements costs,
conditional completion rewards and progression gates. The live v9 PLAN packet
primarily contains a purpose label/cost, recent lessons and cash constraints; richer
pros/cons are stored as receipt metadata but are not sent when `tradeoffs=False`.
The reference LLM briefing received more explicit mechanics than the classifier.
An optional full objectives-summary prompt was tested and did not improve behavior.
That experiment is not the live policy.

## Current implemented effects

| Mission | Cost now | Conditional delivered outcome | Custom next-month resource reward | Persistent progression |
|---|---:|---|---:|---|
| Research/probe | 2 | Verified native flight completion | +1 | Intelligence +1 |
| Harvest | 3 | Verified native productive activity | +2 | Logistics +1 |
| Abduction | 3 | Verified native productive activity | +2 | Adaptation +1 |
| Base search/retaliation | 2 | Nearby-base discovery under native scanning rules | None | No numeric progression; assault unavailable |
| Terror/surface attack | 4 | Native objective/activity/political pressure if delivered | None | No custom progression; no terror -> infiltration link |
| Infiltration | 6 | Possible country pact and alien base under native completion rules | Resulting bases earn income; pact itself has no recurring income | Resulting bases earn progression and local influence |
| Standalone base | 6 | Native base establishment | Surviving bases earn 1–2/month; delivered supply +1 pending | Quarter-point each track/base-month; local influence |

Resource/progression rewards are conditional, once per funded parent over its lifetime.
Multiple completion facts from the same parent do not multiply that reward. Resource
bonuses are capped when credited at the next monthly boundary; progression increments
persist. Returned craft and missing completion facts are not a whole-mission verdict.

Standalone base gate: month >=1 and logistics >=2. Infiltration gate: month >=2,
adaptation >=2 and intelligence >=1. More intelligence is not a supplied infiltration
success-probability modifier. These gates are not proof of eventual objective delivery.

## Native infiltration feasibility patch

The portfolio menu now excludes infiltration regions whose effective mission region
contains no static country label, using the same `insideRegion(labelLon,labelLat)`
geography convention as native infiltration. This excludes standard Antarctica.
Effective mission-region aliases are resolved before this check. Country-area overlap
alone is not enough: native completion uses the label point.

`executeAlienPortfolio` rebuilds that menu and validates the whole proposed portfolio
against it before reserving funds, consuming mission RNG or creating missions. A stale
or invented excluded infiltration choice therefore rejects the whole portfolio.
This is a native portfolio boundary guarantee, not a universal patch to stock event
schedulers. Existing saved missions are not rewritten or cancelled.

Scope deliberately limited: it guarantees a geographically possible country, not
that a country currently accepts infiltration, that terrain/base spawning succeeds,
or that craft survive. Native completion retains those dynamic checks. No hidden
player location, technology, radar or force information is revealed. All other
mission costs, prerequisites and numerical difficulty modifiers are unchanged.

Validation: rebuilt engine, zero errors. Valid portfolio suites passed 155 UFO and
147 TFTD checks; invalid-proposal suites passed 150/142. Tests inspect every unlocked
infiltration candidate for a country-label match and explicitly exclude Antarctica
in standard UFO rules. The existing commit tests cover atomic rejection of excluded
menu proposals; they do not simulate every country/terrain completion outcome.
All 72 Python checks also passed. Logs are
`build/local/infiltration-country-build.log` and
`build/local/infiltration-country-tests.log`. No user saves were modified.

## Proposed compact investment specification â€” not live yet

Use structured fields rather than another advisor or long narrative:

```json
{
  "objective": "BUILD_LOGISTICS",
  "mission": "STR_ALIEN_HARVEST",
  "cost_now": 3,
  "delivered_if": "VERIFIED_PRODUCTIVE_ACTIVITY_ON_UNREWARDED_PARENT",
  "conditional_gain": {"next_month_resources": 2, "logistics": 1},
  "next_month_resource_gain_capped": true,
  "capability_path": "logistics >= 2 permits standalone base candidates",
  "success_probability": "UNKNOWN",
  "time_to_delivery": "UNKNOWN_TO_PLANNER",
  "regional_exposure": "PARTIAL_OBSERVATIONS_NOT_A_PROBABILITY"
}
```

This is a **conditional outcome vector**, not a mathematical expected value. An
expected value would require defensible success/timing probabilities and a value
for political control versus cash. Neither is presently supplied. Do not invent them
or imply the model already understands a reward table it has not actually received.

Follow-up experiments should vary progression gates and delivered/undelivered outcomes
while keeping the contract concise, legal, and within the checkpoint token limits.
Retain the old simple packet as a control. Determine whether an outcome contract,
complete-portfolio ranking, or both change behavior; avoid changing all at once.
Meaningful new base/pact income, regional scientific findings, saturation/diminishing
returns or assault capabilities remain separate gameplay-design changes requiring
explicit implementation and validation, not prompt-only promises.

## Robustness standard

No universal wording/order invariance is assumed. Alternative portfolios may be
equally defensible under unknown success odds and an unspecified conquest utility.
Predeclare sets of acceptable decisions and material failures on controlled scenarios.
Measure changes under irrelevant reorderings/renamings, preferably with repeated
trials and confidence margins kept separate from unvalidated model scores. A flip
between acceptable alternatives differs from a flip to an impossible or incoherent
investment. Costs, menu membership, capacity and objective-feasibility boundaries
are hard invariants enforced outside the learned model.

## Persistent base economy

See [ALIEN_BASE_ECONOMY.md](ALIEN_BASE_ECONOMY.md) for maturation, delivered supply, country influence, save migration and destruction semantics. This supersedes the historical no-base-income wording in older experiment packets.
