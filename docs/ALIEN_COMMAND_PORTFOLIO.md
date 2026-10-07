# Budget-aware monthly portfolio: first execution test

This mode replaces routine monthly alien mission scripts with one learned portfolio of zero to three operations. It is an execution test, not shadow accounting. Original difficulty coefficients are unchanged.

From `G:\OpenXcom`, run:

```powershell
.\scripts\run-local.ps1 -Portfolio
```

For the clean comparison, load `Pre-february.sav`, advance across February 1, and save under a new name. Keep the original pre-February and latest March saves. A later save also works, with its next monthly boundary as the decision point. Already-running missions continue; historical spending and rewards are not reconstructed. The native ledger starts a new accounting epoch when portfolio mode first needs resources.

The model sees its own remaining allocation, progress, pending bonus, a rules-derived operation menu, and admitted surviving interception reports. It does not receive XCOM funds, undiscovered bases, radar coverage, or locations of lost UFO encounters. Regions without reports are available and explicitly carry unknown risk.

The classifier first chooses a monthly strategy from the previous-month sitrep, then chooses an objective and its region, and repeats with the remaining budget. At every objective choice it can save remaining resources and end the portfolio. This hierarchy keeps the existing checkpoint's small token window usable without silently truncating packets. It does not imply that this career-trained checkpoint understands XCOM strategy.

Initial selectable objectives are research/probe, harvest, abduction, terror/surface attack where their rules exist, and base search, plus base establishment and infiltration when their native progression prerequisites are met. The engine filters valid trajectories, geography, and already-active mission/region pairs. The complete proposed portfolio is checked for menu membership, duplicates, prerequisites, a maximum of three operations, and total cost before any mission starts. Resources for the accepted portfolio are reserved together. The engine still selects races and executes stock waves and trajectories.

New mission starts outside the portfolio, including retaliation requests, must use the same native budget while this mode is enabled. An unpriced, unaffordable, or ineligible start is interrupted and audited. Such rejected callers may already have consumed their own RNG/mission ID before reaching the common gate; they do not get free deployments. The three-operation limit applies to the monthly portfolio, not separately funded event/reaction requests.

Search costs two units once per parent mission and is operationally separated from assault. Discovery interrupts the search before the stock engine can deploy an assault. Assault selection remains unavailable in v1, including for existing retaliation operations while portfolio mode is enabled. Search operations funded by this mode retain their no-assault restriction after changing launch modes.

The allowance uses the agreed difficulty-specific eighteen-month curves, then holds baseline support constant. Carry is limited to half the current allowance. Verified research flight completion earns one next-month bonus/intelligence unit; verified harvest/abduction activity earns two bonus units and one logistics/adaptation unit, once per funded parent mission. Next-month bonus is capped at half that month's allowance. Rewards from historical, unfunded missions are excluded from this new epoch. Logistics and adaptation/intelligence unlock prerequisites for infrastructure and infiltration starts.

The authoritative budget, commitments, completed rewards, progress, and last portfolio month persist in `alienCommand.budget`. Reloading does not allocate, reward, or execute the same month twice. The current native policy is `monthly-portfolio-v1`; the JSON shadow policy remains a separate report prototype and editing it does not change native execution costs/curves.

The audit records `portfolio` receipts with the full input, raw model response (including each choice's probabilities and prompt), final budget, and result. Common mission facts distinguish enforced accounting from shadow accounting. The offline audit viewer supports these receipts. Failed/unavailable inference saves resources for that monthly decision, with an explicit receipt; it does not silently restore a second monthly scheduler.

Still staged: independently selectable funded assaults, productive-base/supply income, verified terror economic rewards, broader TFTD mission contracts. Terror currently produces its stock political effects but receives no unverified economic bonus. Do not treat this version as the completed long-run economy or as balanced difficulty.

Validation commands:

```powershell
.\scripts\test-alien-command-portfolio.ps1
.\build\local\laya-venv\Scripts\python.exe -m unittest discover -s tests -p 'test_alien_command*.py'
```

The scripted portfolio fixtures test real engine wiring and rejection behavior, not learned strategy. The checkpoint probe is recorded separately.
Validated locally on 2026-10-06: clean native rebuild plus final incremental build succeeded. Python boundary/replay tests: 36 passed. Actual native portfolio fixture runs passed for both masters: accepted portfolio 97 checks (UFO) / 93 (TFTD); save, invalid menu, duplicate and over-budget cases each 95 / 91. Actual checkpoint through the monthly game entry point passed 96 / 92 checks. It chose SAVE_RESOURCES in both fresh test campaigns, leaving six units and no newly scheduled missions; this verifies wiring and persistence, not strategic quality. Exact learned receipts are in `build/local/portfolio-real-model-xcom1.json` and `portfolio-real-model-xcom2.json`. Viewer JavaScript syntax checked; visual layout was not verified.
Historical conquest prompt revision: `conquest-tradeoffs-v2` explicitly states conquest as the goal and describes productive capacity, political pressure, information gathering, commitment loss, uncertain exposure, and allowance expiry. Saving remains valid, with its opportunity cost stated. The launcher rejects a still-running service with an older prompt version; restart the game/model session and reload the comparison save to use this revision. No checkpoint weights or native budget rules changed. A read-only replay of the February campaign input passed the model token guard (477 tokens) and still chose SAVE_RESOURCES; this is evidence that reframing alone did not resolve the observed inaction preference. Previously selected operation names are summarized compactly so later portfolio slots retain token room.

Current revision: `alien-strategy-laya-v2` / `sitrep-strategy-v3` adds a deterministic native monthly sitrep and a learned strategy stage before mixed operation/target choices. See [strategy and sitrep contract](ALIEN_COMMAND_STRATEGY_SITREP.md). Own deployment, return and unavailable-craft receipts persist; unavailable craft are reported by their own assigned region, with unknown enemy cause/recovery. Older saves have partial reporting coverage. Exact native sitrep and all model prompts/choices are retained in each portfolio receipt.

Live context/deferral revision: `roles-defer-v4` adds own craft roles, native mission progress and a two-month review. The SAVE choice explicitly describes carry and forfeiture. Close the earlier game/model session and relaunch Portfolio to use the new service and executable; reload February 28 for the March comparison.
