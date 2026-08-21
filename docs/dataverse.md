# Path 1 — Dataverse (Direct)

The **simplest** Agent Evaluator build: the Power BI template reads Copilot Studio conversation transcripts
**straight from Dataverse** and parses them **inside the model** (Power Query M). No Fabric capacity,
no Lakehouse, no notebooks — just the `.pbit`, a Dataverse environment, and an org-data CSV.

> Want scheduled Spark ingestion, larger volumes, or the **PPAC message-credit** pages? Use
> [**Path 2 — Fabric**](../fabric/) instead.

```
Dataverse conversationtranscripts ─(native connector)─┐
                                                       ▼
                       Power Query M parser (in the model)
                                                       ▼
   Agent Sessions · Turns · Errors · Sub-Agent Calls · Performance · Catalogue
                                                       ▼
   + org data ─(direct CSV file path)─────────────────────────► dashboard
```

> **Just want to run it?** Open **[`Agent Evaluator.pbit`](./Agent%20Evaluator%20-%20Dataverse.pbit)**
> in Power BI Desktop, set the two parameters below, and **Load**.

---

## Connect the template

The `.pbit` is **pre-set to Dataverse** — you only set two parameters:

| Parameter | Required? | Value |
|---|---|---|
| **Dataverse Url** | **Yes** | your environment URL, e.g. `https://yourorg.crm.dynamics.com` — one environment per report ([several? use Fabric](./fabric.md)) |
| **CSV Folder Path** | **Yes** | folder containing `copilot_org_data.csv` (a local/synced/UNC folder, or a SharePoint document library URL) |

> **A folder, not a file path.** The template resolves each CSV it needs by name
> inside that one folder — currently `copilot_org_data.csv`. Keep the filename as
> exported. A SharePoint library URL refreshes cloud-to-cloud (OAuth2, no
> gateway); a local or UNC folder needs an on-premises data gateway.

On first refresh you'll get a one-time **Dataverse** sign-in: choose **Organizational account**, sign
in with an org login that can **read the Conversation Transcript table**, and set the source privacy
level to **Organizational** if prompted. Then enable **Scheduled refresh** in the Service as usual.

> **No app registration / client secret** — the report uses the native Dataverse connector with the
> refresher's own org login.

### No tenant? Run it from a local CSV

The template also reads transcripts straight from a CSV — no Dataverse, no Fabric, no
customer data. There is a **dedicated, pre-configured build** for this: see
**[`../data/`](../data)**, which ships with a ready-made synthetic
dataset (2,400 conversations, 8 agents, 90 days).

You can also switch *this* template over by hand:

| Parameter | Value in CSV mode |
|---|---|
| **Source Mode** | `TranscriptCSV` |
| **CSV Folder Path** | folder holding `conversationtranscripts.csv` + `copilot_org_data.csv` |
| **Dataverse Url** | leave blank — unused |

<details>
<summary><strong>More than one environment?</strong> — use the Fabric path</summary>

**This path reads one environment per report.** The **Dataverse Url** parameter takes a single
environment URL — it is not a list, and a semicolon-separated string will fail with
*"The given URL neither points to an OData service or a feed"*.

For several environments, use **[the Fabric path](./fabric.md)**. The parser notebook accepts a
list of environments, reads them all in one run, and lands the result in a Lakehouse:

```python
# ONE environment:   set DATAVERSE_URL and leave DATAVERSE_URLS = [].
# MANY environments: set DATAVERSE_URLS to a list (DATAVERSE_URL is then ignored).
DATAVERSE_URLS = [
    "https://org-a.crm.dynamics.com",
    "https://org-b.crm.dynamics.com",
]
```

Fabric is the better answer for a second reason. Dataverse keeps conversation transcripts for
about **30 days**, so a report reading Dataverse directly only ever sees the last month. The
Fabric notebook writes each run into the Lakehouse, so history **accumulates past the retention
window** — run it on a schedule and the report keeps everything it has ever collected, across
every environment you list.

| | Dataverse direct | Fabric |
|---|---|---|
| Environments | one per report | many, in one run |
| History | last ~30 days only | accumulates indefinitely |
| Setup | open the `.pbit` | notebooks + Lakehouse |

</details>


---

<details>
<summary><strong>What you need</strong> — environment, permissions & CSVs</summary>

**In your tenant**
- The **Dataverse environment URL** holding the Copilot Studio transcripts (Power Platform Admin
  Center → Environments → *your env* → **Environment URL**).
- A refresher sign-in with **Read** on the **Conversation Transcript** table — e.g. *System
  Administrator*, *System Customizer*, *Environment Maker*, or a least-privilege custom role.

**Supporting CSVs** (each pointed to by its own full-path parameter):

| File | Source export | Parameter | Required? |
|---|---|---|---|
| `copilot_org_data.csv` | Entra → Users (manual export) **or** a Graph `/users` → SharePoint landing flow | **Org Data CSV** | **Yes** (org filter on every page) |

Org data is read from the **raw portal export** — the model normalises headers and US-format dates
for you.

> **Org data stays a CSV (not Dataverse)** so you keep both acquisition methods — a manual Entra
> export, or an Entra-Graph → SharePoint landing flow.
</details>

<details>
<summary><strong>How the file paths work</strong> — connectors & gateway</summary>

Each CSV parameter takes a **full file path**, auto-detected:

| You enter | Connector | Refresh in the Service |
|---|---|---|
| A **SharePoint file URL** (`https://contoso.sharepoint.com/.../copilot_org_data.csv`) | `Web.Contents` | ✅ cloud-to-cloud, **no gateway** (source = *Organizational account* / OAuth2) |
| A **local / synced file** (`C:\AIBV\copilot_org_data.csv`) | `File.Contents` | needs an **on-premises data gateway** |
| A **UNC path** (`\\server\share\copilot_org_data.csv`) | `File.Contents` | needs a gateway |

> A **SharePoint file URL is easiest to schedule-refresh** — no gateway. Pointing at the exact file
> (not a folder) means the report won't silently miss a renamed export.
</details>

<details>
<summary><strong>How the transcript parser works</strong></summary>

The model carries Power Query functions (see
[`model_expressions_reference.tmdl`](./model_expressions_reference.tmdl)) that parse the raw
`conversationtranscripts` JSON into fact tables — entirely in the model, no external compute:

| M function | Produces |
|---|---|
| `RawTranscripts()` | one row per transcript (live from Dataverse) |
| `ParsedBase()` | parses each `content` JSON once into an `activities` list |
| `Parse_Sessions()` | `Agent Sessions` (one row per conversation) |
| `Parse_Turns()` | `Agent Turns` (per message, with intent / knowledge / feedback) |
| `Parse_Errors()` | `Agent Errors` |
| `Parse_SubAgents()` | `Agent Sub-Agent Calls` |
| `Parse_Performance()` | `Agent Performance` (per-conversation KPI fact) |

`Agent Catalogue` self-derives from the parsed sessions + sub-agents.

**Notes / limitations**
- **Topics** are classified by generic, customer-agnostic DAX — no extra services or LLM enrichment.
- **Agent name** resolves via the Dataverse bot lookup where exposed, else from transcript content.
- Token / plugin telemetry columns are null in this path (not in the transcript JSON); the value
  model doesn't depend on them.
- Conversation transcripts default to ~30-day retention in Dataverse — the dashboard sees only what
  the environment currently holds.
</details>

<details>
<summary><strong>Verifying the connection</strong></summary>

A built-in **`Dataverse Diagnostic`** table returns the live row count of `conversationtranscripts`
and `systemusers`. If `conversationtranscripts = 0` but `systemusers > 0`, the connection is fine —
the environment simply has no Copilot Studio transcripts in scope yet.
</details>

---

> **Credit / message-credit consumption** is **not** in this path — it's scoped to Copilot Studio
> transcript analytics (transcripts + org data). For **PPAC Copilot Studio
> message-credit** pages, use [**Path 2 — Fabric**](../fabric/).

⬅ Back to the [Agent Evaluator overview](../README.md).
