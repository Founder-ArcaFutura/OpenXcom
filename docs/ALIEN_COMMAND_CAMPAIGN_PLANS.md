# Concrete campaign plans experiment

## Current live revision: campaign-lessons-v7

The simple concrete planner now receives a compact assessment in each plan choice:
previous-month verified productive activity, region if exactly one previous/pending
assignment matches that mission type, cumulative admitted reporters plus recent
assignment losses, progression, and pending missions. Target choices receive the
productive history. Region attribution is a single recorded assignment hypothesis,
not a claimed safe region or confirmed full mission success. Multiple assignments
yield UNKNOWN_REGION. Assessment source remains native DTOs, not generated narrative.

Hotspots and pending summaries retain four rows with explicit omitted counts.
Productive types retain four rows. The full original input and assessment remain in
the portfolio receipt; assessments are rebuilt from the saved native ledger each
month. Outcome details are previous-month coverage, not an unlimited long-term
campaign memory. Cumulative interception beliefs and earned progression persist.

If any admitted reports or assignment-loss evidence exist but no matching search
target is available, new searches are removed instead of falling back to exploration.
Existing searches continue normally. Exploration is allowed only with no such evidence.
The audit records `searchEligibility`, `campaignAssessment`, and `assessmentLimits`.
No assault, budget, mission reward or numerical difficulty changes are introduced.

66 Python checks pass, including occupied evidence regions excluding unsupported
searches, ambiguous productive regional attribution, and exact tested/live packets.
Native copied February 28 to March 1 replay executed abductions in Australasia,
Central Asia and South East Asia, spending 9 of 18 resources and retaining 9.
Existing Europe/North Africa searches continued; no new polar searches. Assessment
contained the rewarded Australasia harvest and four assignment losses per hotspot.
Inference took 12.92 seconds; maximum packet 303 tokens. Source save unchanged,
native save/load and same-month no-repeat assertions passed. Receipt:
`build/local/lessons-v7-march-receipt.json`.
Launcher health requires `campaign-lessons-v7`; restart the game/launcher service
to activate. Historical sections below describe earlier versions.

## Live integration: concrete-plans-v6

Independent-search race fix, 2026-10-07: funded portfolio retaliation searches
now draw from the active research mission's monthly race weights (UFO), falling
back to the probe mission's weights (TFTD). Absence of either progression rejects
the portfolio rather than using unrestricted retaliation weights. Native reactive
retaliation race inheritance is unchanged; mission rules and other mission race
selection remain unchanged. Already saved mission races are preserved.

Correction to the initial diagnosis: stock UFO research permits Snakemen even in
January/February. February weights are Sectoid 60, Snakeman 10, Floater 30.
The unrestricted retaliation fallback instead weights all five races equally from
month zero. This fix removes that fallback for independent searches; it does not
ban early Snakemen. TFTD month-one probe weights are Aquatoid 60, Gillman 30,
Lobsterman 10; that legitimate early Lobsterman possibility is likewise preserved.
The engine rebuild passed with zero errors. Scripted native portfolio integration
passed 121 UFO and 116 TFTD checks, including early independent-search race pools.
Logs: `build/local/search-race-build.log`, `build/local/search-race-tests.log`.

The portfolio service now calls the shared `scripts/campaign_plans.py` planner
with `tradeoffs=False`, preserving the exact tested simple packets. The historical
experiment imports that same module. `predict_portfolio` emits protocol v2 and
prompt version `concrete-plans-v6`; the launcher refuses an older running service.

No broad strategy inference is made. The protocol's strategy label is derived from
spending by objective for native compatibility, marked
`DERIVED_SPEND_LABEL_NOT_MODEL_STRATEGY`. Ties follow the existing strategy order.
With no new operations it uses a compatible prior/default reporting label, marked
`COMPATIBILITY_LABEL_NO_NEW_OPERATIONS`; infeasible menus report NO_FEASIBLE_OPERATION.
The individual plan objectives, costs, targets and conditional gains are authoritative.
Pros/cons are retained as capability metadata in receipts but are not fed to the
simple planner's model calls. The live service still makes sequential synchronous
calls at month end; advisory staging is not part of this integration.

The existing native validator commits up to three affordable valid missions
atomically, with search-only/no-auto-assault behavior unchanged. Verified harvest
activity awards +2 pending income and +1 logistics once per funded parent mission,
subject to the incoming bonus cap; abduction similarly awards adaptation. A target
with no reported XCOM presence does not receive automatic completion or income.

Actual March boundary replay committed abduction Australasia, search Europe and
harvest Australasia, retaining 5 resources. Audit receipt:
`build/local/concrete-v6-march-receipt.json`. Original source save unchanged;
native save/reload and duplicate monthly scheduling checks passed. The unit suite
has 64 passing checks including exact packet equivalence between tested and live
planners, deferral and infeasible budgets. Native real-checkpoint portfolio tests
passed 117 checks for UFO and 112 for TFTD; receipts are
`build/local/concrete-v6-xcom1-receipt.json` and
`build/local/concrete-v6-xcom2-receipt.json`.

To activate: close the current launcher/game session, then run
`.\scripts\run-local.ps1 -Portfolio` from `G:\OpenXcom`. Load a pre-boundary save
to see a revised monthly choice. A recorded post-boundary portfolio is preserved.
For the January-end comparison use `Pre-february.sav` (January 30), or
`Feb 28 - finally.sav` for the March decision. No user save was rewritten.

## January and February retrospective comparison

The requested months are the completed-month inputs: January reviewed at February 1,
and February reviewed at March 1. These are independent frozen-input redecisions,
not a simulated alternate campaign. February retains actual historical outcomes;
it is not conditioned on the new January portfolio.

| Completed month | Concrete plans | Explicit pros/cons | Resources retained |
|---|---|---|---|
| January | Harvest Australasia; search Europe; search North Africa | Research Arctic; research South East Asia; research Antarctica | 4 / 5 |
| February | Abduction Australasia; search Europe; harvest Australasia | Terror Australasia; terror Central Asia; terror Europe | 5 / 1 |

Budgets were 11 and 13. Inference times: January 5.67 / 12.62 seconds;
February 6.23 / 10.73 seconds. February reproduces the previous comparison.
January has one admitted reporter each in Europe and North Africa. Concrete searches
match those clues, although the deterministic v5 eligibility constraint also limits
searches to supported regions. Australasia has unknown exposure, not proven safety.
The simpler structure produces coherent mixed portfolios on these two inputs; that
does not establish future outcome superiority or broad model reliability.

January source: `build/local/user/xcom1/Now THAT was a lag! .sav`, boundary time
February 1 00:00:45, recorded decision February 1 00:00:00. Original budget/menu/
knowledge/sitrep retained. Missing operationalReview was supplemented from pre-decision
audit, leaving all three legacy losses UNKNOWN. Existing mission 2 wave progress
comes from the boundary save; no subsequent recorded deployment for that mission was
found. This is a labelled reconstruction, not an original v4 native receipt.
Full provenance: `build/local/campaign-january-input-provenance.json`.

January input: `build/local/campaign-january-input.json`. February input:
`build/local/search-v5-march-receipt.json`. Outputs and individual input hashes:
`build/local/campaign-plans-jan-feb/campaign-january-input` and
`build/local/campaign-plans-jan-feb/search-v5-march-receipt`. Both manifests confirm
unchanged source receipts, no mission execution and no live policy change. Source
January save hash was checked unchanged during extraction. 61 checks passed after
adding batch receipt support; one model load runs both variants for each input.

2026-10-06. Same March native input as the advisor comparisons, same actual
career-trained Laya checkpoint, CPU. Read-only: no missions executed, live policy
unchanged, source receipt SHA unchanged. Output directory:
`build/local/campaign-plans-march-v1`.

Plans are deterministic templates grounded in existing mission capabilities and
budget costs. The model chooses up to three plan types and targets. There is no
separate broad strategy choice that can drift away from the selected mission.
Each plan receipt retains objective, actual mission/region, cost, conditional
gain, downside, admitted supporting IDs, reported exposure and uncertainty.
This experiment does not demonstrate learned advisor generation or independent models.

Two variants share the same eligible operations, budget, search constraints and
selection instructions. The treatment adds explicit gain/risk descriptions to plan
and target packets. The control uses objective/cost labels without those descriptions.
Both retain uncertainty about enemy locations and unobserved regional exposure.
Static descriptions remain in final receipts in both variants, but only the treatment
actually feeds their full pros/cons to the model.

| Variant | Operations | Spent / retained | Inference |
|---|---|---|---|
| Concrete objective/cost plans | Abduction Australasia; search Europe; harvest Australasia | 8 / 5 | 6.39 s |
| Plans with explicit pros/cons | Terror Australasia; terror Central Asia; terror Europe | 12 / 1 | 10.54 s |

The control now pairs a locate-XCOM objective with a real base search. The treatment
instead concentrates entirely on terror. This establishes sensitivity to wording,
not successful campaign risk management. No gain or strategy superiority is established.
Terror has no implemented new income bonus; political vulnerability remains UNKNOWN.
Australasia/Central Asia lack admitted reports, which does not demonstrate safety.
Europe has a surviving interception report. Existing North African search is excluded
from duplicate deployment by the native candidate menu.

Search benefit is explicitly conditional: discovery may enable a later devastating
base assault, but assault is currently unavailable. Scout losses can prevent discovery,
search provides no income, and reports describe XCOM reach rather than a base coordinate.
Harvest and abduction gain +2 pending income and +1 logistics/adaptation only on verified
activity; interference may prevent gains. Income is subject to the native bonus cap.
Research/probe flights develop intelligence and income but cannot discover bases.

61 unit checks passed. Real model packets passed strict token guards and retained
their probabilities, token counts and hashes. This is a single frozen campaign input
and two deterministic runs, not a generalization or campaign-outcome evaluation.
The live v5 commander and campaign saves remain untouched. Staged/background inference
is still not wired into the engine.

Reproduce from `G:\OpenXcom`:

```powershell
.\build\local\laya-venv\Scripts\python.exe scripts/test-campaign-plans.py `
  --receipt build/local/search-v5-march-receipt.json `
  --checkpoint 'C:\Users\Main PC 2\AppData\Local\Temp\uppward-v4' `
  --out build/local/campaign-plans-march-v1
```
