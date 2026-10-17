"""Build a blind, manual, no-API reference-planner packet from recorded May input."""
import argparse, hashlib, importlib.util, json, random, statistics
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]

BRIEF='''You are a reference planner in a fictional OpenXcom alien campaign experiment.
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
'''

README='''# Manual reference-planner probe

No API calls, provider integrations, downloads or training are required. You run
the prompts yourself in the interfaces you already use. Start with the full May
prompt on ChatGPT, Grok and Gemini, one fresh conversation per run.

## Files to send

- `01_FULL_MAY_PROMPT.md`: paste the entire file as the first message. Self-contained
  mechanics briefing, exact admitted native input, filtered eligible operations and
  answer instructions. Do not send the whole folder or this README to the model.
- `02_MATCHED_FIRST_CHOICE_PROMPT.md`: optional second arm, in a DIFFERENT fresh chat.
  It reproduces the exact first PLAN state, choices and instructions Laya received,
  with no full briefing. It compares the first mission-type decision only, not targets
  or a complete portfolio. The evidence briefing is intentionally absent in this arm.

Use the same file unchanged across providers. Ask for the first response, keep it
even if poor, and do not hint at research, infiltration, polar oddities or Laya's
answer. Avoid follow-up coaching before saving the initial response. If you want
replicates, use new chats and retain EVERY attempt. A few manual runs are exploratory,
not a statistically established ranking. No need to buy a subscription for this.

Record the visible model name, mode, date, whether memory/custom instructions or
tools were active, any quota/model fallback, and whether the prompt was complete.
Where possible use chats without prior project context and without browsing or
personalization. If a setting cannot be disabled, record it; don't claim controlled
equivalence. Do not ask a model to identify its own model version as evidence.

## Return the evidence

Copy each complete transcript into a separate text/Markdown file, using
`03_TRANSCRIPT_TEMPLATE.md` for metadata. Include the exact prompt/file name and
every response, refusal, truncation and follow-up in order. Paste/upload those files
back into this OpenXcom chat. Share links alone may be inaccessible. Do not include
account details, credentials or unrelated chat history. For a basic cross-section,
three full-brief runs plus up to three compact first-choice runs are enough to begin.

## Keep the comparison blind

Do NOT send or read `private_comparison/` into the test chats. It contains Laya's
recorded answer and seeded random baselines, reserved for AFTER initial responses
are collected. No specific mission mix is the answer key. Don't tell the providers
that any previous result was considered good or bad.

## What this can establish

The full prompt lets an LLM see a fuller explanation and all admitted native fields
at once, and select a whole portfolio. Laya actually saw short sequential packets
limited to 512 tokens, with a shared checkpoint trained for another domain. So full
brief superiority could reflect presentation/context/architecture as well as model
capability. The matched arm helps isolate a narrower first-choice comparison, but
still does not equalize pretraining, compute, tuning, familiarity or hidden provider
settings. Country-level player locations, technology and actual safety are withheld.

Inspect choices and evidence use; polished prose is not demonstrated competence or
faithful internal reasoning. We have no measured payoff forecast, campaign rollout,
unique optimal portfolio or verified long-term conquest outcome. Native recurring
income from controlled countries/bases is not implemented. A model identifying weak
incentives in these rules may be providing a useful diagnosis rather than failing.

## Evaluation

Use `04_EVALUATION_RUBRIC.md` after collection, preferably with author names hidden.
`scripts/check-reference-portfolio.py` checks the JSON operations against the frozen
eligible menu and budget; it does not execute missions or score strategic merit.
The random samples are genuine negative controls for legality/choice behavior, not
evidence of strategic quality. The current classifier is a reference baseline.

Original saves, live policy and weights are unchanged. Provenance, input hash,
source hashes and generation checks are in `provenance.json`.
'''

RUBRIC='''# Review rubric — after collecting responses

Freeze the criteria before comparing authors. Hide provider/model names for the
first reading where practical. Keep structural legality separate from judgement.

## Structural checks (pass/fail, no strategy score)
- Only frozen eligible mission-region pairs; no duplicates; <=4 new missions.
- Correct native costs, <=25 spent, correct remaining resources.
- No unavailable assault, premature base construction, free cancellations or invented
  rewards. Existing operations are not charged again as new orders.
- Correct carry and conditional bonus treatment; do not promise future mission gains.

## Independent dimensions (0=absent/contradicted, 1=partial, 2=clear)
1. Objective coherence: each mission can accomplish its claimed purpose.
2. Evidence discipline: distinguishes reports, assignment losses, absent observations
   and UNKNOWN, without reconstructing hidden player facts.
3. Campaign allocation: accounts for ongoing commitments, opportunity costs and
   progression, rather than assuming more of any mission is always better.
4. Learning: names observable outcomes and specific corresponding allocation changes.
5. Mechanics realism: recognizes native timing/uncertainty and missing economy pieces.

Give a short supporting quote for each rating and mark reviewer uncertainty. Report
dimensions separately; do not collapse them into an unvalidated 'intelligence score'.
Do not reward infiltration merely for being chosen, punish research merely for being
polar, require spending every resource, or treat good prose as a good campaign outcome.
A defended low-risk research investment can be legitimate under these incentives.
Tag failures by likely source: unavailable evidence, misunderstood mechanics, weak
objective-to-action link, unsupported certainty, or presentation/option-order effect.

For the compact arm, judge only first legal mission-type choice and use of its actual
state. It was NOT supplied the full briefing; missing briefing facts are not hallucination
unless it asserts incorrect facts. No region/portfolio answer is required in that arm.

## Interpretation
- Coherent full-brief plans but poor compact choices suggest representation/context
  is a candidate bottleneck; they do not isolate it causally.
- Coherent compact and full-brief choices suggest task-specific Laya learning or its
  formulation deserves testing, not that LLM prose proves understanding.
- Shared mechanical ambiguity or plausible but unhelpful plans suggests reward/action
  design and outcome evaluation need work.
- Do not create training labels from provider consensus alone. Retain disagreements
  and several defensible plans; evaluate held-out scenarios before any fine-tuning.
'''

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--save',type=Path,default=ROOT/'build/local/user/xcom1/And into may.sav')
 p.add_argument('--out',type=Path,default=ROOT/'docs/experiments/reference-planner-probe-v1')
 a=p.parse_args();raw=a.save.read_bytes();s=list(yaml.safe_load_all(raw.decode('utf-8')))[-1]
 receipt=[json.loads(x) for x in s['alienCommand']['audit'] if json.loads(x).get('kind')=='portfolio'][-1]
 assert receipt['gameTime']=='1999-05-01 00:00:00','Use the frozen May decision'
 data=receipt['input'];response=json.loads(receipt['response'])
 spec=importlib.util.spec_from_file_location('model',ROOT/'scripts/alien-command-model.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 b,menu,beliefs,si=m.portfolio_input(data)
 reports={x['region']:{} for x in beliefs}
 regions,basis=m.search_region_pool(sorted({x['region'] for x in menu if x['mission']=='STR_ALIEN_RETALIATION'}),reports,si)
 if (reports or si['lossAssignments']) and basis=='NO_MATCHING_EVIDENCE_EXPLORATION':regions=[]
 eligible=[x for x in menu if x['mission']!='STR_ALIEN_RETALIATION' or x['region'] in regions]
 packet={'decisionTime':receipt['gameTime'],'eligibleOperations':eligible,'nativeInput':data}
 out=a.out;out.mkdir(parents=True,exist_ok=True);private=out/'private_comparison';private.mkdir(exist_ok=True)
 def write(name,value): (out/name).write_text(value,encoding='utf-8')
 write('README.md',README);write('01_FULL_MAY_PROMPT.md',BRIEF+'\n```json\n'+json.dumps(packet,indent=2)+'\n```\n')
 first=next(d for d in response['decisions'] if d['stage']=='PLAN')
 matched={'state':first['state'],'criteria':first['question']['criteria'],'instructions':first['question']['instructions']}
 write('02_MATCHED_FIRST_CHOICE_PROMPT.md','''This is a fictional campaign choice probe. Use only the state, options and instructions below. Do not browse or use tools. Choose ONE option label, including SAVE if warranted. Do not select regions or construct a full portfolio. Give the label and a justification of at most 150 words, distinguishing evidence from assumptions. If context is missing, say which facts are missing, but still make the requested choice. Do not import other XCOM rules.\n\nThe following state string, option labels/text and decision instruction are exactly those supplied to the classifier at its first May choice. This wrapper requests an inspectable answer.\n\n```json\n'''+json.dumps(matched,indent=2)+'\n```\n')
 write('03_TRANSCRIPT_TEMPLATE.md','''# Run metadata\n- Run ID:\n- Provider/interface:\n- Visible model name/version:\n- Mode/reasoning setting (as shown):\n- Date and timezone:\n- Prompt file and packet version:\n- Fresh chat? Prior project context?\n- Memory/custom instructions/personalization active or unknown:\n- Browsing/tools active or unknown:\n- Quota fallback, refusal, cutoff or incomplete paste:\n- First attempt or replicate number (retain all attempts):\n\n# Exact prompt\nPaste it here, or identify the unchanged prompt file plus its SHA-256. Record all edits.\n\n# Complete response\nPaste verbatim, including JSON and explanation.\n\n# Follow-ups\nPreserve every message in order. Leave blank if none.\n''')
 write('04_EVALUATION_RUBRIC.md',RUBRIC)
 write('frozen_packet.json',json.dumps(packet,indent=2)+'\n')
 samples=[]
 for seed in range(30):
  rng=random.Random(seed)
  result=m.plan_concrete_portfolio(data,lambda state,criteria,ins:(rng.choice(list(criteria)),{}))
  assert len(result['operations'])<=b['maxOperations']
  assert all(x in eligible for x in result['operations'])
  assert len({(x['mission'],x['region']) for x in result['operations']})==len(result['operations'])
  samples.append({'seed':seed,'operations':result['operations'],'remaining':result['remainingProposed']})
 write('private_comparison/baselines.json',json.dumps({'recordedLaya':response,'randomNegativeControls':samples,'sampling':'Python Random seeds 0-29; uniform available labels at each PLAN (including SAVE), then uniform region labels. Not uniform over whole portfolios. No inference calls.','randomMedianSpent':statistics.median(b['remaining']-x['remaining'] for x in samples)},indent=2))
 hashes={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='provenance.json'}
 sourcefiles=['scripts/campaign_plans.py','scripts/alien-command-model.py','src/Savegame/AlienCommand.cpp','src/Savegame/AlienCommand.h','src/Geoscape/AlienCommandAudit.cpp','src/Savegame/AlienMission.cpp']
 provenance={'packetVersion':'manual-reference-planner-v1','sourceSave':str(a.save.resolve()),'sourceSaveSha256':hashlib.sha256(raw).hexdigest(),'recordedDecisionId':receipt['id'],'decisionTime':receipt['gameTime'],'nativeInputSha256':m.digest(data),'sourceFilesSha256':{x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in sourcefiles},'packetFilesSha256':hashes,'checks':{'eligibleMenuSubset':all(x in menu for x in eligible),'randomSamplesLegal':len(samples),'matchedStateAndQuestionExact':True,'apiCalls':0,'modelInferenceCalls':0,'livePolicyChanged':False,'missionsExecuted':False}}
 assert raw==a.save.read_bytes(),'Original save changed'
 write('provenance.json',json.dumps(provenance,indent=2)+'\n')
 print(json.dumps({'out':str(out.resolve()),'eligiblePairs':len(eligible),'randomControls':len(samples),'apiCalls':0,'sourceUnchanged':True}))

if __name__=='__main__':main()
