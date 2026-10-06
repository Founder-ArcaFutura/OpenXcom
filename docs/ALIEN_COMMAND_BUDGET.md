# Monthly allocation and capability prototype

Status: shadow accounting only. This is a concrete first economy design, not enforced campaign balance. ModelExecute still executes the v2 operation menu without this budget. No difficulty modifiers, waves, detection chances, or current campaign funds were changed.

## Monthly allocation

Use the existing calendar boundary: January is month 0. A mission is a commitment purchased from that month's allocation, including all its existing waves. Delayed waves do not buy the operation again. Unused allocation carries forward within a limit; losses do not refund the original commitment. Monthly replenishment pays for future commitments, not an unlimited fleet on demand.

Provisional policy in `config/alien-command-budget.json`:

- Allocation uses one editable eighteen-month allowance transition per difficulty, then continues baseline support without further automatic increases. These are proposed off-world allowance curves, not extracted stock mission counts.
- January / July / month 18 allowances: Beginner 6 / 10 / 16; Experienced 7 / 13 / 23; Veteran 8 / 19 / 32; Genius 9 / 21 / 38; Superhuman 10 / 24 / 48. Full curves are in the policy file.
- Unspent carry remains limited to half the month's base allocation.
- Verified gain bonuses arrive next month, capped at half its base allocation; excess expires.
- Research/probe costs 2; harvesting and abduction cost 3; terror costs 4; base establishment and infiltration cost 6; supply costs 2.
- A retaliation request costs 0 until forces deploy. Its search deployment costs 2 once per parent operation; every distinct base-assault UFO costs 6 separately. An already-known base can produce an assault without paying for a search that never happened.

These are broad mission commitment units, not money or a researched measure of fleet value. The full mission purchases its waves. There is no separate replacement charge for a lost UFO in this first policy; the loss consumes its committed force and denies any uncompleted productive gain. Later fleet accounting can separate command capacity, hull availability, and replacement costs. We should tune costs against complete wave inventories before enforcement.

## Gains and capability progression

A first verified productive task within a mission earns the reward once. It does not claim that every UFO or the entire mission succeeded.

- Research/probe: a UFO reaches the end of its trajectory rather than crashing or being destroyed. Bonus 1 and intelligence progress 1. An admitted interception alone is not this completion receipt.
- Harvesting: the engine awards the operation's activity score. Bonus 2 and logistics progress 1.
- Abduction: the engine awards the operation's activity score. Bonus 2 and adaptation progress 1.
- Terror, retaliation, supply, infiltration, and base establishment earn no allocation bonus in this prototype. Their future rewards require explicit outcome contracts.

Another landing or another returning UFO from the same mission cannot farm another reward. Bonuses are earned from engine facts, not model assertions, mission disappearance, X-COM debrief scores, or mission timer expiry. A completed task can retain its reward if a different UFO is subsequently lost. Destroying all craft before productive completion earns no reward.

At monthly allocation, capability prerequisites are checked against accumulated verified progress and minimum elapsed months:

- Basic: research, harvesting, abduction, and terror operations.
- Logistics network: month 1 or later and logistics 2; enables base establishment and supply.
- Assault fleet: month 2 or later, intelligence 2 and logistics 1; enables assault deployments; searching only requires basic capability.
- Infiltration network: month 2 or later, adaptation 2 and intelligence 1; enables infiltration.

These are deployment/adaptation capabilities, not claims that aliens must invent their already-existing technology. The minimum month and progress thresholds are provisional.

Search and assault now have separate **accounting commitments**. BASE_SEARCH_COMMITTED records an actual normal retaliation UFO spawn; BASE_ASSAULT_COMMITTED records a spawned UFO on the direct base-assault trajectory. Search is charged once per parent mission, while every assault is charged separately using its unique UFO identity. Neither detecting a base nor requesting retaliation grants a free assault.

This is not yet operational separation: the stock parent AlienMission still progresses from searching to assaulting automatically. Shadow mode records a WOULD_BLOCK assault when its capability or allocation is unavailable but does not stop it. Before enforcement, that transition must become a queued assault request that independently reserves resources. Search wave composition still includes stock larger ships; independent search fleet capability rules must be settled too.

Stock-code comparison: xcom1/missionScripts.rul enables recon from month 1 and invasion from month 6. Recurring retaliation becomes eligible at zero-based month 10 on Superhuman, 11 on Genius, 12 on Veteran, 13 on Experienced, and 14 on Beginner, subject to its conditional/research logic. Alien raceWeights also change with elapsed months. The scheduler runs eligible script commands once at monthly scheduling; this inspected ruleset has no universal twelve-month alien-resource ramp. A transition toward locally earned income over roughly 12–18 months is the intended feel, not a recovered stock economy.

## Engine facts and coverage

Opt-in AlienCommandAudit records MISSION_COMMITTED at the common AlienMission::start path, after a non-interrupted start. This covers scheduler, shootdown retaliation, supply, base-generated, and event-generated operations that use that path. It records productive score events for harvest/abduction and completed-flight events for research/probe. Facts are persisted in the existing authoritative save ledger and its JSONL sidecar, and consume no RNG.

The reporting harness replays these facts deterministically. It also admits older decision receipts as historical commitment evidence, deduplicating the same mission ID across a start and decision receipt. Legacy active missions with unknown start time remain UNKNOWN: the report does not invent a start month, subtract their cost from an arbitrary month, or give them a reward. Legacy receipts cannot establish complete historical automatic mission or gain coverage; a report warns about that gap. Missing historical bonuses are not evidence that aliens accomplished nothing.

The replay shows actual recorded costs even when they exceed the hypothetical allocation or violate capability prerequisites. WOULD_BLOCK means a future enforcement gate would have refused that commitment; it does not mean the existing mission was stopped. Only costs for fully covered history can support balance conclusions.

## Run

From G:\OpenXcom:

```powershell
.\scripts\audit-alien-budget.ps1 -Save "G:\OpenXcom\build\local\user\xcom1\Crash-ed.sav"
```

Report: `build/local/budget-reports/Crash-ed.budget.json`. It contains policy/source hashes, monthly allocation, commitment receipts, verified gains, progress, hypothetical eligibility, and explicit coverage warnings. Reading a save never modifies it. Re-running the same save reproduces accounting and cannot accumulate bonuses across runs. Each campaign branch reconstructs its own ledger; no external shared bonus state exists.

For further observed engine facts, use the rebuilt development runtime with -Audit, -ModelAudit, or -ModelExecute, save normally, then run the report. The latter still controls only operation execution, not budget enforcement.

## Next enforcement boundary

Before turning this into campaign limits:

1. Define separate search and assault commitments and validate every UFO wave against deployed capabilities.
2. Centralize reservation before *all* operation starts; reject unaffordable or ineligible requests without changing mission IDs, strategy tables, or RNG. Handle failed starts and reservations explicitly.
3. Make automatic retaliation a request against the same resources; anger never grants free craft. Decide explicitly whether it competes immediately or queues for allocation.
4. Persist authoritative budget/progression in the save rather than treating this debug report as game state. Rollovers and gain rewards must remain idempotent after reload.
5. Give the model only the resulting affordable eligible menu plus alien-owned allocation and progress, with recorded exclusion reasons. Supply and event obligations must compete too.
6. Test paired campaign branches with identical seeds and report missing historical coverage separately. Keep original difficulty numbers until downstream balance evidence justifies changes.

No live budget enforcement or technology-driven wave changes are claimed by this prototype.

The initial reward and operation-cost contracts target UFO Defense. TFTD calendar replay starts in 2040, and probe completion is recorded, but interdiction, resource raids, ship attacks, and artifact missions remain explicitly UNPRICED until their own contracts are defined. They must not silently inherit UFO Defense semantics.

Validation: 15 Python budget checks; native engine checks 64 for UFO and 60 for TFTD, including common start, research completion, productive activity in UFO, provenance, and save/load. A real engine fixture produces exactly 3 unique verified gains and 5 pending bonus units, with no save mutation. Historical campaign replay exposes its coverage gaps.

Pressure v2 validation adds separate real engine search/assault spawn receipts and checks difficulty scaling and the first-year plateau. Original difficulty coefficients remain unchanged.

A new search/assault deployment from an older operation can still be charged at its observed deployment time without inventing the parent start time. That uncertainty remains a coverage warning. Pressure-v2 checks passed: 19 Python budget cases and native engine checks 68 (UFO) / 64 (TFTD), including actual search and assault UFO spawns.


## Clarified long-run economy

The allowance is off-world support, not the aliens' entire budget. Its automatic growth tapers over roughly 12–18 months. Baseline transfers can persist, but additional Earth capacity must increasingly be earned. The intended equilibrium is not a fixed total allocation: it is a balance among productive infrastructure, successful operations, recurring maintenance, and losses.

The eighteen-month tables only prototype that allowance component. The report exposes earthIncomeStatus=NOT_YET_ACCOUNTED so its present totals cannot be mistaken for a complete long-run economy. The user described this pressure trajectory as their experience of playing X-COM; it is a design target rather than a verified original-game formula.

Productive alien bases should earn recurring income while they remain operational, with upkeep and adequate supply. Destroying or isolating a base should reduce that flow. Merely counting constructed bases must not mint permanent unrestricted income. Supply missions should deliver support that sustains or restores production; do not award a full delivery windfall and count the same resources again as base output. Harvesting, abduction, and research gains remain distinct verified contributions to materials, adaptation, and capability development.

Before income enforcement we need observed base commissioning/destruction, supply completion, supply state/maintenance contracts, and provenance for recurring production. A vanished supply UFO or a still-existing base cannot establish those outcomes retrospectively. Early receipts and a base-income/supply replay fixture must be added before presenting a full economy simulation.

Difficulty should govern off-world support, deployment capacity, and income/upkeep efficiency explicitly, without using hidden X-COM wealth or performance as an automatic subsidy. The provisional allowance curves are editable and do not change the engine's existing difficulty modifiers.


## Portfolio execution mode
The separate native monthly portfolio is now documented in [ALIEN_COMMAND_PORTFOLIO.md](ALIEN_COMMAND_PORTFOLIO.md). The earlier sections describe the historical shadow report, not the new executable ledger.
