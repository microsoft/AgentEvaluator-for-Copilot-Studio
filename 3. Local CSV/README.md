# 3 · Local CSV — run Agent Evaluator with no tenant

The **fastest** way to see Agent Evaluator: the template reads Copilot Studio
conversation transcripts from a **local CSV file**. No Dataverse environment, no
Fabric capacity, no app registration, no customer data.

Bundled demo data is included, so this path works **out of the box** — open the
`.pbit`, point two parameters at the files in [`data/`](./data), and Load.

```
Local CSV path
  data/conversationtranscripts.csv ─┐
                                    ├─► Agent Evaluator - Local CSV.pbit ─► dashboard
  data/copilot_org_data.csv ────────┘        (parsed in-model, Power Query M)
```

> Ideal for demos, training, evaluating the template before committing to a
> rollout, and validating the parser offline.

---

## Quickstart

1. Open **[`Agent Evaluator - Local CSV.pbit`](./Agent%20Evaluator%20-%20Local%20CSV.pbit)**
   in Power BI Desktop.
2. Set the two file-path parameters (the template is **pre-set** to `TranscriptCSV`
   mode, so `Source Mode` needs no change):

   | Parameter | Required? | Value |
   |---|---|---|
   | **Source Mode** | pre-set | `TranscriptCSV` — leave as-is |
   | **Transcript CSV Path** | **Yes** | full path to `data\conversationtranscripts.csv` |
   | **Org Data CSV** | **Yes** | full path to `data\copilot_org_data.csv` |
   | **Dataverse Url** | no | leave blank — unused in this mode |

3. **Load.** Every page renders against the demo data.

> Use **full paths**, e.g.
> `C:\repos\AgentEvaluator-for-Copilot-Studio\3. Local CSV\data\conversationtranscripts.csv`.
> A SharePoint file URL (`https://…`) also works and refreshes cloud-to-cloud;
> local paths need an on-premises gateway if you publish to the Service.

---

## What's in the demo data

2,400 conversations over 90 days, 420 users, 8 agents — each agent given a
**deliberately different performance profile** so the Agent Evaluation page ranks
meaningfully instead of showing a flat wall of identical bars:

| Agent | Conversations | Resolved | Escalated |
|---|---:|---:|---:|
| IT Support Agent | 469 | 65.9% | 19.0% |
| HR Leave Assistant | 420 | 81.0% | 7.6% |
| Employee Self-Service | 367 | 66.8% | 14.2% |
| Payroll Helper | 288 | 48.3% | 26.4% |
| Travel & Expense Agent | 248 | 59.3% | 16.1% |
| Onboarding Guide | 235 | 66.0% | 11.1% |
| Procurement Advisor | 206 | 77.2% | 9.7% |
| Facilities Bot | 167 | 51.5% | 14.4% |

Overall: **65.8% resolved · 15.0% escalated · 19.2% abandoned**.

Every dashboard-facing column is populated, so no page renders empty:

- **Topics / intents** — 37 topics, 8,240 scored turns (mean confidence 0.83)
- **Knowledge** — 12 cited source files across ~1,180 turns
- **Grounding** — Internal / Mixed (Internal+Web) / Ungrounded
- **Errors** — 227 errors across 8 codes, split system vs user error
- **Feedback** — ~22% submit rate, ~70/30 positive/negative, with free-text comments
- **Sub-agents** — 776 connected-agent hand-off events
- **Users** — authenticated, anonymous and returning-user cohorts
- **Time** — 90 distinct days, business-hours and weekday weighted

All of it is synthetic. Fictional people at `contoso.com`, fictional agents,
fictional message text. No real tenant, user or conversation data.

### Files

| File | Used by |
|---|---|
| `data/conversationtranscripts.csv` | **Transcript CSV Path** — the transcripts |
| `data/copilot_org_data.csv` | **Org Data CSV** — drives the org filter on every page |
| `data/agents_365.csv` | *not read by this template* — provided for the Fabric path's `Copilot_Agent365_Lander.ipynb` |

---

## Regenerating the data

```bash
cd tools
python generate_sample_data.py                        # defaults: 2400 convs, 420 users, 90 days
python generate_sample_data.py --conversations 10000 --days 180
python generate_sample_data.py --seed 7               # a different but equally valid world
python generate_sample_data.py --end-date 2026-08-16  # fixed window (fully reproducible)
```

Seeded — the same arguments always produce the same data. Output lands in `data/`.

## Validating

```bash
cd tools
python validate_sample_data.py
```

Runs the **real** parser (`../../2. Fabric/notebooks/Copilot_Agent_Transcript_Parser.ipynb`)
over the generated CSV and reports row counts, per-column fill rates and
distributions. Exits non-zero if any dashboard-facing column would come out
empty. This runs in CI on every change.

---

## How outcome is scored

The parser does **not** read the explicit `SessionInfo.outcome` trace. It infers
the outcome from the conversation's **shape**:

| Shape | Scored as |
|---|---|
| a connected / sub-agent was invoked | `Escalated` |
| user turns but no bot reply | `Abandoned` |
| anything else | `Resolved` |

The generator deliberately builds conversations matching those shapes, so the
demo reflects what the shipped template actually shows rather than a flattering
fiction. Every conversation also carries a correct `SessionInfo.outcome`, so this
data keeps working if the parser is later changed to honour the explicit trace.

## Known gaps in this path

- **Credit Consumption** pages are empty by design — those tables are hardcoded
  to empty outside the Fabric path. Use [`../2. Fabric/`](../2.%20Fabric) for
  PPAC message-credit reporting.
- **Dataverse Diagnostic** is empty — it only populates in `Dataverse` mode.

⬅ Back to the [Agent Evaluator overview](../README.md).
