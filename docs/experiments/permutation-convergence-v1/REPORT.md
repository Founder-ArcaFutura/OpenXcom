# Six-family first-decision convergence and the separate question of adaptive strategy

Completed the additional convergence check on the two previously ambiguous first PLAN decisions, February and April. Seventy-two ordered component evaluations: 48 new local CPU inferences and 24 exact prior reuses. All component scores and pooled results were recalculated; original saves and the live model/planner scripts are unchanged. Maximum packet size was 387/512 tokens. No API call, reward change, native execution, online training or live policy change occurred. Ninety-seven Python tests passed.

## What converged

| State | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| 1999-02 | HARVEST | HARVEST | HARVEST | HARVEST | HARVEST | HARVEST |
| 1999-04 | HARVEST | ABDUCTION | ABDUCTION | ABDUCTION | ABDUCTION | ABDUCTION |

| State | Pool | Components | Choice | Mean-score gap |
|---|---|---:|---|---:|
| 1999-02 | AB | 12 | HARVEST | 0.002208 |
| 1999-02 | CD | 12 | HARVEST | 0.021700 |
| 1999-02 | EF | 12 | HARVEST | 0.037783 |
| 1999-02 | ABCD | 24 | HARVEST | 0.011954 |
| 1999-02 | CDEF | 24 | HARVEST | 0.029742 |
| 1999-02 | ABCDEF | 36 | HARVEST | 0.020564 |
| 1999-04 | AB | 12 | HARVEST | 0.001808 |
| 1999-04 | CD | 12 | ABDUCTION | 0.032442 |
| 1999-04 | EF | 12 | ABDUCTION | 0.037808 |
| 1999-04 | ABCD | 24 | ABDUCTION | 0.015317 |
| 1999-04 | CDEF | 24 | ABDUCTION | 0.035125 |
| 1999-04 | ABCDEF | 36 | ABDUCTION | 0.022814 |

February consistently selects harvest across all six disjoint families and every tested pool. April illustrates why the extra families matter: the original AB pool narrowly selects harvest, while the separate CD and EF pools select abduction. Adding those families changes the growing pool to abduction at ABCD and retains it at ABCDEF. This is convergence evidence for two fixed first-decision rankings, not universal order invariance or convergence of complete portfolios. The mean-score gaps are not calibrated confidence.

A/B reproduce the earlier families. C-F use preregistered deterministic seeds, with cyclic orbits rejected until all six sets are pairwise disjoint. Every action, including SAVE, occupies each position once per family. The independent pair pools and overlapping growing pools are not independent statistical samples, and no family was selected to produce a desired mission.

## Does that make the April strategy better?

No quality conclusion follows from this ranking alone. In the April state, logistics is one and adaptation is two. Harvesting can unlock base construction; further abduction adds resources and adaptation, but no new adaptation-gated option is identified by the current simple gate table. Different native mission risks, target opportunities and political effects can still make abduction defensible. We have no reliable success odds or actual alternate outcomes here. A stable abduction score does not demonstrate that the commander understood those tradeoffs, and a harvest choice would not automatically prove long-term planning either.

The larger first-choice pool was not rolled forward into a new full portfolio. Later mission choices, regions, CPU latency and actual campaign results cannot be inferred from these 72 component rankings. The earlier full-portfolio experiment still shows residual family sensitivity.

## The intended opponent

The objective is a coherent, evidence-responsive adversary under fair constraints, rather than perfect play or a fixed mission mix. Useful behavior would include recognizing a missing capability, trying to acquire it, exploiting it after delivery, and changing a repeatedly frustrated plan without treating every scout loss as a mission defeat. The aliens should translate a foothold into pressure and react to player disruption while retaining uncertainty about XCOM. Random variety or more spending is not itself adaptation.

For example, June harvesting can be sensible because logistics one blocks direct bases. The meaningful follow-up is whether a delivered harvest leads to an appropriate base investment, subsequent supply/influence growth, and pressure on XCOM or funding nations. If the player repeatedly prevents that investment from paying off, the commander should change route, investigate or switch objectives for a campaign reason. The current frozen-state tests do not demonstrate that loop. A search-to-assault strategy is also mechanically incomplete while separate funded assaults are unavailable.

## Assessment framework and next experiment

The separate [adaptation rubric](../../ALIEN_COMMAND_ADAPTATION_RUBRIC.md) specifies independent dimensions, observed limitations and matched tests. Do not replace them with one unvalidated cleverness score. Distinguish model behavior from engine-enforced legality and evidence filtering.

The next informative tests are matched changes to strategically material facts: move coherent interference evidence; deliver the missing logistics prerequisite and rebuild the native menu; distinguish a verified objective defeat from a lost preparation scout with an objective still pending. Register qualitative acceptable responses rather than one mandatory mission. These tests are specified, not executed in this run.

Before judging those responses, audit the actual compact input. The live lessons still contain an unnamed progress vector. A model cannot be expected to exploit facts that the packet does not identify clearly. Prior named-context probes did not uniformly improve choices, so clear state and capability contracts also need testing rather than automatic promotion. The career-trained checkpoint has not been trained on campaign consequences; fixed weights can support adaptive behavior, but reward-description sensitivity does not establish that capability.

## Saved results

- [Convergence table](convergence.csv): every individual family and pool, with choice, full mean scores, score margin and component count.
- [Component score table](component-scores.csv): all 72 ordered evaluations, probabilities and cache provenance.
- [Detailed results](results.json) and [protocol](PROTOCOL.md).
- Raw states, exact questions, per-family component receipts and source/checkpoint manifests: build/local/permutation-convergence-v1/<month>/.
- Runner: scripts/test-permutation-convergence.py; analyzer: scripts/analyze-permutation-convergence.py.
