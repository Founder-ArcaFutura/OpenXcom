# Manual reference-planner probe: twelve responses

## Finding

This is a useful exploratory cross-section of **four provider labels, three fresh
chats each, on one frozen campaign decision**. It is not twelve independent campaign
tests or evidence of battlefield/long-term strategic superiority. The user confirms
independent fresh chats, incognito/temporary where possible. Exact displayed model
versions, modes, dates, tool settings and the complete submitted prompts are not in
these response files. Outputs are consistent with the full briefing, but prompt
identity cannot be verified from the files alone. No compact-arm results were supplied.

The substantive signal is broader than 'LLMs prefer infiltration': several responses
connect an unlocked mission to national control, and harvesting to the missing
logistics threshold, while others defend cheaper economy/search allocations. That
supports testing complete campaign portfolios as the classifier's unit of choice.
It does **not** establish an optimal portfolio or justify turning consensus into
training labels. Explanations expose proposed strategic models, not faithful internal
reasoning. Some of those proposed models contain important mistakes.

## Mechanical audit

All files in `llm_responses` were read, hashed, and parsed without repairing their
operations. `<escape>` export markup in chatgpt_1 surrounds valid JSON; the object
was extracted without changing fields. There is one portfolio object per file.
The existing frozen-menu/budget checker was used. Transcripts were not modified.

| File | New operations | Spent | Remaining | Eligible and within capacity/budget |
|---|---|---:|---:|---|
| chatgpt_1 | Research North America; harvest North Africa; abduct South East Asia; infiltrate Europe | 14 | 11 | Yes |
| chatgpt_2 | Research North Africa; harvest North Africa; abduct South East Asia; infiltrate North Africa | 14 | 11 | Yes |
| chatgpt_3 | Research North America; harvest North Africa; abduct South East Asia; infiltrate North Africa | 14 | 11 | Yes |
| claude_1 | Infiltrate South America/Australasia; harvest Southern Africa; abduct North America | 18 | 7 | Yes |
| claude_2 | Infiltrate Southern Africa; harvest South America; abduct Australasia/North America | 15 | 10 | Yes |
| claude_3 | Infiltrate South America/Australasia; harvest South America; abduct Australasia | 18 | 7 | Yes |
| gemini_1 | Infiltrate Europe; abduct North Africa; harvest South East Asia | 12 | 13 | **No: harvest South East Asia already active and absent from eligible menu** |
| gemini_2 | Infiltrate North Africa; abduct North Africa; research Europe; search South East Asia | 13 | 12 | Yes |
| gemini_3 | Abduct North Africa; harvest South East Asia; research Europe | 8 | 17 | **No: same excluded harvest** |
| grok_1 | Search South East Asia; harvest North America/Europe; infiltrate South America | 14 | 11 | Yes |
| grok_2 | Harvest North America; research Europe; abduct South America; search South East Asia | 10 | 15 | Yes |
| grok_3 | Harvest North America; research Europe/North Africa; search South East Asia | 9 | 16 | Yes |

- **10/12** portfolios satisfy the frozen native-menu, slot, duplicate and cost checks.
- **12/12** declared portfolio cost/remaining totals are correct. This does not mean
  their reward arithmetic or explanatory mechanics are all correct.
- **9/12** choose at least one infiltration; restricting to legal portfolios gives
  **8/10**. Research appears in 7 responses, abduction in 10, harvest in 11, search in
  4, terror in none. These are descriptions of this sample, not quality scores.
- Median spending is 14/25. Legal plans range from 9 to 18 spent. Spending more
  is not inherently better. Laya spent 9 on abduction plus three researches.
- Seeded random controls are all legal by construction and have median spending 11.
  That makes them useful legality/choice controls, not a measure of strategic merit.

## Qualitative review against the preregistered rubric

This first pass is a single assistant review with provider filenames visible. It is
**not blinded, independently replicated, or numerically calibrated**. The dimensions
below are kept separate; no post-hoc composite intelligence score is assigned.

### Objective coherence

Claude's responses most explicitly connect a national-control mission to a longer
campaign purpose. `claude_1`: "the closest mechanic to conquest" and harvesting
provides "a second chance at reaching logistics 2". ChatGPT's responses similarly
identify the pact/base outcome; `chatgpt_3`: "the only selected operation capable
of directly producing a pact and base". These are checkable action-to-purpose links,
not evidence the plans would win.

Calling infiltration the *only* route toward conquest, as some Claude text does,
is stronger than the briefing supports: terror has political effects, and future
search information or economy can also contribute indirectly. No victory metric
establishes the relative values. Grok's search/economy emphasis is a legitimate
alternative hypothesis, not automatically an inferior answer.

### Evidence discipline and targeting

Several responses correctly retain uncertainty. `chatgpt_3`: "prioritization, not a
probability estimate". `claude_2`: "less demonstrated to be dangerous, not demonstrated
safe". However, ChatGPT repeatedly treats evidence of interception as affirmative
support for harvesting/abduction/infiltration in those same regions. `chatgpt_2`:
"a deliberate concentration of effort"; it does not supply a mechanism that would
make concentration under this resistance worthwhile. Contact evidence directly
supports suspicion/search more clearly than it supports productive opportunity.

Grok_1 wrongly states both North America and Europe have interception/loss evidence;
the supplied North American evidence is absent. Gemini_3 extends the search-target
policy to its productive choices and describes them as respecting that policy,
without resolving their mission-specific purpose. Claude avoids observed hotspots
more consistently but still cannot establish quiet-region safety or quantify a
diversification benefit. These are different risk hypotheses under weak evidence.

### Campaign allocation and accounting

The responses make useful missing-gate connections, notably harvest -> logistics 2
-> possible standalone base eligibility. They also identify the unused-cash/slot
distinction. This is more inspectable than Laya's action probabilities alone.

Important errors remain:

- `chatgpt_1` says "potential 4 resource reward" for research+harvest+abduction;
  the listed conditional rewards total **5**, before effects from other parents.
- `chatgpt_2` proposes replacing one infiltration with two operations as its strongest
  alternative. Keeping its other three operations would require **five slots**, not four.
- `gemini_1` adds adaptation/intelligence to standalone-base requirements in one
  explanation, despite later reciting the correct gate. Gemini_3 likewise claims the
  full adaptation/logistics/intelligence mix is required for standalone bases.
- `grok_2` describes an alternative of three productive missions plus research as
  "while still searching SEA"; those four operations leave no new search slot.
- `grok_3` says more intelligence enables "higher Infiltration confidence"; no such
  success/confidence mechanic is supplied. It also treats retained funds above the
  carry limit as future flexibility, although those excess funds expire.
- `claude_2` discusses an expected bonus reduction without probabilities, and says
  two infiltrations "doubles the pact/base chances". Neither doubling aggregate
  success probability nor independence is established by the briefing.

### Learning and feedback

All twelve provide some proposed follow-up observables, but their specificity varies.
Claude_1 links logistics 2 to a different next mission and new regional losses to
changed targets. ChatGPT_3 says "adjust the balance" after repeated missing rewards,
which is less operationally specific. Gemini_2 mostly lists observations rather than
clearly specifying which allocations change.

Some proposed learning rules are unsafe even as campaign logic. `claude_3` concludes
"the hedges failed" if next month's budget is near 27. Delayed unresolved operations,
other pending rewards, caps and timing prevent that inference from budget alone.
`claude_2` would treat new interceptions as proof of defended regions; that is evidence
of reach, not a complete estimate of coverage or force strength.

### Mechanics realism and uncertainty

Most responses correctly note that recurring pact/base income is absent and research
cannot discover bases. They acknowledge missing success probabilities and the lack
of a conquest score. This is valuable diagnosis of the experiment itself.

But "discovery gives no strategic payoff" (`claude_1`) or "no payoff here"
(`claude_2`) goes beyond the supplied fact that assault is currently unavailable.
Information could still affect future allocation. Conversely, a promise that any
research finds a region-specific fact would be unsupported; research currently has
only its generic numeric completion reward. There are no actual campaign rollouts
for these LLM portfolios, so outcomes and optimality remain unmeasured.

## Architecture diagnosis

1. **The briefing supports richer candidate plans.** Several models make explicit
   future-state links that the current Laya labels do not express well. A classifier
   ranking a few complete legal portfolios is worth comparing with the present
   sequential mission-type/region choices.
2. **More verbal explanation is not sufficient.** The illegal Gemini orders, invalid
   alternatives, generic risk-to-target mapping and invented confidence link show
   why native validation and typed mechanics must remain authoritative.
3. **The objective/reward specification is incomplete.** Cheap repeatable research
   in quiet regions has a real generic reward; further research has no saturation
   penalty, and political effects have no calibrated scalar value. These data do
   not prove that avoiding infiltration is irrational or that Laya lacks motivation.
4. **The comparison is confounded by representation.** LLMs received a full briefing
   and could choose an entire portfolio at once; Laya received short sequential
   packets. It also has different training/pretraining and compute. Results do not
   isolate model capacity, architecture, missing information or wording effects.

## Next bounded experiment

Keep the live planner unchanged. Build several distinct legal portfolio hypotheses
(capacity development, mixed conquest/economy, pressure/search, information/economy)
from native mechanics, including the current policy and more than one defended
reference plan. Do not let any template promise unsupported gains. Have the same
classifier rank whole portfolios with short, comparable descriptions; contrast this
with its existing sequential choices on the same frozen case.

Then test a small held-out set of controlled campaign situations: infiltration gated
versus available; repeated productive success versus unresolved activity; corroborated
resistance versus no observations. Preserve legality when constructing counterfactual
menus. Shuffle option order, retain every attempt and preregister the qualitative
direction expected—not a compulsory mission sequence. Use the matched compact LLM
arm if information/presentation remains the main question. Only after those tests
should we consider whether task-specific fine-tuning is warranted.

No provider consensus is a gold label, and none of these reports authorizes a live
policy switch, training run, API call, or deployment. This analysis executed no model,
altered no campaign state and changed none of the submitted transcripts.

## Reproduce the mechanical analysis

From `G:\OpenXcom`:

```powershell
.\build\local\laya-venv\Scripts\python.exe scripts/analyze-reference-planner-responses.py
```

`structural-results.json` contains exact parsed portfolios, per-file hashes, legality
results and metadata limits. The existing frozen packet and private baseline files
remain unchanged. Structural checks are automated; the narrative observations above
are an unblinded human-readable review, not automated semantic scoring.
