# Path 2 — Fabric

The **Fabric / Lakehouse** build of Agent Evaluator. Notebooks land your Copilot Studio
data as Delta tables in a Lakehouse; the Power BI template is a thin client over the Lakehouse SQL
endpoint. Focused on **Copilot Studio agent performance, quality, evaluation, and message-credit
consumption** — not the broader M365 Copilot value dashboard.

> Prefer the simplest footprint? [**Path 1 — Dataverse (Direct)**](../1.%20Dataverse%20(Direct)/)
> reads transcripts straight from Dataverse in Power Query — no Fabric capacity,
> no notebooks. Use **this Fabric build** when you want scheduled Spark ingestion, larger volumes, or
> the **PPAC message-credit** pages.

## What's here

| Item | Purpose |
|---|---|
| `Agent Evaluator.pbit` | The Power BI template — Copilot Studio pages (Quality & Performance, Conversation Flow & Quality, Topic Explorer, Knowledge Files, Error Analysis, User Feedback) **plus** the PPAC **Credit Consumption** page, and reference appendices. |
| `notebooks/Copilot_Agent_Transcript_Parser.ipynb` | Parses **Copilot Studio agent transcripts** (Dataverse `ConversationTranscript`) into the agent Delta tables (sessions, turns, errors, sub-agents, catalogue, performance). |
| `notebooks/Copilot_Credit_Consumption_Ingester.ipynb` | Ingests the **Power Platform Admin Center (PPAC)** per-agent Copilot Studio **message-credit** export into the `credit_consumption_*` tables (drives the Credit Consumption page). |

## Quick start

### 1. Create a Lakehouse
In a Fabric workspace on a capacity (F2+ or trial): **+ New → Lakehouse**. Note its **SQL endpoint**
(`<workspace-guid>.datawarehouse.fabric.microsoft.com`).

### 2. Register an Entra app
Microsoft Graph **application** permissions (admin-consented), plus environment access for the
Copilot Studio sources:

| Access | For |
|---|---|
| Dataverse **Read** on `ConversationTranscript` (System Customizer / Environment Maker) | Transcript parser |
| **Global / Billing Administrator** to export PPAC `MCSMessages` reports | Credit consumption |

### 3. Run the notebooks
Import each into the workspace, attach + pin your Lakehouse, fill the `# === CONFIG ===` cell, run.

| Notebook | Output tables |
|---|---|
| `Copilot_Agent_Transcript_Parser.ipynb` | `agent_sessions`, `agent_turns`, `agent_errors`, `agent_subagents`, `agent_catalogue`, `agent_performance` |
| `Copilot_Credit_Consumption_Ingester.ipynb` | `credit_consumption_tenant` / `_agent` / `_user` |

> **Org data (optional):** pages that break users down by department use a `copilot_org_data` table.
> Land it from an Entra `/users` export if you want org-level slicing; otherwise those breakdowns show
> "Unknown".

### 4. Connect the template
Open **`Agent Evaluator.pbit`** in Power BI Desktop, set the **Fabric SQL
Endpoint** and **Lakehouse Name** parameters, and leave `Enable_Consumption = Include`
if you ran the credit ingester (set it to `Exclude` to skip the Credit Consumption
page). **Load**, then **Publish**.

### 5. Schedule
Schedule the notebooks (or a Fabric pipeline), then enable dataset **Scheduled refresh** in the Service.

---

## Pages

**Studio** — Quality & Performance · Conversation Flow & Quality · Topic Explorer · Knowledge Files ·
Error Analysis · User Feedback · **Credit Consumption (PPAC)**, plus **Appendix** — Key Concepts ·
Glossary · Signal-Impact Table.
