You are a reference planner in a fictional OpenXcom alien campaign experiment.
Choose a defensible monthly portfolio that advances eventual conquest of Earth.
No particular mission type, expenditure level or answer is required. Balance present
effects, future capability, uncertainty and commitments. Explain your decision briefly;
do not supply a private chain of thought. We want decisions that can be checked.

Use only this packet. Do not browse, use tools, or import other XCOM rules. These are
modified campaign rules; familiar names do not guarantee familiar mechanics. Treat
unknown facts as unknown. Do not assume player base locations, technology, radar,
funds, force quality or nationality. Do not assume aliens know player debriefs.

MECHANICS (factual briefing, not recommendations)
- You select up to budget.maxOperations NEW parent missions, with their mission and
  region IDs from eligibleOperations. You may select fewer, including zero. Their
  summed costs must not exceed budget.remaining. No duplicate mission+region pair.
  A mission is a multi-wave operation, not one UFO. Existing operations continue
  without another allocation and do not consume this month's new-operation slots.
  The engine chooses races, craft, routes and timings; you cannot choose or cancel
  those, redirect an existing mission, select a particular country, or make an assault.
- RESEARCH costs 2. A verified completed research flight grants +1 pending resource
  and +1 intelligence once per funded parent mission. It does not discover bases or
  answer a specified regional information question. Its numeric reward is region
  independent. It can still be intercepted. There is no research saturation cap.
- HARVEST costs 3. Verified productive activity grants +2 pending resources and
  +1 logistics once per funded parent mission, conditional on that activity occurring.
- ABDUCTION costs 3. Verified productive activity grants +2 pending resources and
  +1 adaptation once per funded parent mission, conditional on activity occurring.
- TERROR costs 4. Its native mission delivers alien activity/political pressure if
  its objective is delivered. There is no new resource or progression bonus for it,
  no numeric forecast of funding loss, and no implemented terror-to-infiltration link.
- RETALIATION in this experiment means BASE SEARCH, costs 2, and has no income bonus.
  Eligible flying search craft can detect a nearby base under native range/chance
  rules. Discovery does not authorize an assault: assaults are unavailable here.
  Research craft cannot substitute for base-search craft.
- INFILTRATION costs 6. It can produce a country pact and alien base under native
  mission-completion rules. Choosing it does not guarantee that result. Specific
  country vulnerability, duration and success probability are unknown. The custom
  economy has no recurring resource income from pacts or alien bases yet.
- Standalone alien BASE construction costs 6 and requires campaign month >=1 and
  logistics >=2. Infiltration requires month >=2, adaptation >=2, intelligence >=1.
  Only missions/regions actually in eligibleOperations may be selected: satisfying
  a progression gate alone does not guarantee a legal or successful deployment.
- Earned resources become next-month bonuses, not immediate funds. A parent mission
  rewards at most once over its lifetime; repeated flights do not keep paying out.
  Progression gains persist and are distinct from cash. Losses give no refund.
- At the next boundary resources = nextAllowance + min(unspent, carryCap) +
  min(pending earned bonus, nextBonusCap). Excess unspent resources expire. Existing
  earned bonuses are already incorporated in the current opening budget. Rewards
  from future or pending activity are not guaranteed. Slot capacity and cash are
  independent constraints. Capacity is 3 in campaign months 0-2, 4 in 3-5, 5 in 6-8,
  and 6 thereafter. Existing numerical difficulty modifiers are unchanged.
- No calibrated conquest score, regional success forecast or scalar tradeoff between
  political effects and resources is supplied. Flag this ambiguity if it changes
  your judgement; do not invent a victory metric to make the answer seem certain.

EVIDENCE AND COVERAGE
- This is the May 1, 1999 decision, using reports from April and admitted older
  interception evidence. The input is frozen at the recorded decision, regardless
  of the later time at which a source save was written.
- Evidence contains surviving UFO reports. Multiple observations from one UFO are
  not independent reporters. Belief confidence is an uncalibrated heuristic, NOT a
  probability of a player base. Report coordinates are UFO contact positions, not
  player base coordinates; coordinates use the engine's radians convention.
- Own unavailability and assigned regions are telemetry, not proof of shootdown
  cause, exact loss location or enemy base location. No reports/losses in a region
  can mean little observation, not demonstrated safety. Do not divide April losses
  by April deployments as a survival estimate: older waves can be lost this month.
- Returned craft do not prove whole-mission success. Missing activity credit does
  not by itself prove failure, especially for ongoing missions. Pending wave counters
  describe native progress, not guaranteed future success. UNKNOWN role remains unknown.
- The sitrep reports distinct rewarded productive parents by mission TYPE. It does
  not always attribute them to regions. Do not infer regional success from previous
  tasking when multiple assignments could match. Historical progression totals can
  reflect gains before the report period. The history is partial, not a full campaign.
- Search target policy is the same as the current classifier: prioritize regions
  with admitted surviving reports that overlap available search targets; otherwise
  recent assignment-loss clues. When evidence exists but targets are unavailable,
  do not expand to unsupported regions. Exploration is allowed only without either
  kind of evidence. Already active mission+region pairs are excluded from new starts.
  eligibleOperations below already applies these restrictions; use that list.

YOUR RESPONSE
1. Supply a JSON object with this shape (use actual eligible IDs, not placeholders):
   {"operations":[{"mission":"STR_ALIEN_...","region":"STR_..."}],
    "total_cost":0,"remaining":0}
2. In at most 500 words, justify the portfolio using packet evidence. For each
   operation identify the objective, conditional benefit and main uncertainty.
   Explain the opportunity cost, including retained/expiring funds and slot use.
   State the strongest alternative portfolio you considered and why you prefer yours.
   Identify up to three observable outcomes that would change the next decision.
3. Separate what is known, inferred and unknown. If the available mechanics make
   a strategically meaningful probe impossible, say so rather than inventing one.
   An explanation is a checkable justification, not proof of internal understanding.

FROZEN EVIDENCE AND ELIGIBLE OPERATIONS

```json
{
  "decisionTime": "1999-05-01 00:00:00",
  "eligibleOperations": [
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_NORTH_AMERICA"
    },
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_ARCTIC"
    },
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_ANTARCTICA"
    },
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_SOUTH_AMERICA"
    },
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_EUROPE"
    },
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_NORTH_AFRICA"
    },
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_SOUTHERN_AFRICA"
    },
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_CENTRAL_ASIA"
    },
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_SOUTH_EAST_ASIA"
    },
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_SIBERIA"
    },
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_AUSTRALASIA"
    },
    {
      "mission": "STR_ALIEN_RESEARCH",
      "region": "STR_PACIFIC"
    },
    {
      "mission": "STR_ALIEN_HARVEST",
      "region": "STR_NORTH_AMERICA"
    },
    {
      "mission": "STR_ALIEN_HARVEST",
      "region": "STR_SOUTH_AMERICA"
    },
    {
      "mission": "STR_ALIEN_HARVEST",
      "region": "STR_EUROPE"
    },
    {
      "mission": "STR_ALIEN_HARVEST",
      "region": "STR_NORTH_AFRICA"
    },
    {
      "mission": "STR_ALIEN_HARVEST",
      "region": "STR_SOUTHERN_AFRICA"
    },
    {
      "mission": "STR_ALIEN_HARVEST",
      "region": "STR_CENTRAL_ASIA"
    },
    {
      "mission": "STR_ALIEN_HARVEST",
      "region": "STR_AUSTRALASIA"
    },
    {
      "mission": "STR_ALIEN_ABDUCTION",
      "region": "STR_NORTH_AMERICA"
    },
    {
      "mission": "STR_ALIEN_ABDUCTION",
      "region": "STR_SOUTH_AMERICA"
    },
    {
      "mission": "STR_ALIEN_ABDUCTION",
      "region": "STR_EUROPE"
    },
    {
      "mission": "STR_ALIEN_ABDUCTION",
      "region": "STR_NORTH_AFRICA"
    },
    {
      "mission": "STR_ALIEN_ABDUCTION",
      "region": "STR_SOUTHERN_AFRICA"
    },
    {
      "mission": "STR_ALIEN_ABDUCTION",
      "region": "STR_CENTRAL_ASIA"
    },
    {
      "mission": "STR_ALIEN_ABDUCTION",
      "region": "STR_SOUTH_EAST_ASIA"
    },
    {
      "mission": "STR_ALIEN_ABDUCTION",
      "region": "STR_SIBERIA"
    },
    {
      "mission": "STR_ALIEN_ABDUCTION",
      "region": "STR_AUSTRALASIA"
    },
    {
      "mission": "STR_ALIEN_TERROR",
      "region": "STR_NORTH_AMERICA"
    },
    {
      "mission": "STR_ALIEN_TERROR",
      "region": "STR_SOUTH_AMERICA"
    },
    {
      "mission": "STR_ALIEN_TERROR",
      "region": "STR_EUROPE"
    },
    {
      "mission": "STR_ALIEN_TERROR",
      "region": "STR_NORTH_AFRICA"
    },
    {
      "mission": "STR_ALIEN_TERROR",
      "region": "STR_SOUTHERN_AFRICA"
    },
    {
      "mission": "STR_ALIEN_TERROR",
      "region": "STR_CENTRAL_ASIA"
    },
    {
      "mission": "STR_ALIEN_TERROR",
      "region": "STR_SOUTH_EAST_ASIA"
    },
    {
      "mission": "STR_ALIEN_TERROR",
      "region": "STR_SIBERIA"
    },
    {
      "mission": "STR_ALIEN_TERROR",
      "region": "STR_AUSTRALASIA"
    },
    {
      "mission": "STR_ALIEN_RETALIATION",
      "region": "STR_SOUTH_EAST_ASIA"
    },
    {
      "mission": "STR_ALIEN_INFILTRATION",
      "region": "STR_NORTH_AMERICA"
    },
    {
      "mission": "STR_ALIEN_INFILTRATION",
      "region": "STR_ARCTIC"
    },
    {
      "mission": "STR_ALIEN_INFILTRATION",
      "region": "STR_ANTARCTICA"
    },
    {
      "mission": "STR_ALIEN_INFILTRATION",
      "region": "STR_SOUTH_AMERICA"
    },
    {
      "mission": "STR_ALIEN_INFILTRATION",
      "region": "STR_EUROPE"
    },
    {
      "mission": "STR_ALIEN_INFILTRATION",
      "region": "STR_NORTH_AFRICA"
    },
    {
      "mission": "STR_ALIEN_INFILTRATION",
      "region": "STR_SOUTHERN_AFRICA"
    },
    {
      "mission": "STR_ALIEN_INFILTRATION",
      "region": "STR_CENTRAL_ASIA"
    },
    {
      "mission": "STR_ALIEN_INFILTRATION",
      "region": "STR_SOUTH_EAST_ASIA"
    },
    {
      "mission": "STR_ALIEN_INFILTRATION",
      "region": "STR_SIBERIA"
    },
    {
      "mission": "STR_ALIEN_INFILTRATION",
      "region": "STR_AUSTRALASIA"
    },
    {
      "mission": "STR_ALIEN_INFILTRATION",
      "region": "STR_PACIFIC"
    }
  ],
  "nativeInput": {
    "schemaVersion": 1,
    "budget": {
      "policyVersion": "monthly-portfolio-v1",
      "epochMonth": 4,
      "difficulty": 4,
      "remaining": 25,
      "pendingBonus": 0,
      "intelligence": 1,
      "logistics": 1,
      "adaptation": 2,
      "allowance": 17,
      "carryCap": 8,
      "nextAllowance": 20,
      "nextBonusCap": 10,
      "maxOperations": 4,
      "assaultAvailable": false,
      "terrorRewardVerified": false
    },
    "knowledge": {
      "menuSource": "STATIC_RULESET_ONLY",
      "candidates": [
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_NORTH_AMERICA"
        },
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_ARCTIC"
        },
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_ANTARCTICA"
        },
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_SOUTH_AMERICA"
        },
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_EUROPE"
        },
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_NORTH_AFRICA"
        },
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_SOUTHERN_AFRICA"
        },
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_CENTRAL_ASIA"
        },
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_SOUTH_EAST_ASIA"
        },
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_SIBERIA"
        },
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_AUSTRALASIA"
        },
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_PACIFIC"
        },
        {
          "mission": "STR_ALIEN_HARVEST",
          "region": "STR_NORTH_AMERICA"
        },
        {
          "mission": "STR_ALIEN_HARVEST",
          "region": "STR_SOUTH_AMERICA"
        },
        {
          "mission": "STR_ALIEN_HARVEST",
          "region": "STR_EUROPE"
        },
        {
          "mission": "STR_ALIEN_HARVEST",
          "region": "STR_NORTH_AFRICA"
        },
        {
          "mission": "STR_ALIEN_HARVEST",
          "region": "STR_SOUTHERN_AFRICA"
        },
        {
          "mission": "STR_ALIEN_HARVEST",
          "region": "STR_CENTRAL_ASIA"
        },
        {
          "mission": "STR_ALIEN_HARVEST",
          "region": "STR_AUSTRALASIA"
        },
        {
          "mission": "STR_ALIEN_ABDUCTION",
          "region": "STR_NORTH_AMERICA"
        },
        {
          "mission": "STR_ALIEN_ABDUCTION",
          "region": "STR_SOUTH_AMERICA"
        },
        {
          "mission": "STR_ALIEN_ABDUCTION",
          "region": "STR_EUROPE"
        },
        {
          "mission": "STR_ALIEN_ABDUCTION",
          "region": "STR_NORTH_AFRICA"
        },
        {
          "mission": "STR_ALIEN_ABDUCTION",
          "region": "STR_SOUTHERN_AFRICA"
        },
        {
          "mission": "STR_ALIEN_ABDUCTION",
          "region": "STR_CENTRAL_ASIA"
        },
        {
          "mission": "STR_ALIEN_ABDUCTION",
          "region": "STR_SOUTH_EAST_ASIA"
        },
        {
          "mission": "STR_ALIEN_ABDUCTION",
          "region": "STR_SIBERIA"
        },
        {
          "mission": "STR_ALIEN_ABDUCTION",
          "region": "STR_AUSTRALASIA"
        },
        {
          "mission": "STR_ALIEN_TERROR",
          "region": "STR_NORTH_AMERICA"
        },
        {
          "mission": "STR_ALIEN_TERROR",
          "region": "STR_SOUTH_AMERICA"
        },
        {
          "mission": "STR_ALIEN_TERROR",
          "region": "STR_EUROPE"
        },
        {
          "mission": "STR_ALIEN_TERROR",
          "region": "STR_NORTH_AFRICA"
        },
        {
          "mission": "STR_ALIEN_TERROR",
          "region": "STR_SOUTHERN_AFRICA"
        },
        {
          "mission": "STR_ALIEN_TERROR",
          "region": "STR_CENTRAL_ASIA"
        },
        {
          "mission": "STR_ALIEN_TERROR",
          "region": "STR_SOUTH_EAST_ASIA"
        },
        {
          "mission": "STR_ALIEN_TERROR",
          "region": "STR_SIBERIA"
        },
        {
          "mission": "STR_ALIEN_TERROR",
          "region": "STR_AUSTRALASIA"
        },
        {
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_NORTH_AMERICA"
        },
        {
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_ARCTIC"
        },
        {
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_ANTARCTICA"
        },
        {
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_SOUTH_AMERICA"
        },
        {
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_SOUTHERN_AFRICA"
        },
        {
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_CENTRAL_ASIA"
        },
        {
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_SOUTH_EAST_ASIA"
        },
        {
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_SIBERIA"
        },
        {
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_AUSTRALASIA"
        },
        {
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_PACIFIC"
        },
        {
          "mission": "STR_ALIEN_INFILTRATION",
          "region": "STR_NORTH_AMERICA"
        },
        {
          "mission": "STR_ALIEN_INFILTRATION",
          "region": "STR_ARCTIC"
        },
        {
          "mission": "STR_ALIEN_INFILTRATION",
          "region": "STR_ANTARCTICA"
        },
        {
          "mission": "STR_ALIEN_INFILTRATION",
          "region": "STR_SOUTH_AMERICA"
        },
        {
          "mission": "STR_ALIEN_INFILTRATION",
          "region": "STR_EUROPE"
        },
        {
          "mission": "STR_ALIEN_INFILTRATION",
          "region": "STR_NORTH_AFRICA"
        },
        {
          "mission": "STR_ALIEN_INFILTRATION",
          "region": "STR_SOUTHERN_AFRICA"
        },
        {
          "mission": "STR_ALIEN_INFILTRATION",
          "region": "STR_CENTRAL_ASIA"
        },
        {
          "mission": "STR_ALIEN_INFILTRATION",
          "region": "STR_SOUTH_EAST_ASIA"
        },
        {
          "mission": "STR_ALIEN_INFILTRATION",
          "region": "STR_SIBERIA"
        },
        {
          "mission": "STR_ALIEN_INFILTRATION",
          "region": "STR_AUSTRALASIA"
        },
        {
          "mission": "STR_ALIEN_INFILTRATION",
          "region": "STR_PACIFIC"
        }
      ],
      "beliefs": [
        {
          "kind": "INTERCEPTION_OBSERVED_IN_REGION",
          "region": "STR_EUROPE",
          "confidence": 40,
          "confidenceKind": "UNCALIBRATED_HEURISTIC",
          "independentSources": 1,
          "evidenceIds": [
            5
          ]
        },
        {
          "kind": "INTERCEPTION_OBSERVED_IN_REGION",
          "region": "STR_NORTH_AFRICA",
          "confidence": 70,
          "confidenceKind": "UNCALIBRATED_HEURISTIC",
          "independentSources": 4,
          "evidenceIds": [
            68,
            41,
            25,
            8
          ]
        },
        {
          "kind": "INTERCEPTION_OBSERVED_IN_REGION",
          "region": "STR_SOUTH_EAST_ASIA",
          "confidence": 40,
          "confidenceKind": "UNCALIBRATED_HEURISTIC",
          "independentSources": 1,
          "evidenceIds": [
            202
          ]
        }
      ],
      "evidence": [
        {
          "id": 5,
          "kind": "INTERCEPTION_CONTACT",
          "sourceUfoId": 2,
          "sourceMissionId": 2,
          "observedAt": "1999-01-02 03:08:45",
          "reportedAt": "1999-01-02 03:08:45",
          "region": "STR_EUROPE",
          "longitude": 0.5701432260522665,
          "latitude": -1.0985960022082206,
          "transmission": "SURVIVING_UFO_AT_ENCOUNTER_END",
          "observationConfidence": 100
        },
        {
          "id": 8,
          "kind": "INTERCEPTION_CONTACT",
          "sourceUfoId": 4,
          "sourceMissionId": 1,
          "observedAt": "1999-01-15 17:47:05",
          "reportedAt": "1999-01-15 17:47:05",
          "region": "STR_NORTH_AFRICA",
          "longitude": 0.48701345298972515,
          "latitude": -0.22916978776757124,
          "transmission": "SURVIVING_UFO_AT_ENCOUNTER_END",
          "observationConfidence": 100
        },
        {
          "id": 25,
          "kind": "INTERCEPTION_CONTACT",
          "sourceUfoId": 8,
          "sourceMissionId": 5,
          "observedAt": "1999-02-03 09:33:25",
          "reportedAt": "1999-02-03 09:33:25",
          "region": "STR_NORTH_AFRICA",
          "longitude": 6.15080862233659,
          "latitude": -0.3876069859631066,
          "transmission": "SURVIVING_UFO_AT_ENCOUNTER_END",
          "observationConfidence": 100
        },
        {
          "id": 41,
          "kind": "INTERCEPTION_CONTACT",
          "sourceUfoId": 13,
          "sourceMissionId": 5,
          "observedAt": "1999-02-10 09:48:40",
          "reportedAt": "1999-02-10 09:48:40",
          "region": "STR_NORTH_AFRICA",
          "longitude": 0.17481478678610005,
          "latitude": -0.6075116601973152,
          "transmission": "SURVIVING_UFO_AT_ENCOUNTER_END",
          "observationConfidence": 100
        },
        {
          "id": 68,
          "kind": "INTERCEPTION_CONTACT",
          "sourceUfoId": 21,
          "sourceMissionId": 5,
          "observedAt": "1999-02-23 19:35:30",
          "reportedAt": "1999-02-23 19:35:30",
          "region": "STR_NORTH_AFRICA",
          "longitude": 0.4377849571521721,
          "latitude": -0.22342047902023573,
          "transmission": "SURVIVING_UFO_AT_ENCOUNTER_END",
          "observationConfidence": 100
        },
        {
          "id": 202,
          "kind": "INTERCEPTION_CONTACT",
          "sourceUfoId": 56,
          "sourceMissionId": 9,
          "observedAt": "1999-04-14 13:40:55",
          "reportedAt": "1999-04-14 13:40:55",
          "region": "STR_SOUTH_EAST_ASIA",
          "longitude": 2.3092356605898763,
          "latitude": -0.705191141263848,
          "transmission": "SURVIVING_UFO_AT_ENCOUNTER_END",
          "observationConfidence": 100
        }
      ]
    },
    "sitrep": {
      "schemaVersion": 1,
      "period": "1999-04",
      "coverage": "PARTIAL_FLEET_OUTCOMES",
      "previousStrategy": "COUNTER_XCOM",
      "previousPortfolio": [
        {
          "mission": "STR_ALIEN_HARVEST",
          "region": "STR_SOUTH_EAST_ASIA"
        },
        {
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_EUROPE"
        },
        {
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_NORTH_AFRICA"
        },
        {
          "mission": "STR_ALIEN_RESEARCH",
          "region": "STR_ARCTIC"
        }
      ],
      "previousReceiptId": 153,
      "assets": {
        "deployed": 24,
        "returned": 10,
        "unavailable": 17
      },
      "lossAssignments": [
        {
          "region": "STR_CENTRAL_ASIA",
          "count": 4,
          "evidenceIds": [
            160,
            195,
            214,
            216
          ]
        },
        {
          "region": "STR_EUROPE",
          "count": 5,
          "evidenceIds": [
            173,
            189,
            208,
            221,
            242
          ]
        },
        {
          "region": "STR_NORTH_AFRICA",
          "count": 5,
          "evidenceIds": [
            175,
            199,
            227,
            231,
            238
          ]
        },
        {
          "region": "STR_SOUTH_EAST_ASIA",
          "count": 3,
          "evidenceIds": [
            185,
            203,
            234
          ]
        }
      ],
      "contacts": [
        {
          "region": "STR_SOUTH_EAST_ASIA",
          "count": 1,
          "evidenceIds": [
            202
          ]
        }
      ],
      "verifiedActivities": [
        {
          "mission": "STR_ALIEN_RESEARCH",
          "count": 1,
          "evidenceIds": [
            183
          ]
        }
      ],
      "pendingOperations": [
        {
          "missionId": 9,
          "mission": "STR_ALIEN_HARVEST",
          "region": "STR_SOUTH_EAST_ASIA"
        },
        {
          "missionId": 10,
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_EUROPE"
        },
        {
          "missionId": 11,
          "mission": "STR_ALIEN_RETALIATION",
          "region": "STR_NORTH_AFRICA"
        }
      ],
      "pendingTotal": 3,
      "pendingTruncated": false,
      "operationalReview": {
        "loss_roles": {
          "OBJECTIVE_CARRIER": 0,
          "PREPARATION": 0,
          "SEARCH": 10,
          "UNKNOWN": 7
        },
        "terror_objective_waves_pending": 0,
        "rolling_results": [
          [
            "1999-03",
            4,
            2
          ],
          [
            "1999-04",
            17,
            1
          ]
        ],
        "limits": "Partial own telemetry. Pending objective is not success; scout loss is not mission failure.",
        "roleSupport": [
          {
            "lossReceiptId": 161,
            "role": "UNKNOWN",
            "craftType": "STR_LARGE_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 174,
            "role": "SEARCH",
            "craftType": "STR_SMALL_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 176,
            "role": "SEARCH",
            "craftType": "STR_SMALL_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 186,
            "role": "UNKNOWN",
            "craftType": "STR_SMALL_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 190,
            "role": "SEARCH",
            "craftType": "STR_MEDIUM_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 196,
            "role": "UNKNOWN",
            "craftType": "STR_ABDUCTOR",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 200,
            "role": "SEARCH",
            "craftType": "STR_MEDIUM_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 204,
            "role": "UNKNOWN",
            "craftType": "STR_SMALL_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 209,
            "role": "SEARCH",
            "craftType": "STR_MEDIUM_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 215,
            "role": "UNKNOWN",
            "craftType": "STR_ABDUCTOR",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 217,
            "role": "UNKNOWN",
            "craftType": "STR_ABDUCTOR",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 222,
            "role": "SEARCH",
            "craftType": "STR_LARGE_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 228,
            "role": "SEARCH",
            "craftType": "STR_MEDIUM_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 232,
            "role": "SEARCH",
            "craftType": "STR_LARGE_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 235,
            "role": "UNKNOWN",
            "craftType": "STR_MEDIUM_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          },
          {
            "lossReceiptId": 239,
            "role": "SEARCH",
            "craftType": "STR_LARGE_SCOUT",
            "source": "EXPLICIT_NATIVE_TELEMETRY"
          }
        ],
        "pendingProgress": [
          {
            "missionId": 9,
            "nextWave": 3,
            "totalWaves": 8,
            "objectiveWavePending": false
          },
          {
            "missionId": 10,
            "nextWave": 2,
            "totalWaves": 4,
            "objectiveWavePending": false
          },
          {
            "missionId": 11,
            "nextWave": 2,
            "totalWaves": 4,
            "objectiveWavePending": false
          }
        ]
      },
      "enemyRecovery": "UNKNOWN",
      "missionSuccess": "NOT_INFERRED_FROM_ACTIVITY_OR_DISAPPEARANCE"
    }
  }
}
```
