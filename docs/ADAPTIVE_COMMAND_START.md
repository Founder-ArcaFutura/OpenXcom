# Adaptive alien command: first Geoscape slice

The supplied design is preserved verbatim in ADAPTIVE_COMMAND_DESIGN.txt.

## Current behavior

Alien-command auditing is opt-in and defaults off. With it enabled, the engine
records existing mission-command attempts and evaluates a small reconnaissance
policy in shadow mode. The existing commander still makes every actual mission
choice. Existing difficulty modifiers and Battlescape AI remain unchanged.

The deterministic policy establishes the observation and decision contract.
An optional local Laya classifier is now connected for learned shadow comparison;
see ALIEN_COMMAND_MODEL.md for checkpoint identity, launch instructions, and the
actual saved-campaign replay. No learned proposal executes missions.

## Run and inspect

From PowerShell in G:\OpenXcom:

    .\scripts\setup-local.ps1
    .\scripts\run-local.ps1 -Audit

For Terror from the Deep:

    .\scripts\run-local.ps1 -Game TFTD -Audit

The source-built runtime, copied original resources, settings, and saves are
under build\local. The launcher selects these development directories. Running
without -Audit explicitly disables new auditing; existing saved knowledge is
preserved. The installed game and Steam originals are not modified.

Start a campaign, allow a mission scheduling opportunity and an interception,
then save. Each save with audit state exports:

    build\local\user\xcom1\<save>.sav.alien-command.jsonl
    build\local\user\xcom2\<save>.sav.alien-command.jsonl

Open docs\alien-command-audit.html in your browser and choose that sidecar. The
viewer also accepts build\local\user\openxcom.log. Files are read locally with no
network access. It shows reports, beliefs, supporting evidence, proposals,
validation, actual mission creation, and the exact stored receipt.

For a fixture immediately, run the native tests below and open:

    build\local\test-xcom1\xcom1\audit-fixture.sav.alien-command.jsonl
    build\local\test-xcom2\xcom2\audit-fixture.sav.alien-command.jsonl

These exports are explicitly test campaigns. Their interception evidence is
injected to test persistence and hidden-state independence; the scheduler
records are produced by the real engine. They are not live playtest findings.

## Information boundary

Only an active, interceptor-initiated dogfight captures a UFO's own encounter
location, time, unique UFO identity, and own mission identity. Waiting/minimized
encounters that never activate do not produce reports. Hunter-killer encounters
are outside this first slice.

At encounter end, only a surviving UFO can transmit the captured observation.
Destroyed or crashed UFOs produce audit-only rejection records. Duplicate
reports do not add evidence. Repeated reports from one UFO do not count as
independent sources.

Stored beliefs say that interception was observed in a region. They do not
assert an X-COM base exists there. Confidence is an explicitly uncalibrated
heuristic, capped at 80 for newly derived beliefs. The most recent report from
up to eight independent UFOs supports each belief. Observations, beliefs,
confidence, event counters, and exact decision receipts persist in the save.

The policy receives value-only records: candidates, admitted observations, and
stored beliefs. It has no game/save/base/craft pointers. Its candidate catalog
comes from static region/mission rules, without reading player state. At most
64 candidates are scored. The current domain is UFO research/TFTD probe region
selection on the original reconnaissance script.

The highest supported confidence wins; lexical ordering resolves ties without
consuming game RNG. Missing evidence, unsupported scripts, malformed proposals,
and empty/oversized menus abstain or reject. The proposal must reference its
admitted evidence and be a typed member of the static candidate menu.

This catalog is not a claim of full current mission legality. Script eligibility,
region aliases, active mission conflicts, random scheduling, and execution
constraints remain with the original engine. Modified reconnaissance scripts
with targeting or region/mission overrides stay baseline-only.

## Audit and save contract

The authoritative YAML save field is alienCommand, schema version 1. Loading
restores stored beliefs exactly, rather than inferring them from current hidden
state. Old saves without the field start with empty knowledge; unsupported or
invalid knowledge schemas fail explicitly rather than silently discard state.

Decision receipts separate policy input/proposal from the legacy engine action.
They include the script, time, difficulty, actual mission ID/type/region/race,
validation, and engine RNG before/after. Only command attempts reaching
processCommand are audited; upstream eligibility skips are not logged yet.

Interception receipts separate admitted evidence from debug encounter outcomes.
The latter is not passed to the policy. Future mission results are marked PENDING;
mission lifecycle result tracking and a replay runner are not implemented yet.
The viewer traces the recorded evidence, but does not simulate the campaign.

Sidecars are exported after successful saves; each is a snapshot of that save's
ledger. A sidecar export failure warns without losing the authoritative knowledge
already stored in the save. The runtime log also receives events immediately.
The full audit ledger is retained; long-campaign retention/compaction remains
future work.

## Validation on this machine (2026-10-05)

Run:

    .\scripts\test-alien-command.ps1

The script builds the real engine, links its object files into the native test
executable, and loads both original games' actual rules and resources. For an
engine already rebuilt after the latest changes, -SkipEngineBuild skips that step.
SDL dummy drivers are confined to testing and restored afterward.

- Modified x64 engine: build successful, zero errors; upstream compiler warnings remain.
- UFO Defense: initial 48 checks passed; updated integration has 56 baseline / 58 live-model checks.
- TFTD: initial 48 checks passed; updated integration has 56 baseline / 58 live-model checks.
- Actual scheduler: same missions, strategy, and RNG with auditing on versus off
  for paired seeded campaigns.
- Actual dogfight hook: survivor admitted once; crashed/destroyed/waiting
  encounters rejected or unobserved; unique identity retained independently of
  the player-facing UFO number.
- Permitted evidence drives region scoring; repeated sources, fabricated evidence,
  invalid confidence, out-of-menu proposals, and absent evidence are checked.
- Hidden base coordinates and funds do not change identical policy input/proposals.
- Actual SavedGame save/load preserves the entire knowledge state and sidecar;
  old-save compatibility and unsupported schema rejection pass.
- Viewer JavaScript syntax and JSONL/log parsing passed against both native test
  exports, including evidence references and malformed/future-schema records.
  Visual browser verification was blocked because the browser tool disallows
  local file URLs; the browser layout has not been visually verified.
- git diff --check passed. Changes remain local and uncommitted.

These are engine integration checks, not interactive playtesting, strategic
balance findings, or evidence that a trained model improves alien behavior.

## Local setup

Source is OpenXcom Extended 8.7.1 on true_difficulty. This machine has MSVC v142,
Windows SDK 10.0.19041.0, and the repository's SDL x64 dependencies.

Verified original resources are read from:
- C:\Program Files (x86)\Steam\steamapps\common\XCom UFO Defense\XCOM
- C:\Program Files (x86)\Steam\steamapps\common\X-COM Terror from the Deep\TFD

setup-local.ps1 accepts -SteamApps and -MSBuildPath overrides. -SkipBuild stages
resources only. It copies resource directories, not original saves/executables.
The upstream Visual Studio post-build step also copies ignored DLLs to bin\x64.

Before this implementation, both unchanged-engine masters passed hidden startup
checks. Staged resource inventories matched the originals: UFO 720 files,
10,618,846 bytes; TFTD 1,121 files, 61,917,520 bytes. The supplied design matched
the attachment byte for byte.

## Next decision space

Use real campaign audit traces to review the evidence contract. Then add mission
outcome observations and a dynamically legal reconnaissance menu, followed by a
game-domain evaluation and fine-tuning for the connected classifier. Keep shadow
comparison until its decisions and information boundaries can be assessed. Numerical
difficulty balancing remains a later playtest decision.
