# Specialist advisor experiment, 2026-10-06

## Revision 2: evidence gates and compact commander control

`scripts/test-command-advisors.py` now tests three structures against identical
native input: current v5, compact commander without advice, and compact commander
with evidence-gated advice. Outputs are separate in `build/local/advisors-march-v2`;
the v1 results below remain historical.

Resistance advice can select only regions backed by admitted surviving reports,
or recent loss assignments when reports do not overlap the available menu. It may
abstain. Each recommendation retains report count, assignment-loss count, source
IDs and HYPOTHESIS certainty; compact advice carries counts and certainty.
Political and economic regional recommendations are gated to UNKNOWN because
the current native input lacks regional exposure and productive/political outcome
attribution. This is deliberate deterministic gating, not evidence of the model
learning to abstain. Their live regional evidence contracts still need development.
They make no model call when unsupported. Strategic mission choices remain open;
UNKNOWN advice does not prohibit productive operations or terror.

57 unit checks cover the revised advisor contracts and existing portfolio checks.
This remains a read-only experiment, not a live staged implementation.

| Revision 2 variant | Strategy | Operations | Remaining | Time |
|---|---|---|---|---|
| Current v5 | Political pressure | Terror Europe; search Europe; terror Southern Africa | 3 | 12.81 s |
| Compact commander alone | Intelligence | Research Arctic; research Antarctica; research Central Asia | 7 | 9.92 s |
| Compact commander with advisors | Intelligence | Research Europe; research Arctic; research Antarctica | 7 | 12.50 s |

Resistance advice selected Europe with one admitted reporter and receipt 5.
North Africa already had a pending search and was absent from the native menu;
this advice does not rank all suspected regions independently of deployability.
Political and economic advice correctly remained UNKNOWN under the evidence gates.
The compact control shows that simplifying context changed the strategy and mission
types; advice changed the first research region to Europe. Research is not a base
search under stock rules, and the final two regions still lack supportive targeting
evidence. This is narrower behavioural improvement in advice provenance, not proven
strategic judgement. No missions executed and source receipt SHA remained unchanged.

## Staging in the engine

The existing `GeoscapeState::time10Minutes` update permits distinct advisory slots
at 23:30, 23:40 and 23:50 on the last day of a month, followed by a commander decision
at the monthly boundary. Calendar month length must come from the engine calendar.
Each slot needs a saved cutoff and receipt, so loading a save does not repeat it.
Final mission eligibility, budget and prerequisites must be rebuilt at commitment.

The current `buildAlienMonthlySitrep` selects the month before its `asOf` argument.
Calling it normally at 23:30 would summarise the wrong month for upcoming planning.
A staged implementation must explicitly select the current month and bound evidence
at the stage cutoff, preserving partial-month coverage instead of claiming a final
monthly report. Advisory observations can be stale at commitment; that must remain
visible, with changed constraints revalidated and material late contacts handled.
Neither advisors nor their cached recommendations may reserve funds or spawn missions.

Spacing synchronous calls spreads hiccups; it does not make calls nonblocking.
The commander itself still makes multiple sequential choices, so advisor staging
alone cannot eliminate its month-boundary pause. Background work and safe polling,
or staging more of the decision sequence, require separate engine integration.

Read-only comparison on the exact native March input in
`build/local/search-v5-march-receipt.json`. Both variants use the same career-trained
Laya checkpoint on CPU. Live policy and campaign saves remain unchanged.

The experimental resistance, political and economic advisors each rank up to two
affordable regional opportunities, with an explicit insufficient-evidence option.
They receive compact admitted interception counts, recent own loss assignments and
relevant pending operations. They have no player locations or hidden campaign data.
The commander receives advisory region summaries, budget, progression, last-month
counts and pending-work counts instead of detailed operational-review telemetry.
Existing v5 search targeting constraints remain in force for actual portfolios.
Advisory recommendations themselves are unconstrained in this experiment so their
evidence use can be measured. Evidence IDs and counts accompany each recommendation
in the audit; they are deterministic annotations, not generated explanations.

| Variant | Strategy | Proposed operations | Remaining | Inference time |
|---|---|---|---|---|
| Current single commander | Political pressure | Terror Europe; search Europe; terror Southern Africa | 3 | 11.44 s |
| Advisors plus compact commander | Intelligence | Harvest Australasia; harvest Central Asia; harvest South East Asia | 4 | 21.73 s |

The resistance advisor ranked Antarctica then Arctic, both with zero reports,
zero assignment losses and no evidence support. Political advice ranked Australasia
then Central Asia, also without support. Economic advice ranked South East Asia
then abstained. The commander chose two harvest regions recommended by the political
advisor and one by the economic advisor. Its intelligence strategy and all-harvest
portfolio are inconsistent in intent, although mixed portfolios are legally allowed.

This demonstrates behavioural change, not strategic improvement. Splitting the same
checkpoint into roles does not make it independently knowledgeable or reliable.
This experiment also changes the commander's context, so the difference cannot be
attributed to role separation alone. Political/economic advice lacks observed regional
mission exposure, productive regional outcomes or political-state evidence; absent
reports must not be interpreted as demonstrated safety or vulnerability. The present
regional menu cannot justify country-level Canada/US base hypotheses.

Outputs: `build/local/advisors-march-v1/single_commander.json`,
`specialist_advisors.json`, and `manifest.json`. All model decisions, probabilities,
packets and token counts are preserved. 55 unit checks passed. This experiment did
not execute missions through the native engine, evaluate campaign outcomes, or implement
background/staggered inference. The current live v5 commander remains installed.

Next candidates: validate resistance advice against admitted support; preserve
support strength and UNKNOWN in compact commander summaries; add a regional exposure
denominator and verified economic outcomes before estimating safety; compare compact
commander alone against compact commander plus advice to isolate the advice effect.

Reproduce from `G:\OpenXcom`:

```powershell
.\build\local\laya-venv\Scripts\python.exe scripts/test-command-advisors.py `
  --receipt build/local/search-v5-march-receipt.json `
  --checkpoint 'C:\Users\Main PC 2\AppData\Local\Temp\uppward-v4' `
  --out build/local/advisors-march-v1
```
