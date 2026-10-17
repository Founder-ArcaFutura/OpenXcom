# Campaign objectives summary experiment

2026-10-16. The live v8 planner is unchanged. `campaign_plans.plan` has an optional
`objectives=False` argument, enabled only by `scripts/test-campaign-objectives.py`.
Each PLAN packet receives native prerequisite gaps for infiltration and bases,
whether a target is present in the currently affordable candidate menu, and a short
statement that extra intelligence is not a missing infiltration prerequisite once
the intelligence threshold is reached. No choices are forced, prices altered or
rewards invented; no tactical/player-only data enters the experiment.

The same actual local checkpoint evaluates baseline and treatment per frozen input.
May source: `And into may.sav`. April source: `I forgot to save.sav`. March source:
`Post-March_again.sav`. Only the last recorded portfolio input in each save is read;
later save-state outcomes are not supplied. Thus the later April save does not leak
its April 5 research completion into the April 1 decision. Each source hash is checked
unchanged. These are independent redecisions, not an alternate campaign simulation.

May baseline reproduced abduction Australasia and research South East Asia, Arctic,
Antarctica, spending 9 and retaining 16. The objectives treatment selected research
South East Asia, Arctic, Antarctica and Pacific, spending 8 and retaining 17.
The treatment's objective summary explicitly had no missing infiltration prerequisites
and available targets; the model still preferred four research missions. Packets
were not truncated: maximum token counts 378 baseline, 464 treatment. Timings were
16.34 seconds and 17.95 seconds respectively.

The first attempted April input (`Post-April.sav`) was the superseded three-slot
v7 receipt. Both variants correctly rejected its capacity/month mismatch. It is
excluded from behavioural comparisons; its rejected outputs are retained openly.
The current four-slot April receipt was then tested via `I forgot to save.sav`.

| Decision | Baseline | Objectives summary |
|---|---|---|
| March 1 | Three abductions: Australasia, Central Asia, South East Asia; retained 9 | Three research: Arctic, South East Asia, Antarctica; retained 12 |
| April 1 | Harvest South East Asia; searches Europe/North Africa; research Arctic; retained 15 | Research Arctic, South East Asia, Antarctica, then explicit defer; retained 18 |
| May 1 | Abduction Australasia; research South East Asia, Arctic, Antarctica; retained 16 | Four research: South East Asia, Arctic, Antarctica, Pacific; retained 17 |

The summary consistently shifts these three frozen inputs toward research. This
is not evidence of sensible milestone reasoning: May already meets infiltration
prerequisites while April/March do not, yet the treatment repeatedly chooses
research-heavy portfolios. The explicit research sentence may itself cue the action;
this experiment does not isolate that effect from the new structured gap fields.
Next diagnostic candidate is a label-neutral gap-only summary and controlled
counterfactual prerequisite states, with option-order sensitivity checked before
attributing behavior to campaign reasoning. Neither forced infiltration nor a
new live prompt is justified by these runs. Keep v8 active.

69 Python checks pass, including exact prerequisite gaps, unlocked paths, and legal
deferral despite objective advice. Outputs and per-source manifests:
`build/local/objectives-april-may-v1`. No native mission execution or live policy
change is performed by this experiment. The model is career-trained and not validated
for XCOM; these observations show prompt sensitivity, not calibrated strategic beliefs.
