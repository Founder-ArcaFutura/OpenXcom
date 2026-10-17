# Persistent operation feedback: v10

The monthly portfolio now receives a parent-linked account of funded operations. Native mission IDs are the operation identities. Decision receipts record the IDs actually committed, so an auditor can join the choice, its input/options, its cost and its subsequent events. Accounting and native mission execution remain authoritative; no model output awards a gain or declares a successful objective.

## Evidence and outcomes

The ledger is a deterministic projection of the existing saved audit and funded/rewarded mission sets. It has no second mutable balance or outcome database to drift during save/load. New assignment receipts mark complete telemetry from assignment; older history remains `PARTIAL_LEGACY`. Missing historical evidence is not backfilled from hidden player state.

Each operation reports assignment/last-event/gain dates, mission and assigned region, original cost, decision receipt, unique craft deployed/returned/unavailable, objective-carrier counts, admitted evidence IDs and:

| Field | Meaning |
|---|---|
| `lifecycle: PENDING` | New operation with continuously covered assignment, not yet closed |
| `lifecycle: ENDED` | Native scheduler explicitly ended the parent; no further waves/live craft remain |
| `lifecycle: UNKNOWN` | Legacy coverage does not establish its lifecycle; current sitrep may separately show an active parent |
| `outcome: GAIN_VERIFIED` | Accounting confirms a first qualifying research/productive receipt; reward persists despite craft losses |
| `outcome: OBJECTIVE_DELIVERED` | Native site establishment, alien base establishment, country pact/base establishment or base discovery was observed |
| `outcome: OBJECTIVE_PREVENTED` | Complete assignment coverage, explicit parent closure, at least one observed objective carrier, every such carrier unavailable, and no verified gain/delivery |
| `outcome: UNKNOWN` | No sufficient outcome evidence; ending or losing a scout alone is insufficient |

Lifecycle and outcome are independent: an operation can remain pending after earning a gain. Delivery takes precedence over carrier loss. Site delivery means the alien objective reached the Geoscape; it does **not** mean aliens won the subsequent tactical battle or secured an unopposed terror result. No tactical-victory claim or new terror reward is introduced.

`cashEarned` is the operation's lifetime conditional resource award, not a promise of that amount being credited at the next boundary. Existing bonus caps still apply. `gainAt` prevents an old gain being described as new monthly productivity when a later craft event occurs. Research/harvest/abduction gains remain once per funded parent.

## Monthly loop

Before a due monthly portfolio decision, after existing budget/base accounting, native code writes one `monthly_reconciliation` receipt for that calendar month. It snapshots the operation ledger and current budget. Repeated scheduler calls and save/reload cannot issue a second monthly reconciliation or repeat the portfolio allocation. The subsequent portfolio receipt links newly committed IDs; its input includes the reviewed evidence.

Rolling regional loss memory covers the current calendar month and the two preceding months, deduplicates own unavailable-craft identities, retains assignment-region receipt support and expires older clues. These are uncertain assignment clues, not exact interception coordinates or enemy-base knowledge. Both resource targeting and evidence-directed base search can use this memory. Zero reports remains unknown exposure.

## Bounds and classifier contract

The native envelope includes up to 24 operation rows, prioritizing continuously covered pending operations, then most recently updated history. Its total/truncated fields disclose omissions. Regional loss memory contains up to 16 regions and eight receipt IDs per region. Operation proof lists retain the last eight qualifying receipts and their total count. Full original audit events remain saved.

The existing concrete-plan action labels and checkpoint are retained. With a ledger present, the compact briefing includes two recent operation rows (`mission, region, lifecycle, outcome, lifetime cash earned, unavailable craft`), two productive groups, three interference hotspots and two commitments, plus omission counts/coverage. Gain locations are joined by parent ID rather than guessed from another same-type mission. Existing callers without a ledger remain supported. Detailed inputs and rendered model packets stay in the decision receipt.

The launcher requires prompt version `progressive-portfolio-v10` so a stale service cannot silently handle the new contract. No reward buffs, portfolio-cap changes, forced mission mix, online training or checkpoint switch accompany this change.

## Use and inspection

From `G:\OpenXcom`, launch `.\scripts\run-local.ps1 -Portfolio`. Continue an existing campaign through the next monthly decision and save. New operations receive complete coverage; legacy records retain their explicit limitations. Rewinding is optional if a controlled comparison is wanted.

Read the last saved monthly review without modifying the campaign:

```powershell
.\build\local\laya-venv\Scripts\python.exe .\scripts\audit-alien-operations.py `
  --save '.\build\local\user\xcom1\YOUR_SAVE.sav' `
  --out '.\build\local\operation-review'
```

This creates `monthly-review.json` (the snapshot before the monthly choice, with later portfolio receipts) and `operations.csv`. It verifies that reading/exporting did not modify the source save. Original player saves are never rewritten by the test/export harness.

Validation results and copied-save transition receipts are recorded under `build/local/operation-ledger-*`. This telemetry implementation does not by itself demonstrate improved strategic choices; that requires subsequent campaign observations.

## Completed validation, 17 October 2026

- Native build installed in `build/local/runtime`, zero build errors. Native suites passed 184 UFO and 173 TFTD checks, including actual research-flight/productive-landing reward hooks and ledger persistence.
- All 108 Python tests passed. A tokenizer-only check exercised 84 forced portfolio paths including six-operation portfolios; maximum packet length was 505/512 with no truncation.
- Scripted copied-save transition crossed into June, admitted three funded operations and preserved decision links/reconciliation across reload.
- The actual career checkpoint then crossed the same boundary on a separate copy: native status `PORTFOLIO_EXECUTED`, four linked operations, 14 reviewed historical operations, six lifetime verified gains and all 14 historical coverage markers explicitly partial. Reconciliation exactly matched the model input. Maximum actual model packet length was 445 tokens; request size 16,061 bytes.
- The learned portfolio selected abduction in South East Asia and North America, then harvest in Australasia and Central Asia; cost 12, remaining 18. This records execution, not demonstrated strategic superiority.
- A brief power outage damaged the final local validation-summary log/file. The completed result save, operation ledger and monthly-review receipts were intact. Re-running `check-operation-ledger-replay.py --learned` against those saved outputs passed and regenerated the summary; all Python tests also passed after recovery.
- Original pre-June save SHA256 remained `d095e3dd2850ee74751309d8a7570356aff20577b12916b434a3345f296d3ec7`. Only isolated copies were advanced. Implementation remains local and uncommitted.

The verified review is at `build/local/operation-ledger-replay-learned/review/monthly-review.json`, its operation table at `operations.csv`, and the regenerated checks at `validation.json` in the same directory.
