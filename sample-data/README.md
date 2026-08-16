# Sample data — run Agent Evaluator with no tenant

Synthetic demo data so anyone can open the template and see a **fully populated
dashboard** with no Dataverse environment, no Fabric capacity, and no customer data.

Everything here is generated. No real users, tenants, agents or message text.

## Files

| File | Feeds the parameter | Required? |
|---|---|---|
| `conversationtranscripts.csv` | **Transcript CSV Path** | yes |
| `copilot_org_data.csv` | **Org Data CSV** | yes |
| `agents_365.csv` | **Agent 365 CSV** | optional |

## Quickstart — local CSV mode

1. Open **`1. Dataverse (Direct)/Agent Evaluator - Dataverse.pbit`** in Power BI Desktop.
2. When prompted for parameters, set:

   | Parameter | Value |
   |---|---|
   | **Source Mode** | `TranscriptCSV` |
   | **Transcript CSV Path** | full path to `sample-data/conversationtranscripts.csv` |
   | **Org Data CSV** | full path to `sample-data/copilot_org_data.csv` |
   | **Agent 365 CSV** | full path to `sample-data/agents_365.csv` (or leave blank) |
   | **Dataverse Url** | leave blank — unused in this mode |

3. **Load.** Every page renders against the synthetic data.

> `Source Mode` accepts `Dataverse` (live transcripts), `Fabric` (Lakehouse Delta
> tables) or `TranscriptCSV` (this mode). Only `TranscriptCSV` needs no tenant.

## What the data looks like

2,400 conversations over 90 days, 420 users, 8 agents with **deliberately different
performance profiles** so the Agent Evaluation page ranks meaningfully:

| Agent | Conversations | Resolved | Escalated |
|---|---:|---:|---:|
| IT Support Agent | 481 | 62.8% | 22.7% |
| HR Leave Assistant | 413 | 85.2% | 4.8% |
| Employee Self-Service | 374 | 74.1% | 13.4% |
| Payroll Helper | 257 | 41.6% | 33.1% |
| Onboarding Guide | 254 | 69.3% | 11.4% |
| Travel & Expense Agent | 242 | 55.4% | 21.9% |
| Procurement Advisor | 227 | 81.1% | 7.9% |
| Facilities Bot | 152 | 57.2% | 17.8% |

Overall: **67.5% resolved · 16.3% escalated · 16.2% abandoned**.

Also exercised, so no page renders empty:

- **Topics / intents** — 37 topics with intent scores (mean 0.83)
- **Knowledge** — 12 cited source files across ~1,200 turns
- **Grounding** — Internal / Mixed (Internal+Web) / Ungrounded
- **Errors** — 8 error codes, split system vs user error
- **Feedback** — ~22% submit rate, ~70/30 positive/negative, with free-text comments
- **Sub-agents** — connected-agent hand-offs for escalations
- **Users** — authenticated, anonymous and returning-user cohorts
- Business-hours and weekday-weighted timestamps

## Regenerating

```bash
python generate_sample_data.py                      # defaults: 2400 convs, 420 users, 90 days
python generate_sample_data.py --conversations 10000 --days 180
python generate_sample_data.py --seed 7             # a different but equally valid world
python generate_sample_data.py --end-date 2026-08-13 # fixed window (reproducible)
```

Seeded — the same arguments always produce the same data.

## Validating

```bash
python validate_sample_data.py
```

Runs the **real** parser (`2. Fabric/notebooks/Copilot_Agent_Transcript_Parser.ipynb`)
over the generated CSV and reports row counts, per-column fill rates and
distributions. Exits non-zero if a dashboard-facing column would come out empty.

You can also run the parser smoke test directly against this data:

```bash
cd "../2. Fabric/notebooks/samples"
python smoketest_files_mode.py ../../../sample-data/conversationtranscripts.csv
```

## Note on how outcome is scored

The parser does **not** read the explicit `SessionInfo.outcome` trace. It derives
the outcome from conversation shape:

| Shape | Scored as |
|---|---|
| connected/sub-agent invoked | `Escalated` |
| user turns but no bot reply | `Abandoned` |
| anything else | `Resolved` |

The generator deliberately builds conversations that match those shapes, so the
demo reflects what the shipped template will actually show. If the parser is ever
changed to honour the explicit outcome trace, this data already carries a correct
`SessionInfo.outcome` on every conversation and will keep working.
