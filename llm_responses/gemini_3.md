JSON
{
  "operations": [
    {
      "mission": "STR_ALIEN_ABDUCTION",
      "region": "STR_NORTH_AFRICA"
    },
    {
      "mission": "STR_ALIEN_HARVEST",
      "region": "STR_SOUTH_EAST_ASIA"
    },
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_EUROPE"
    }
  ],
  "total_cost": 8,
  "remaining": 17
}
Portfolio Justification
This portfolio balances resource generation, adaptation progression, and intelligence acquisition under the May 1, 1999 decision constraints while respecting evidence-based tasking policies.

STR_ALIEN_ABDUCTION in STR_NORTH_AFRICA (Cost: 3): Targets a region with robust historical contact evidence (70% heuristic confidence from 4 sources). Objective: Conditional +2 pending resources and +1 adaptation upon productive activity. Main uncertainty: High April loss counts in North Africa suggest hostile interception risk could disrupt completion.

STR_ALIEN_HARVEST in STR_SOUTH_EAST_ASIA (Cost: 3): Aligns with surviving contact evidence (#202) and ongoing pending progress (missionId: 9). Objective: Conditional +2 pending resources and +1 logistics. Main uncertainty: Continuation of wave progression through threat resistance.

STR_ALIEN_RESEARCH in STR_EUROPE (Cost: 2): Prioritizes a region with surviving contact history (#5) and concentrated April engagement losses. Objective: Conditional +1 pending resource and +1 intelligence. Main uncertainty: Heavy localized asset attrition.

Opportunity Cost & Budget: Total cost is 8 against a remaining budget of 25 (allowance 17), utilizing 3 of 4 available slots. Unspent funds carry over subject to carryCap (8), meaning 9 points expire, enforcing strict budgetary discipline without speculative over-tasking.

Alternative Considered: Adding an Infiltration or Terror mission was considered. However, Infiltration costs 6 and requires specific progression gates without guaranteeing pact formation, while Terror yields no resource or progression bonus. The chosen portfolio maximizes progression gains (adaptation, logistics, intelligence) required for future standalone bases.

Observable Outcomes for Next Decision:

Verification of productive activity or loss attribution for the tasked parent missions in North Africa, Southeast Asia, and Europe.

Changes in pending resource totals and progression metrics at the next monthly boundary.

Shifts in regional contact heuristics or own-craft loss distribution.

Knowledge Classification
Known (from packet telemetry & rules): Current budget parameters (remaining: 25, allowance: 17, maxOperations: 4), static slot capacities, exact costs per mission type (Research: 2, Harvest/Abduction: 3, Terror/Retaliation: 2-4, Infiltration/Base: 6), and surviving interception contact reports with associated uncalibrated heuristics.

Inferred: Regions with surviving contact histories (STR_NORTH_AFRICA, STR_EUROPE, STR_SOUTH_EAST_ASIA) represent areas of active engagement overlap, making them valid targets under search target policy constraints.

Unknown: Exact player base locations, enemy race composition, true mission success probabilities, uncalibrated victory scalar tradeoffs, and the precise cause of craft unavailability or loss location beyond explicit telemetry tags.