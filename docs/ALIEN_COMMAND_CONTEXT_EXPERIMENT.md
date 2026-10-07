# March commander context experiment

This is a read-only comparison of the real local checkpoint on the existing March 1 campaign input. It changes neither the live policy nor campaign commitments. The current portfolio mode does allow model-selected operations to be committed: the native engine validates the complete portfolio, pays costs, picks races and runs stock mission waves. The model does not control individual UFO movement or tactical units.

## Tested variations

| Variant | Strategy | New proposed operations | Spending / remaining |
| --- | --- | --- | --- |
| Existing policy | Resource acquisition | None | 0 / 13 |
| Explicit deferral consequences | Resource acquisition | None | 0 / 13 |
| Mission context and rolling review | Political pressure | None | 0 / 13 |
| Context plus explicit deferral | Political pressure | Terror Europe; search Australasia; search Arctic | 8 / 5 |

The baseline reproduces the recorded March choices and probabilities exactly. Explicit deferral states the carry amount and forfeiture, ends new commitments, and explains that money alone cannot replace productive prerequisites for base/infiltration unlocks. Its question compares deployment against deferral without requiring spending or prescribing an economic operation.

The added context distinguishes two preparation-craft losses from four search-craft losses, no confirmed objective-carrier loss, and two funded terror missions with objective waves still pending. It includes January and February loss/activity counts, and explicitly preserves partial coverage and uncertainty. It does not call a pending objective successful or read the later Mexico City site into the March decision.

Roles are reconstructed from complete own deployment sequences since recorded assignment and the stock mission-wave rules. Active mission wave counters must agree with observed deployment counts; missing coverage leaves the role UNKNOWN. This is an offline stock-rules experiment. Live integration requires explicit native craft type, wave index and objective-role telemetry rather than depending on reconstruction. Player research, funds, bases, captured inventory and lost encounter positions are excluded.

## Interpretation

The combined change prevents total inaction in this comparison, but produces renewed pressure/search rather than economic investment. Context alone changes the strategy; explicit deferral alone increases the preference to defer. These are prompt-sensitive, unvalidated classifier results, not evidence of a coherent long-term plan. No experimental variant has been installed as the default. Existing allowance curves, mission costs and saving rules are unchanged.

Every strategy/operation/region prompt, probability, token count and choice is retained in `build/local/commander-context-march-experiment-final/*.json`, with source and rules SHA-256 values, role provenance and original-save integrity in `manifest.json`. Oversized model packets fail explicitly; successful packets are not truncated. Source boundary saves are restricted to the first two minutes of the matching portfolio month so later mission state cannot enter this comparison. Python boundary checks: 45 passed, including incomplete coverage, hidden player state and future telemetry exclusion.

Run from G:\OpenXcom:

```powershell
.\build\local\laya-venv\Scripts\python.exe .\scripts\test-commander-context.py --save '.\build\local\user\xcom1\March 1.sav' --checkpoint 'C:\Users\Main PC 2\AppData\Local\Temp\uppward-v4' --out '.\build\local\commander-context-march-experiment-final'
```

This launches its own finite checkpoint process and does not use or stop the game's model service. It executes no missions and verifies that the original save hash is unchanged.
