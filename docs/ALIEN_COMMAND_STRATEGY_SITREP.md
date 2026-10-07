# Monthly sitrep and campaign strategy — implementation

The commander loop is: engine-generated monthly sitrep -> learned campaign strategy -> up to three eligible funded operations and targets -> engine execution -> next month's observed outcome review. Protocol `alien-strategy-laya-v2`, prompt `roles-defer-v4`. Strategy changes the decision context; native costs and allowance curves remain unchanged.

Conquest is the continuing objective. A strategy is a temporary means of advancing it, not a replacement objective or a requirement to spend every resource. Saving is a spending decision within a strategy and should be evaluated against useful deployment, the carry limit, future commitments, and allowance expiry.

## Initial strategies

| Strategy | Preferred operations | Intended purpose |
| --- | --- | --- |
| Resource acquisition | Harvest, abduction, eligible base establishment and supply | Earn verified income and develop productive infrastructure/capabilities. |
| Political pressure and expansion | Terror, eligible infiltration | Weaken resistance and establish controlled territory; verified control should eventually contribute income. |
| Intelligence development | Research/probe, base search where appropriate | Improve situational awareness and establish actionable targets. Research flights and base search retain their distinct engine capabilities. |
| Counter-XCOM | Evidence-directed search, later independently funded assaults | Find and disrupt the organization opposing conquest; confirmed targets and assault prerequisites remain necessary. |

Strategies should bias a mixed portfolio rather than restrict it to a single mission type. An economic posture may still buy intelligence or protect infrastructure. There should be no compulsory retaliation and no fabricated assault target. All decisions remain bounded by the native eligible menu, costs, prerequisites, existing commitments, and three-operation limit.

## Monthly sitrep contract

Use deterministic summaries of admitted facts, with full source receipts retained separately:

- Previous strategy, selected operations and assigned regions, actual commitments, and spending versus reserved/expired resources.
- Own craft deployed and operational losses, deduplicated by unique craft ID. A missing craft or terminated contact must not automatically establish that XCOM shot it down or captured it. Preserve the evidence quality and reporting coverage.
- Last known own mission/assignment region for unavailable assets. Do not expose the hidden encounter location of a lost reporter as enemy-position evidence.
- Surviving reported interceptions, per region, with independent reporting craft and evidence references.
- Verified research flight completions and productive activities, their once-per-parent gains, capability progress, and pending next-month income. A productive subtask is not automatically a successful entire mission.
- Operations still pending, uncertain outcomes, and any lack of historical accounting/reporting coverage. Absence of new reports does not establish regional safety or campaign success.
- Later: verified infrastructure commissioning/destruction, supply deliveries and productive capacity, territorial control, and terror outcomes. These need explicit native outcome contracts before they create income or claims of victory.

An initial safe summary might say: 'Previous strategy: intelligence. Two craft unavailable on operations assigned to North Africa and Europe; cause and enemy recovery unconfirmed. One verified research flight completed in North America. Two operations remain pending.' This is an illustrative format, not a report of the player's actual campaign.

If enemy recovery or raids become observable, admit them through a specific evidence/reporting mechanism. Do not read the player's debriefing, hidden research, or captured inventory into the commander merely because those fields exist in the save.

## Decision context and persistence

The strategy choice receives conquest objective, monthly sitrep, own resources/progression, known obligations, and feasible strategic options. Operation choices receive the selected strategy, compact sitrep, relevant reported regional risk, prior selections, and remaining resources. Separating these questions avoids squeezing the entire campaign history into the current checkpoint's 512-token window. Reject oversized packets rather than silently truncating evidence or constraints.

Persist chosen strategy, exact sitrep and provenance, actual committed portfolio, and outcome receipts in the campaign audit/save. Reload must not repeat strategy selection, allocation, commitments, or rewards. The following month compares intended strategy with observed results, while retaining uncertainty and pending operations. Do not require the model to invent a rationale: audit explicit strategy purpose, choice scores and engine facts separately.

## Implementation boundaries

The native input now carries a deterministic previous-calendar-month sitrep, including prior portfolio/strategy, owned deployment/return receipts, deduplicated unavailable reporting craft by assignment, surviving contacts, verified productive activities and pending operations. Coverage is explicitly PARTIAL_FLEET_OUTCOMES: ground recovery/capture and every possible removal cause are not tracked. Legacy saves cannot reconstruct missing telemetry. The exact sitrep and every strategy/operation/region prompt and choice persist in portfolio audit receipts. No player debrief, funds, hidden base position or research is admitted.

Base/supply productivity and infiltration-derived income remain staged. Infiltration income should depend on verified alien territorial control and a defined recurring-income contract; choosing an infiltration mission or launching its UFOs cannot itself award conquered-country revenue. Base establishment and infiltration choices are available when existing native prerequisites and rules are met; their future recurring-income claims remain unavailable. Supply portfolio selection and independent assaults remain staged.

## Local validation, 2026-10-06

Native clean rebuild and final incremental correction passed. Python checks: 41 passed. Six scripted cases (accept, save, invalid menu, duplicate, over-budget, invalid strategy) passed in UFO Defense and TFTD; accepted runs: 118/113 checks, save: 116/111, rejection cases: 114/109. Real checkpoint through the monthly native entry point: 115/110 checks. Reload preserves the prior strategy and committed portfolio; losses are deduplicated and hidden base/funds/encounter coordinates cannot change the sitrep.

The read-only replay of Post-January - AI testing.sav used the same native input builder as execution and verified the original SHA-256 unchanged. Final receipt: build/local/replay-20261006-173415-974/manifest.json. Its exact sitrep reports three unavailable craft by assignment (two Europe, one North Africa), surviving regional contacts and the pending European terror operation. Deployment/return counts are incomplete on this older save. The checkpoint chose political pressure and a nonempty mixed portfolio; this establishes actionable inference, not strategic quality or balance. The initial replay exposed an overly broad terror menu; native eligibility and selected target-area indices now apply the stock mission-site area rule, excluding ordinary polar rectangles. Full input, choice prompts/scores and final response remain in the replay directory.

Nine mission types, thirteen regional loss groups, previous three operations and all three slots passed the actual tokenizer guards with scripted choices. This is token/wiring validation, not learned behavior. Oversized packets still fail explicitly rather than truncate. Audit viewer JavaScript syntax passed; visual layout was not verified. No checkpoint weights, allowance curves or player saves changed.

Launch from G:\OpenXcom with `.\scripts\run-local.ps1 -Portfolio`. Close an earlier game/service session first. Load Pre-february.sav, cross February 1, and save a new comparison branch. A later campaign save uses its next monthly boundary; an already recorded February portfolio is not replaced on reload.

## Live role/progress and deferral revision

Prompt roles-defer-v4 includes a two-month review of losses and verified productive activities, loss counts by preparation/search/objective-carrier/unknown role, and pending terror objective waves. New UFO deployment receipts capture the actual craft type, wave index and role. Preparation is reserved for non-objective craft of site missions; other unsupported purposes remain UNKNOWN. Pending wave and total wave counters remain explicit in the native input/audit.

Legacy records may establish roles only for continuously observed own assignments where all recorded deployments match native wave counters and rule counts. Such support is labelled LEGACY_OWN_SEQUENCE_MATCHED_TO_RULES; explicit telemetry is labelled EXPLICIT_NATIVE_TELEMETRY. Missing or completed legacy coverage remains unknown. Lost craft assignment is not hidden enemy encounter location, and pending objectives are not successful outcomes.

The spending option remains SAVE in the engine protocol, but its model description explicitly says defer investment, amount carried and amount forfeited. Money alone cannot provide productive prerequisites. No compulsory spending, allowance change, race control or tactical control was introduced. Larger regional summaries retain the largest four groups and explicit totals for other groups; the complete native input remains audited. Repeated strategy prose is reduced only for the wider late-campaign operation menu. Oversized packets still fail explicitly.

The isolated month-transition test advances a copied February 28 save through the real Geoscape monthly entry point, executes native commitments in that copy, and verifies save/load and no repeated decision. Its source save is hashed before and after. It does not replace the player's campaign branch.

### Validated live revision on 2026-10-06

Clean native rebuild passed. Python checks: 48 passed. All six scripted portfolio cases passed in both masters (accept 120/115, save 118/113, rejection cases 116/111). Actual checkpoint through native monthly entry: 117/112 checks. The wider nine-type, thirteen-loss-region, two-month, three-slot tokenizer stress case passed without truncation (largest packet 499 tokens). Viewer JavaScript syntax passed; visual layout remains unverified.

The real Geoscape timer advanced an isolated copy of Feb 28 - finally.sav into March. Native commitments were terror Europe (Sectoid), search Australasia (Sectoid), search Arctic (Floater), spending eight and retaining five. Source SHA-256 unchanged; saved result/reload preserved accounting and receipts, and a repeated monthly call made no new commitments. Receipt: build/local/roles-march-transition-receipt.json. Copy and integrity manifest: build/local/replay-20261006-215746-931/manifest.json. Exact native role review matches the offline reconstruction: two preparation scouts lost, four search craft lost, both earlier funded terror objective waves pending. All six legacy classifications carry their reconstruction provenance. Inference took 11802.49 ms. Timing remains synchronous; background or staggered planning is a separate change.

Restart with `.\scripts\run-local.ps1 -Portfolio`, load Feb 28 - finally.sav and cross March 1, then save a new comparison branch. Do not expect an already saved March portfolio to reselect on reload. Existing March and earlier campaign branches remain available.

Final deployment-hook verification passed for both games: actual craft type, wave index and role were emitted by native UFO spawning. Stock retaliation assault craft are labelled objective carriers; funded portfolio searches retain their assault restriction. Exact wire receipt: build/local/roles-deployment-wire-receipt.json. The final incremental build and accepted native portfolio tests passed after this role-label correction.
# Search targeting revision: search-evidence-v5

The portfolio service constrains base-search targets to regions with persistent
admitted surviving interception reports. If none overlap the static search menu,
it uses the previous month's own loss assignment regions as explicitly uncertain
clues. With neither source it permits exploration. Other mission targets retain
their full menu. The model chooses among eligible targets; this targeting constraint
is deterministic and must not be credited as learned strategic judgement.

Each REGION decision records `targetingBasis` and `eligibleRegions`. Exhausting
evidence-supported search targets removes further searches for that portfolio;
it does not fall back to unrelated targets. No player base coordinates enter the
policy. Missing reports are not converted into known shootdown positions. Legacy
loss assignments remain weak tasking-region proxies, not encounter locations.

The existing native retaliation mission flies its selected region. Native
`DetectXCOMBase` requires an eligible flying craft, trajectory stage and sight
range, then tests the base detection chance. A matching region increases relevance
but cannot guarantee detection, particularly with wide radar coverage. The existing
search-only/no-auto-assault restriction remains enforced by the native engine.

Restart the portfolio launcher to load v5 and replay a pre-boundary save; a recorded
March portfolio does not rerun when a post-boundary save is loaded.

# Current live policy: concrete-plans-v6

The native sitrep and evidence contract described here remains in force. The live
planner now uses simple concrete objective/mission choices and targets rather than
a separate strategy call. See `ALIEN_COMMAND_CAMPAIGN_PLANS.md`. Earlier prompt
versions and experiments below are retained as history.

