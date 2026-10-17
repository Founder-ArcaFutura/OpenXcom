# Conditional-outcome contract: paired monthly test

## Finding

Explicit conditional rewards change Laya's allocations, but do not demonstrate a
better conquest strategy. April becomes invariant between the two tested mission
option orders, but three of four months remain order-sensitive. More resources are
invested in abduction; no treatment portfolio selects infiltration or terror.
Keep this experimental: the live v8 planner is unchanged.

The reference LLM responses supplied more inspectable justifications and some
coherent plans; this experiment does not validate their campaign outcomes or make
provider consensus an answer key. No LLM response was fed to the local classifier.

## Controlled comparison

Four frozen inputs: February 1 reviewing January; March 1 reviewing February;
April 1 reviewing March; May 1 reviewing April. Each input is run in four conditions:
current sequential baseline; sequential with conditional outcomes; baseline with
reversed PLAN options; outcomes with reversed PLAN options. TARGET options retain
their order. Same actual checkpoint, budget, costs, capacity, search policy and
lessons in every paired condition. No whole-portfolio ranking, broad objectives
summary, long pros/cons, new rewards, mandatory spending or training is added.

Only two PLAN-state fields are added to the treatment:

- `conditional_results`: offered mission types mapped to verified completion/activity
  rewards or possible native political/discovery/pact/base outcomes.
- `outcome_limits`: rewards once per parent, next-month cash subject to cap,
  success odds/timing unknown, recurring pact/base income absent.

Cost remains in the unchanged option label. The contract does not invent a success
probability or expected utility. It is the minimal conditional-payoff component of
the proposed outcome specification; it does not yet add a prerequisite-path summary.
A field-by-field check confirms identical first PLAN state after removing these two
fields, identical criteria/order, and identical instructions within each pair.
After the first different choice, later states naturally diverge.

Historical inputs predate the new country-feasibility patch. The same static rules
filter is applied to BOTH arms before running: the May infiltration options for
Arctic, Antarctica and Pacific are excluded because they contain no country label.
Other inputs lose no options. Original hashes and filtered paired-input hashes are
retained separately. The filter mirrors native region alias, longitude-wrap and
latitude-boundary conventions for the standard UFO rules; these runs are not native
deployment tests. Geographic feasibility still does not guarantee a pact or base.

## Results

H=harvest, A=abduction, R=research, S=base search. Regions follow below.

| Decision | Baseline, normal | Outcomes, normal | Baseline, reversed | Outcomes, reversed |
|---|---|---|---|---|
| February 1 | 3 H; retain 2 | Same 3 H; retain 2 | H + 2 R; retain 4 | 3 A; retain 2 |
| March 1 | 3 A; retain 9 | 2 H + A; retain 9 | Defer all; retain 18 | 3 A; retain 9 |
| April 1 | H + 2 S + R; retain 15 | 4 A; retain 12 | Defer all; retain 24 | Same 4 A; retain 12 |
| May 1 | A + 3 R; retain 16 | 3 A + R; retain 14 | A only; retain 22 | 4 A; retain 13 |

Normal-order treatment targets:

- February: harvest South East Asia, Australasia, Europe (unchanged).
- March: harvest South East Asia, abduct Australasia, harvest Central Asia.
- April: abduct North Africa, Europe, North America, Siberia.
- May: abduct Australasia, South East Asia, North America; research South East Asia.

Reversed-order treatment differs in February (abduct Australasia, South East Asia,
North America), March (abduct Australasia, Central Asia, South East Asia), and May
(abduct Australasia, South East Asia, North America, Europe). April is identical.
All exact baseline and treatment portfolios are in `results.json`.

All **16** portfolios pass the paired menu, cost, duplicate and capacity checks.
All actual packets passed the strict model budget without truncation. Maximum tokens
by month: 383, 396, 447, 491. Baseline order stability: 0/4 months; treatment: 1/4.
These counts describe one deterministic pair of menu orders per state, not estimated
population robustness or statistical significance. No acceptable-plan equivalence
set was preregistered, so a changed answer is not automatically a strategic failure.

## Interpretation and limits

The sparse live packet was missing explicit conditional rewards. Supplying them has
a measurable local effect: the treatment invests rather than deferring in the reversed
March/April/May cases, and normal May shifts away from research. This weakens an account
that Laya simply ignores all mechanics. It does not prove it understands expected
campaign consequences: text/numeric cues and task-transfer biases remain alternatives.

The treatment still chooses repeated adaptation investments after adaptation has
reached infiltration's gate, while neglecting national control. April sends new
abductions into North Africa and Europe despite recent assignment losses. Conditional
payoff information alone has not resolved targeting or long-horizon allocation.

An additional representation issue is now explicit: the existing lessons represent
progression as the positional vector `[intelligence, logistics, adaptation]`, without
those axis names in the actual model state. The treatment names reward dimensions but
does not repair that existing ambiguity or supply missing prerequisite paths. We must
not attribute failure to use those paths solely to model capability or motivation.
The next bounded information test could use named progression fields and a compact
numeric missing-prerequisite contract, with the current sparse and payoff-only packets
retained as controls. Do not combine that with a new action-space architecture in the
same treatment. Wording/order variation still needs acceptable-plan criteria.

None of these plans was played through. Success probabilities, time-to-delivery and
the scalar value of political control versus resources remain unspecified. These are
independent frozen redecisions, not a resimulated alternate campaign. More spending,
more income-bearing missions, and less research are not independently validated wins.

February uses the previously labelled legacy January-input reconstruction with UNKNOWN
roles; later inputs are recorded native monthly DTOs. Later save-state outcomes are
not admitted into earlier decision packets. No source save or input file changed.

## Validation and artifacts

75 Python checks passed. New tests verify that only outcome information is added,
the geographic correction does not mutate original inputs, and outcome metadata does
not award resources or force operations. Post-run checks validate all 16 portfolios,
first-packet treatment differences and original source hashes.

`build/local/outcome-contract-monthly-v1/<decision-month>/` contains input.json,
baseline.json, contract.json, both reversed variants and manifest.json, including
exact model packets/probabilities, timing, source and paired-input hashes, excluded
regions and checkpoint identity. `results.json` here records the durable summary and
source-code/static-rule hashes. Live model/service configuration, checkpoint weights,
engine executable and user saves are unchanged by this experiment. No API calls.

Reproduce from `G:\OpenXcom`:

```powershell
.\build\local\laya-venv\Scripts\python.exe scripts/test-outcome-contract.py `
  --checkpoint 'C:\Users\Main PC 2\AppData\Local\Temp\uppward-v4' `
  --out build/local/outcome-contract-monthly-v1
```
