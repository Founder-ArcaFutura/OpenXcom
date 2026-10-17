# Named progression and capability paths

## Result

Explicit names and short prerequisite paths change behavior, but do not establish
a stronger campaign policy. Across the tested normal/reversed mission-option orders,
exact portfolio stability was 0/4 months for the current baseline, 2/4 for named
progression, and 0/4 for named progression plus paths. These are descriptive paired
checks, not statistical estimates or a strategic-quality score. A changed portfolio
can be an acceptable alternative; identical choices can also be poor.

No model was forced to choose infiltration. Alien-base construction and XCOM-base
discovery/assault were represented as separate paths with actual implementation limits.
The live v8 service, game executable, checkpoint and user saves remain unchanged.

## Test design

Same four frozen monthly inputs, current sequential mission/region selection, costs,
capacity, native-style geographic infiltration filter and lessons in each arm:

1. Baseline: current compact progression vector.
2. Named: replace only `[intelligence, logistics, adaptation]` with explicitly named
   values. All remaining state and instructions stay the same.
3. Named + paths: named values plus missing prerequisites for BASE and INFILTRATION,
   preparatory mission types for the missing numeric dimensions, and the explicit
   fact that BASE_ASSAULT is unavailable while search can discover bases.

Each arm uses canonical and reversed PLAN options; TARGET ordering is unchanged.
This test deliberately does NOT combine conditional-payoff fields, whole-portfolio
ranking, long objectives prose, new rewards or fine-tuning. It isolates the next
representation components rather than attributing all changes to a combined rewrite.
First-packet differences and identical choice/instruction fields were checked after
the run. Later decision states differ when earlier choices differ.

Four independent frozen redecisions are not an alternate-campaign rollout. Historical
months retain actual outcomes, not consequences of newly proposed earlier choices.
The February input uses the existing labelled legacy January reconstruction; later
inputs use recorded native DTOs. Post-boundary save state is not passed as foresight.
Both arms exclude geographically impossible infiltration regions using the same
standard-rule country-label filter. Original input/source hashes are retained.

## Results by mission mix

A=abduction; H=harvest; R=research; S=base search. 'Normal / reversed' are separate
runs with the same factual input. Exact targets, cash and timing are in results.json.

| Decision | Baseline: normal / reversed | Named: normal / reversed | Named + paths: normal / reversed |
|---|---|---|---|
| February 1 | 3 H / H + 2 R | 3 R / same 3 R | A + 2 R / 2 S + R |
| March 1 | 3 A / defer | 3 A / defer | 2 A + H / A + 2 H |
| April 1 | H + 2 S + R / defer | A + 3 R / defer | A + 3 R / 2 S + 2 R |
| May 1 | A + 3 R / A only | 4 R / same 4 R | A + 3 R / S + 3 R |

In normal March, the path arm adds one harvest to two abductions. With delivered
activity it could fill the missing logistics point for base eligibility. This is a
plausible investment link, not proof the model selected it for that reason. Reversed
March instead selects two harvests and one abduction. Normal May's path result has
the same mission mix as baseline, with a different creation order; reversed May adds
a search in South East Asia. No arm chooses infiltration in this run.

## What the engine actually lets the commander do

The user's broader strategic point is valid: infiltration is not the sole intended
route. However, the currently wired adaptive space is narrower than that intention:

- Alien-base construction is gated by month and logistics; logistics remains below
  the threshold in these actual input states. Correctly showing that gap cannot
  create a legal base operation immediately. Successful future harvesting could.
- Funded searches can discover XCOM bases, but a separate funded assault option is
  not implemented. The native game supports base attacks, but the adaptive policy
  explicitly separates and currently defers them. It cannot choose to destroy all
  XCOM bases through an action absent from its legal menu.
- Infiltration is available in May after real research/abduction progression, but
  recurring custom income from pacts/bases remains unimplemented. Native pact/base
  effects are still conditional. The relative conquest utility is not calibrated.
- Terror has native political effects but no custom economic bonus or supplied
  numerical conversion into conquest utility.

Therefore failure to pick infiltration is not itself failure to pursue conquest,
and failure to pick unavailable base/assault actions must not be blamed on the model.
Continuing the unchanged campaign into June is useful for obtaining another real
state, especially if logistics rises. It does not imply online weight learning:
the fixed checkpoint receives updated evidence/progression, not training updates.

## Interpretation

Naming the axes is a cleaner information contract, but it often amplifies research
choices rather than revealing stable multi-step planning. Paths introduce some
plausible mixed preparation and more searches, yet remain order-sensitive. Small
semantic wording changes, transferred classifier priors and the incomplete reward/
capability specification remain competing explanations.

These runs do not establish that one new packet is superior, that the model lacks
all strategic capacity, or that LLM reference portfolios would win. Keep v8 live;
do not promote this prompt on the basis of one appealing March result. Obtain June's
before/after saves, and treat implementation of a legitimate known-base assault
choice and meaningful infrastructure/control consequences as separate design work.

## Validation and artifacts

78 Python checks pass, including named-state fidelity, actual prerequisite gaps,
correct preparatory mission mapping and the assault restriction. All 24 actual
portfolios passed paired menu/cost/capacity/duplicate checks. Strict token/probability
guards accepted every run without truncation. Actual maximum tokens by month:
see results.json. Source hashes were checked unchanged after the runs. No API calls,
model training, native mission execution or live policy change.

Raw artifacts: `build/local/named-progression-monthly-v1/<decision-month>/` contains
input.json, six complete run receipts and manifest.json with model identity,
source/paired-input hashes, exclusions and timing. This directory's results.json
contains the durable summary. The local experiment is reproducible from `G:\OpenXcom`:

```powershell
.\build\local\laya-venv\Scripts\python.exe scripts/test-named-progression.py `
  --checkpoint 'C:\Users\Main PC 2\AppData\Local\Temp\uppward-v4' `
  --out build/local/named-progression-monthly-v1
```
