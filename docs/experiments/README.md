# Alien commander experiment artifacts

This archive preserves the progression from manual reference-planner probes through incentive, ordering, adaptation, compact-briefing and publisher-base checkpoint comparisons. Each experiment has its own scope and limitations; earlier mechanics descriptions are historical, not necessarily the current runtime.

Start with [base checkpoint comparison](base-laya-comparison-v1/REPORT.md), [compact briefing](compact-command-v1/REPORT.md), [matched adaptation](adaptive-responses-v1/REPORT.md), and the [adaptation rubric](../ALIEN_COMMAND_ADAPTATION_RUBRIC.md). Reports, protocols, tables, harnesses and tests are committed. The twelve manual frontier-model transcripts are in `llm_responses/`; the reference packet's `private_comparison` means withheld from those test chats, not personal/private account data.

Interpret the results narrowly. Evidence-responsive avoidance of repeatedly costly regions while pursuing resource acquisition is meaningful progress where demonstrated. Presentation-dependent targeting, including selecting a loss-bearing region, limits reliability. Neither imperfect consistency nor absence of a complete conquest strategy erases narrower useful behavior. The publisher-base comparison matched 31/32 career-model choices, weakening the career-specific explanation without proving an internal mechanism or optimal strategy.

## Dependency state

The experiments were run against locally implemented v9 economy/planner support on parent `5342681d0b104691b65fd8f636be229b3643c195`. This artifact commit intentionally leaves the active engine/planner changes out of the Git tree. Their exact tracked dependency delta is archived as [runtime-v9-dependencies.patch](runtime-v9-dependencies.patch), including Python envelope/planner support and corresponding tests. This patch is provenance, not a claim that the artifact commit activates the v9 engine.

To reconstruct that dependency state, use a separate checkout of the artifact commit, inspect the zero-context patch, and run `git apply --unidiff-zero --check docs/experiments/runtime-v9-dependencies.patch` followed by `git apply --unidiff-zero docs/experiments/runtime-v9-dependencies.patch` there. Build/setup requirements remain in the existing local setup documentation. Do not apply it over an already modified checkout. Original local engine edits remain available separately for a future implementation commit.

Tests and harnesses may require this dependency patch, the documented local Python environment, checkpoints and native-exported fixtures. Some tests skip when local fixtures are absent. Hashes in historical manifests refer to the actual files at experiment time, including local absolute paths; they are retained as provenance rather than rewritten to pretend portability.

## Retained evidence

The three most recent comparisons include full component receipts, not just aggregate tables:

- `compact-command-v1/receipts.json` and `frozen.json` preserve the career comparator's exact packets and synthetic inputs.
- `adaptive-responses-v1/receipts.json` and `frozen-inputs.json` preserve the earlier career comparator, rendered packets and synthetic inputs.
- `base-laya-comparison-v1/receipts.json` and `download-receipt.json` preserve paired base outputs and pinned publisher download identity.
- `receipt-archive.json` records source paths and SHA256 hashes of those copied artifacts.

Earlier experiments retain their committed tables/protocols/reports and hashes; their larger raw local execution directories are not claimed to be fully archived here. Native executables, model weights, original player saves, original-game assets and the local Python environment remain excluded under `build/`. Archived receipts suffice to inspect/recompute the recent paired comparisons without downloading models or accessing a player save; executing new inferences still requires the checkpoint/runtime. No live policy change or deployment is implied by publication.
