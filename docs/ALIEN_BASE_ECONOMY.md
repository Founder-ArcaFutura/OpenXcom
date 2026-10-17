# Persistent alien base economy

Implemented for the opt-in funded portfolio campaign. Stock campaigns retain their original mechanics.

Each surviving alien base contributes at a monthly portfolio boundary:

- 1 resource directly to the current budget, rising permanently to 2 after two distinct supplied accounting months. Multiple supplies in one month cannot skip maturation.
- One quarter-point each in intelligence, logistics and adaptation. Fractions pool across bases and persist in the commander ledger; each four base-months adds one whole point to all three tracks.
- One local influence level, or two if supplied during the preceding accounting period, capped at six per base.

An objective supply craft must finish its ground stay at its linked base to count. Preparation scouts, flyovers, shot-down craft and supplies to another location do not qualify. Each parent supply mission can reward once, even across saves. Delivery adds +1 pending resource under the existing mission-bonus cap and marks its base supplied.

Influence belongs to the physical base, not a permanent country ledger. Its host country receives 10 times the influence level in extra alien activity points per monthly credit. Native funding calculations use that activity. Within an already chosen infiltration region, native country selection prefers the highest-influence eligible host country; ties retain stock/shuffled order. Influence does not bypass country eligibility, geographical constraints, mission costs or completion rules. Native infiltration has no success probability to boost. No automatic pact is introduced. Bases outside a funding country still earn resources and progression but cannot exert country influence. Multiple bases in a country add activity pressure; infiltration preference uses the strongest surviving base rather than multiplying levels.

Destroying a base ends future income, progression, supply maturation and its infiltration preference. Earned progression and already credited resources remain; political activity already incurred is historical and is not erased. Maturity/influence and supply reward IDs are saved with each base. Monthly cursors prevent duplicate income on retries or reload. Old saves start without invented maturity, supply history or influence; a surviving base older than the current month receives one current payment when next processed, never back pay for missed months.

Base income is distinct from capped mission-completion bonuses, so infrastructure can expand capacity beyond the allowance. The existing carry cap and operation-cap progression still apply. National pacts themselves have no recurring cash income.

The model receives only its own base region, host country, monthly income and influence, with up to six footholds in its compact decision packet. It receives no hidden XCOM assets. Base investment wording now states its recurring payoff. Original source saves are not rewritten.

Initial values are balancing parameters, not empirically established difficulty settings. This adds mechanical consequences; it does not demonstrate that the current career-trained classifier will use them well.

## Validation and local runtime

The local runtime was rebuilt and installed with zero compiler errors (13 existing warnings in the final incremental build). The service and launch guard now identify progressive-portfolio-v9.

- Python regressions: 80 passed.
- Native default engine suites: UFO Defense 164 checks; TFTD 157.
- Scripted valid portfolios: UFO 179; TFTD 171.
- Scripted invalid portfolios: UFO 174; TFTD 166.
- Native tests exercise monthly scheduler credits, repeated scheduling, supplied maturation, fractional progression persistence, legacy base loading without back pay, supply completion at/away from the linked base, duplicate deliveries, and removal of destroyed bases from the own-base briefing.
- Actual installed tokenizer: six synthetic own bases with an expanded base-construction menu fit the tested sequence (maximum 441 of 512 tokens). This is a packet-size check, with no learned inference or campaign outcome claim.

Logs: build/local/base-economy-build.log, base-economy-native-tests.log, base-economy-portfolio-tests.log, base-economy-python-tests.log, and base-economy-expanded-menu-packet-check.json.

Continue an existing campaign using scripts/run-local.ps1 -Portfolio. No source save was edited and no campaign reset is required. Save before and after the next monthly boundary to inspect credits. No API calls, fine-tuning, commits or pushes were performed. Campaign balance, actual new base placement and resulting political outcomes remain to be evaluated in play.
