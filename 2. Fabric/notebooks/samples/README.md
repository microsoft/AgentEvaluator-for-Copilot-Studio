# Files-mode smoke test

A CI-friendly smoke test for the canonical transcript parser
(`../Copilot_Agent_Transcript_Parser.ipynb`). Runs the entire parse + build
chain in plain Python against the sample CSV in
`copilot_transcripts/conversationtranscripts.csv` — **no Fabric workspace,
no Dataverse tenant, no Spark required**.

## What it verifies

- Every code cell of the canonical notebook parses (AST-clean)
- Every build_* function runs against a realistic transcript shape
- All **6** output Delta tables produce non-zero row counts
- The deep-dive enrichment columns populate against the real Copilot
  Studio transcript schema (`SessionInfo`, `IntentRecognition`,
  `VariableAssignment`, `GPTAnswer`, `ConnectedAgentInitializeTraceData`,
  `AuthenticationTraceData`, `ErrorTraceData`)

> Cell indices are **derived at runtime**, not hardcoded. An earlier version
> hardcoded them; when the notebook was refactored the test ran off the end of
> the cell list and could never reach its own assertions, so it always exited
> non-zero regardless of parser health.

> `agent_variables` is produced by the **Dataverse (Direct)** Power Query path,
> not by this notebook. It is reported when present but is not required here.

## Run it

```bash
python smoketest_files_mode.py                    # the 8-transcript fixture below
python smoketest_files_mode.py /path/to/other.csv # any other transcripts CSV
```

Exit code 0 = pass, non-zero = fail.

To run it against the demo-scale synthetic dataset (2,400 conversations):

```bash
python smoketest_files_mode.py ../../../sample-data/conversationtranscripts.csv
```

## What's in the sample CSV

Eight synthetic transcripts (all UPNs anonymised to `user-NNN@example.local`),
each exercising a different combination of trace types:

| # | Shape | Tests |
|---|---|---|
| 1 | Resolved single-agent (`SessionInfo` + `IntentRecognition` + `VariableAssignment`) | Explicit outcome, topic, variables |
| 2 | Abandoned (user gave up) | `is_authenticated`, abandonment |
| 3 | `ErrorTraceData` present | `agent_errors`, `ErrorCategory` |
| 4 | `ConnectedAgentInitializeTraceData` | `agent_subagents`, `MultiAgentSession` |
| 5 | Multiple `VariableAssignment` | `agent_variables` decomposition |
| 6 | `GPTAnswer` + `PluginInvocationTraceData` | `GenerativeResponseCount`, `PluginCallCount` |
| 7 | Anonymous (no `aadObjectId`) | `is_authenticated = False` |
| 8 | Returning user (same `aadObjectId` as #1) | `is_returning_user = True` |

## Expected output

```
SMOKE TEST RESULT — row counts per table
  ✓ dbo.agent_sessions              rows:      8   cols: 31
  ✓ dbo.agent_turns                 rows:     16   cols: 17
  ✓ dbo.agent_errors                rows:      1   cols: 6
  ✓ dbo.agent_subagents             rows:      2   cols: 8
  ✓ dbo.agent_catalogue             rows:      8   cols: 3
  ✓ dbo.agent_performance           rows:      8   cols: 57
SMOKE TEST: PASSED ✓
```
