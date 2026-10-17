# Monthly sequential versus complete-portfolio experiment

## Result

The comparison changes decisions, but does not yet demonstrate a robust replacement
for the live planner. Three of four monthly decisions change when the SAME complete
portfolio options are reordered. The one May infiltration selection also exposes a
country-feasibility hole in the native candidate menu and the experimental builder:
it targets Antarctica, which has no country label eligible for the pact outcome.
No live switch, training or mission execution was performed.

## Paired monthly results

These are current-v8 redecisions on four frozen historical inputs, not four successive
months of a new campaign. Later inputs keep actual historical outcomes. 'Before'
means rerun the current sequential planner, not necessarily the older recorded policy.
There is no recorded initial January decision in this comparison; the first decision
is February 1, reviewing January.

| Decision / evidence month | Before: sequential v8 | After: canonical whole-portfolio choice | Other two orders |
|---|---|---|---|
| February 1 / January | Harvest South East Asia, Australasia, Europe | Terror Australasia; harvest Australasia; research Antarctica | Before portfolio; then canonical choice |
| March 1 / February | Abduct Australasia, Central Asia, South East Asia | Same as before | Same in both orders |
| April 1 / March | Harvest South East Asia; searches Europe/North Africa; research Arctic | Harvest Australasia; abduct North America; research Antarctica; harvest North America | Terror Australasia, harvest Australasia, research Antarctica, abduct North America; then canonical choice |
| May 1 / April | Abduct Australasia; research South East Asia, Arctic, Antarctica | **Infiltrate Antarctica**; harvest Australasia; abduct Australasia; research Arctic | Before portfolio in both orders |

Retained resources, before -> canonical after: February 2 -> 2; March 9 -> 9;
April 15 -> 13; May 16 -> 11. Spending more is not evidence of better strategy.
All twelve v2 complete-portfolio selections satisfy the frozen menu/cost/capacity
checks. This is **menu validity**, not verified native deployment or meaningful
objective feasibility. No selected v2 packet exceeded the token guard; maximum
tokens per month were 267, 308, 338, 371.

## Design and provenance

The same real career-trained Laya checkpoint runs both arms, CPU, without tuning.
The before arm is `plan_concrete_portfolio` with current campaign lessons and native
progressive capacities. The after arm chooses one complete mission+region portfolio
in one model call. It receives budget/capacity, compact campaign lessons and caveats.
It does not receive LLM transcripts, provider consensus or their preferred answer.
Full model identity and input hashes are retained in each manifest.

Candidates are constructed from four fixed, transparent motifs: capacity, control,
pressure and information. Illegal/unaffordable/duplicate operations are excluded;
unavailable mission types are skipped. Candidate target assignment is deterministic:
searches rank admitted reporter/loss clues, while other missions rank fewer assignment
losses/reporters first, then an unambiguous recent productive assignment, then region
ID alphabetically. Absence of reports is NOT evidence of safety. The current rerun
portfolio and defer are also candidates, and duplicate portfolios are removed.
Motif names are audit metadata, not model option labels. There is no model rationale.

The after arm therefore changes **candidate construction, target assignment, packet
wording and joint selection**, not merely classifier architecture in isolation. Its
context is a different projection of the same native input; the sequential packet's
explicit role-loss counts are not separately repeated in the joint packet. Conclusions
must not attribute every difference to joint planning or latent strategic understanding.

Three fixed orders are canonical, reversed and rotated once. Candidate IDs retain
their meaning across orders, and the context string is unchanged within each order
comparison. These are order-sensitivity checks, not independent stochastic replicates
or a generalization benchmark. A single seeded random candidate per month is retained
as a negative choice control, not as a performance score.

Sources:

- February: `build/local/campaign-january-input.json`, the previously labelled
  reconstruction of January's old receipt with UNKNOWN craft roles. Its supplemental
  progress came from the February 1 00:00:45 boundary save; see the existing
  `campaign-january-input-provenance.json`. This is not an original v8 receipt.
- March: `Post-March_again.sav` recorded input.
- April: `I forgot to save.sav` recorded April input; later April outcomes withheld.
- May: `And into may.sav` recorded input.

Source hashes were verified unchanged after runs. No API calls were made. Checkpoint
weights, executable, live launcher/service code and user campaign saves were unchanged.

## Preserve the failed first packing attempt

Version 1 used readable full mission names and uppercase region labels. February,
March and April fit; all three May whole-portfolio orders exceeded the strict model
token budget and were rejected WITHOUT inference/truncation for those choices.
Those receipts remain under `build/local/whole-portfolios-monthly-v1`.

Version 2 uniformly reran ALL four months using explicit action codes (R/H/A/I/S/T/B)
and short geographic names with a legend in the context. It did not drop candidate
choices to make May fit. All before and after receipts remain separate in
`build/local/whole-portfolios-monthly-v2`. The wording change itself matters: March
was order-sensitive in v1 but stable in v2. This is evidence of representation
sensitivity, not a clean learning improvement.

## The Antarctica infiltration problem

The native `buildAlienPortfolioMenu` checks mission wave/trajectory feasibility and
active duplicates, but does not check for a country label eligible for the infiltration
objective. Native `AlienMission` attempts pacts by finding a country whose label is
inside the chosen region and which can be infiltrated. Standard Antarctica covers
latitudes 60..90; standard country-label latitudes range from -60 to 30, so no country
matches. The experimental quiet-region/alphabetical rule picked Antarctica for its
control candidate, and Laya selected it in canonical May order.

This is an inherited-menu/candidate-construction failure, not evidence that Laya
independently reasoned Antarctica was a valuable country. It also means simply
copying the legal menu into an LLM or classifier experiment is insufficient to promise
that every offered action can deliver its stated purpose. Country geography is static
rules knowledge; enforcing objective feasibility need not reveal player base locations.

## Diagnosis and next step

1. **Correct objective feasibility before promoting candidate ranking.** Infiltration
   candidates should have a possible native country target; experimental builders
   must not turn absent observations plus alphabetical ordering into strong advice.
2. **Address order/wording sensitivity.** The v2 February, April and May flips preclude
   claiming stable strategic preference from a single displayed order. Do not cherry-pick
   the May infiltration result or train from it.
3. **Then compare complete-plan ranking again on more states**, with candidate rules
   frozen in advance and exposure uncertainty preserved. A compact representation
   must retain mission semantics without silently changing the task to code association.
4. Fine-tuning remains a possible later step; this experiment does not establish that
   the shared classifier can select sensible plans solely because candidates look
   coherent to the engineer. Keep v8 live for now.

72 Python checks pass, including candidate legality/uniqueness, retaining before and
defer options, order-to-ID integrity and invalid portfolio rejection. Existing strict
model guards checked actual token limits and output probabilities. Unit tests and
menu checks do not substitute for campaign-outcome evaluation.

## Artifacts

`results.json` records the paired results, source-code hashes and stability summary.
Per-month directories in the v1/v2 build outputs retain before.json, candidates.json,
after.json and manifest.json (source/input hashes, actual packets, probabilities,
timing and model identity). Reproduce the v2 experiment from `G:\OpenXcom`:

```powershell
.\build\local\laya-venv\Scripts\python.exe scripts/test-whole-portfolios.py `
  --checkpoint 'C:\Users\Main PC 2\AppData\Local\Temp\uppward-v4' `
  --out build/local/whole-portfolios-monthly-v2
```
