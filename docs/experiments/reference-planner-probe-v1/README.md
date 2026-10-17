# Manual reference-planner probe

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
