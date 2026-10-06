# Local Laya reconnaissance integration

The v2 operational test is available with `scripts/run-local.ps1 -ModelExecute`; see [Intent and operation test](#intent-and-operation-test-v2) below. Default `-ModelAudit` remains shadow.

## What is connected

The user-supplied V4 checkpoint is now connected to the Geoscape reconnaissance
audit hook through an opt-in local classifier service. It is the existing
career-evidence model, not a new X-COM-trained model. No fine-tuning or changes
to the supplied checkpoint or career application were performed.

Checkpoint:
C:\Users\Main PC 2\AppData\Local\Temp\uppward-v4

Weights SHA-256:
bcbb891d21cf081a9d7a941b97f8b0f10cf3dac7473b4b9450fab0d07b885175

Model: uppward-laya-evidence-lambda-probe-v4-production-packet.
Encoder metadata: answerdotai/ModernBERT-large, revision
45bb4654a4d5aaff24dd11d4781fa46d39bf8c13.
Runtime: Laya 0.1.6, PyTorch 2.10.0+cpu, Transformers 4.48.0.

The existing WSL GPU runtime failed to start with WSL_E_VM_CRASHED. The Windows
global Transformers/huggingface-hub versions also conflicted. An isolated
build\local\laya-venv overrides the inference packages while using the existing
Windows CPU PyTorch installation. No WSL configuration or global Python
packages were changed. CPU inference took about one second on this machine.

Only small public architecture/tokenizer metadata is fetched from the pinned
encoder revision. The supplied weights are copied into an ignored local staging
directory and loaded strictly. No replacement model weights or cloud inference
are used. The source checkpoint is read-only input.

## Launch from G:\OpenXcom

    .\scripts\run-local.ps1 -ModelAudit

For TFTD:

    .\scripts\run-local.ps1 -Game TFTD -ModelAudit

This enables both the ledger and learned shadow comparison. The launcher starts
the local CPU classifier, waits for readiness, launches the game with the existing
development user/save directory, and stops its owned service when the game closes.
A correctly identified service already running on the selected port is reused
and is not stopped by the launcher.

The model runs on eligible original reconnaissance-script opportunities, not
every frame or tactical turn. Load Testing.sav to continue the existing campaign.
Startup/terror scripts remain baseline-only. With no admitted evidence the
classifier is skipped. Existing difficulty settings and mission execution stay
unchanged. Run with -Audit for deterministic auditing only; run without either
flag to disable new auditing/inference.

The model service uses fixed loopback 127.0.0.1:18867. -ModelPort can select a
different local port; the client cannot send game data to a remote host or follow
HTTP redirects. Its receive timeout is 15 seconds, so a stalled enabled service
can briefly pause a scheduling opportunity. Failure logs MODEL_UNAVAILABLE and
the existing commander continues. Windows native transport is implemented;
other platforms report MODEL_TRANSPORT_UNSUPPORTED_PLATFORM.

The launcher parses health identity; the supplied V4 checkpoint hash is the
current expected identity. Switching to another checkpoint requires an explicit
identity/protocol update, not silently treating it as the evaluated V4 model.

## Fresh setup

    .\scripts\setup-local.ps1
    .\scripts\setup-alien-command-model.ps1
    .\scripts\test-alien-command.ps1 -SkipEngineBuild

The model setup uses an existing working PyTorch installation and creates the
isolated runtime. It does not install a new GPU stack. All generated runtime
files, staged weights, dependency metadata, classifier logs, and replay artifacts
are under the ignored build\local directory.

## Replay your save without advancing it

Deterministic replay:

    .\scripts\replay-alien-command.ps1

To replay with an already-running local model service:

    .\scripts\replay-alien-command.ps1 -ModelPort 18867

A manual foreground service is available in another PowerShell window:

    .\build\local\laya-venv\Scripts\python.exe .\scripts\alien-command-model.py --checkpoint "C:\Users\Main PC 2\AppData\Local\Temp\uppward-v4"

The replay script accepts -Save and -Game TFTD. It copies the source save into a
new ignored replay directory, loads it through the real SavedGame/Mod code,
evaluates the current admitted knowledge, and records an OFFLINE_REPLAY receipt.
It does not run mission scheduling or write the source save. A manifest records
the source SHA-256 and verifies it remains unchanged.

The completed real save replay is:

build\local\replay-20261005-202308-777\xcom1\recon-replay.jsonl

Its manifest is:
build\local\replay-20261005-202308-777\manifest.json

Open docs\alien-command-audit.html and choose that JSONL file. The latest event
shows the deterministic policy, learned classifier, exact classifier state and
question, model scores, checkpoint identity, and the unexecuted replay outcome.
In-game save sidecars now follow the finalized save filename; the previously
observed temporary .sav.bak.alien-command.jsonl issue is fixed for new saves.
Existing old exports are preserved and remain readable.

## Result on the user's actual saved campaign

Testing.sav SHA-256:
b72f817c871919e3a7b6a8a2e6c5bd9f2619625ba883c7d168458b1b197e58d6

The admitted knowledge was interception in Europe, heuristic confidence 40,
one independent reporting UFO, supported by its most recent surviving report.
The actual native replay produced:

- Deterministic policy: STR_ALIEN_RESEARCH in STR_EUROPE.
- Supplied career-trained Laya: abstain / keep the original schedule.
- Model scores: 0.456 for investigating Europe; 0.544 for keeping the schedule.
- No proposal executed; original save hash unchanged.

A real-engine fixture for North America produced the opposite narrow preference:
0.5214 for reconnaissance, 0.4786 for keeping the schedule. These are diagnostic
scores from an out-of-domain checkpoint, not validated probabilities of correctness
or an X-COM base. The learned action/escalation head and temperatures retain their
career-training meaning and do not authorize mission execution.

This establishes working inference and auditability. It does not establish that
the career checkpoint understands Geoscape strategy or improves gameplay.
Shadow comparison lets us test the information boundary, compare against the
simple policy, and assess model behavior before changing campaigns. It is a
development stage, not a requirement that the final commander stay in shadow.

## Input/output contract

Only the value-only admitted snapshot is sent. The service rejects unexpected
fields, invalid locations, unadmitted transmissions, invented evidence,
duplicates, unsupported belief shapes, and unbounded snapshots.

The model receives a compressed textual packet containing region beliefs,
independent reporter counts, admitted evidence IDs/UFO IDs, and observation/report
times. It gets typed, neutrally coded choices for supported reconnaissance regions
plus abstention. Unsupported regions are not introduced as model choices.
This is an explicit compressed representation; exact packet text/questions and
hashes are retained beside the full source snapshot.

The stock Laya formatter can truncate option definitions, instructions, or state.
The adapter checks the complete token budget and rejects INPUT_LIMIT instead.
Model output must have the expected option set, finite normalized scores, and a
typed choice. The native engine separately checks checkpoint identity format,
schema, scores, static menu membership, region evidence, and exact belief support.

Learned proposals are stored separately from the deterministic proposal and the
legacy engine action. Neither model scores nor its action-head output authorize
execution. The static catalog still does not claim complete dynamic mission
legality.

## Verification on 2026-10-05

- Updated x64 engine built successfully, zero errors; upstream warnings remain.
  A compiler heap failure was resolved by using a 64-bit compiler host and two
  workers; setup-local.ps1 now retains these bounded build settings.
- Baseline native suite: 56 checks passed per original game.
- Real classifier through the actual Geoscape hook: 58 checks passed per original
  game, including unchanged model state/answers when hidden base/funds change.
- Nine Python packet-boundary tests passed.
- Actual UI quick-save path verifies final save and audit sidecar promotion.
- Actual user save replay completed through the native WinHTTP client and real
  checkpoint; source save unchanged.
- No new X-COM training, balance playtest, active learned mission selection, or
  tactical model behavior is claimed.

To repeat the live-model native checks with a running service:

    .\scripts\test-alien-command.ps1 -SkipEngineBuild -ModelPort 18867
    .\build\local\laya-venv\Scripts\python.exe .\tests\test_alien_command_model.py

The next substantive step is a separate game-domain training/evaluation set,
testing evidence sensitivity, abstention, candidate ordering/wording, and campaign
outcomes. Any fine-tuned game checkpoint should be a separate artifact, preserving
the career model. Active execution also needs dynamic mission legality validation.

Laya's underlying typed inference API is documented in its primary source:
https://github.com/NandhaKishorM/laya


## Intent and operation test (v2)

The model now chooses between gathering interception reports (research/probe), searching for a base (retaliation), and keeping the original schedule. Research/probe flights cannot discover bases under normal retaliation rules. Retaliation uses the existing search waves and may launch a base assault once discovery succeeds. No scout strength, wave timings, difficulty modifiers, radar rules, or discovery probabilities were changed. With aggressiveRetaliation enabled, other UFOs can discover bases too; the prompt currently describes the normal configuration used for this test.

From `G:\OpenXcom`, run:

```powershell
.\scripts\run-local.ps1 -ModelExecute
```

Load a save before February 1 (for example `Testign 3`, January 20), then save under a new test name before advancing. The February recon decision can replace that month's normal recon-script operation; recurring terror remains the original engine choice. This is an operational experiment and can lead to a base attack through stock retaliation behavior. Loading an already-February save does not rerun February's decision.

`-ModelAudit` keeps both operations in shadow. The launcher explicitly turns execution off unless `-ModelExecute` is supplied. Restart any old model service before using v2; the launcher rejects a v1 service rather than reusing its old prompt.

Only a model proposal validated against admitted evidence and the static operation menu can execute. Abstention, unavailable/invalid responses, input limits, and an already-active mission of the same type in the effective region fall back to the original commander. The original region/type draws still occur before override; race selection and engine wave generation use the chosen operation. Execution therefore changes campaign behavior and later RNG; shadow mode preserves the original behavior.

Receipts include modelIntent, expectedGain, operationalStatus, actual engine mission/region/id, and model.executedProposal. A successful override has source MODEL_COMMANDER and mode MODEL_EXECUTION. Historical receipts remain unchanged. A modelIntent is the harness's typed interpretation of its selected operation, not an explanation extracted from the model.

This menu is still a small information-gathering test: it has no resource economy, loss-aware planning, verified-location DTO, or full competition among campaign objectives. Base discovery remains the stock engine's flag, separate from the report ledger. A new base_discovery audit event records the first flag transition and its observing UFO. Already-discovered bases can cause retaliation to send an assault directly; the model does not yet receive those discovery flags. It is not yet an inference-and-transmission model of base discovery.

Engine execution and fallbacks can be checked with:

```powershell
.\scripts\test-alien-command-operations.ps1
```

This uses a clearly scripted local HTTP fixture to force research, base search, abstention, and invalid evidence, then tests the actual scheduler and UFO wave spawning in both games. It does not measure learned strategic performance. Separate real-checkpoint tests and save-copy replays use the Laya service.

Validation for v2: 56 baseline native checks per game; 58 with the actual checkpoint service per game; scripted operation checks research 66, base search 67, abstention 60, invalid evidence 60 per game; 10 Python packet checks. The real native replay of Testign 3 preserved the original save SHA and chose North Africa report gathering. Full engine build succeeded. Viewer JavaScript syntax is checked; visual layout has not been reverified.


For budget-aware multi-operation execution, use `-Portfolio` and see [ALIEN_COMMAND_PORTFOLIO.md](ALIEN_COMMAND_PORTFOLIO.md). `-ModelExecute` retains the earlier single-recon experiment.
