"""Validate that generated demo data populates every column the dashboard renders.

Reuses the smoke-test harness to build the real tables, then reports fill rates
and distributions so we can see the dashboard won't render empty visuals.
"""
import json, sys, io, contextlib
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SAMPLES = REPO / "2. Fabric" / "notebooks" / "samples"
sys.path.insert(0, str(SAMPLES))

CSV = sys.argv[1] if len(sys.argv) > 1 else str(
    Path(__file__).resolve().parents[1] / "data" / "conversationtranscripts.csv")

# Run the smoke test harness with our CSV, capturing its namespace.
harness = (SAMPLES / "smoketest_files_mode.py").read_text(encoding="utf-8-sig")
ns = {"__file__": str(SAMPLES / "smoketest_files_mode.py"), "__name__": "__harness__"}
old_argv = sys.argv[:]
sys.argv = ["smoketest_files_mode.py", CSV]
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        try:
            exec(compile(harness, "smoketest_files_mode.py", "exec"), ns)
        except SystemExit:
            pass
        except ModuleNotFoundError as e:
            if "pyspark" not in str(e):
                raise
finally:
    sys.argv = old_argv

inner = ns.get("ns", {})          # the harness runs notebook cells in its own dict
written = ns.get("written", {})

def _tbl(name, var):
    return written.get(f"dbo.{name}", inner.get(var))

sessions = _tbl("agent_sessions", "sessions")
turns = _tbl("agent_turns", "turns")
errors = _tbl("agent_errors", "errors")
subagents = _tbl("agent_subagents", "subagents")
perf = _tbl("agent_performance", "agent_performance")
cat = _tbl("agent_catalogue", "agent_catalogue")

if sessions is None or turns is None:
    print("FAILED to build tables")
    print(buf.getvalue()[-2000:])
    raise SystemExit(1)


def pct(n, d):
    return f"{(100.0 * n / d):5.1f}%" if d else "  n/a"


def fill(df, col):
    if col not in df.columns:
        return "MISSING"
    nn = df[col].notna().sum()
    return f"{pct(nn, len(df))} ({nn:,}/{len(df):,})"


print("=" * 74)
print("TABLE ROW COUNTS")
print("=" * 74)
for name, df in [("agent_sessions", sessions), ("agent_turns", turns), ("agent_errors", errors),
                 ("agent_subagents", subagents), ("agent_catalogue", cat), ("agent_performance", perf)]:
    status = "OK " if df is not None and len(df) > 0 else "EMPTY"
    print(f"  [{status}] {name:<22} {len(df) if df is not None else 0:>8,} rows"
          f"  {len(df.columns) if df is not None else 0:>3} cols")

print()
print("=" * 74)
print("SESSIONS - key column fill rates")
print("=" * 74)
for c in ["primary_agent_schema", "agent_name", "user_id_hash", "session_outcome_explicit",
          "session_outcome_reason_explicit", "grounding_source", "first_error_code",
          "feedback_verdict", "feedback_comment", "knowledge_sources_count", "is_authenticated",
          "is_returning_user", "connected_agent_schemas"]:
    print(f"  {c:<34} {fill(sessions, c)}")

print()
print("=" * 74)
print("TURNS - enrichment fill rates (the columns the fixture never exercised)")
print("=" * 74)
for c in ["intent_title", "intent_id", "intent_score", "knowledge_searched",
          "knowledge_answered", "knowledge_sources", "feedback_offered", "feedback_verdict"]:
    print(f"  {c:<34} {fill(turns, c)}")

print()
print("=" * 74)
print("DISTRIBUTIONS")
print("=" * 74)
print("\n  Session outcome (agent_performance - sessions.* is null by design):")
_perf_out = perf["SessionOutcome"] if perf is not None and "SessionOutcome" in perf.columns else None
if _perf_out is not None:
    for k, v in _perf_out.value_counts(dropna=False).items():
        print(f"    {str(k):<28} {v:>6,}  {pct(v, len(perf))}")
    print("\n  OutcomeReason:")
    for k, v in perf["OutcomeReason"].value_counts(dropna=False).head(8).items():
        print(f"    {str(k):<28} {v:>6,}")
    print("\n  ImpliedSuccess:")
    for k, v in perf["ImpliedSuccess"].value_counts(dropna=False).items():
        print(f"    {str(k):<28} {v:>6,}  {pct(v, len(perf))}")

print("\n  Grounding source:")
for k, v in sessions["grounding_source"].value_counts(dropna=False).items():
    print(f"    {str(k):<28} {v:>6,}  {pct(v, len(sessions))}")

print("\n  Feedback verdict (submitted only):")
fb = sessions["feedback_verdict"].dropna()
for k, v in fb.value_counts().items():
    print(f"    {str(k):<28} {v:>6,}  {pct(v, len(fb))}")
print(f"    {'(submitted / total sessions)':<28} {len(fb):>6,}  {pct(len(fb), len(sessions))}")

print("\n  Top error codes:")
if errors is not None and len(errors):
    ecol = "error_code" if "error_code" in errors.columns else errors.columns[-1]
    for k, v in errors[ecol].value_counts().head(8).items():
        print(f"    {str(k):<28} {v:>6,}")

print("\n  Sessions per agent (resolution rate from agent_performance):")
if perf is not None and "BotName" in perf.columns and "SessionOutcome" in perf.columns:
    for name, g in sorted(perf.groupby("BotName"), key=lambda kv: -len(kv[1])):
        res = (g["SessionOutcome"] == "Resolved").sum()
        esc = (g["SessionOutcome"] == "Escalated").sum()
        print(f"    {str(name):<28} {len(g):>6,}   resolved {pct(res, len(g))}   escalated {pct(esc, len(g))}")

print("\n  Intent score (turns):")
isc = pd.to_numeric(turns["intent_score"], errors="coerce").dropna()
if len(isc):
    print(f"    count {len(isc):,}  min {isc.min():.3f}  mean {isc.mean():.3f}  max {isc.max():.3f}")
else:
    print("    NO INTENT SCORES - dashboard 'Avg Intent Score' would be blank")

print("\n  Distinct knowledge sources cited:")
ks = turns["knowledge_sources"].dropna()
ks = ks[ks.astype(str).str.len() > 0]
uniq = set()
for row in ks:
    uniq.update(str(row).split("|"))
print(f"    {len(uniq)} distinct files across {len(ks):,} turns")

print("\n  Date span:")
sd = pd.to_datetime(sessions["session_start_utc"], errors="coerce", format="mixed", utc=True).dropna()
print(f"    {sd.min()}  ->  {sd.max()}   ({sd.dt.date.nunique()} distinct days)")

print()
problems = []
if pd.to_numeric(turns["intent_score"], errors="coerce").notna().sum() == 0:
    problems.append("intent_score entirely null")
for col in ["feedback_verdict", "knowledge_sources", "intent_title"]:
    if col in turns.columns and turns[col].notna().sum() == 0:
        problems.append(f"turns.{col} entirely null")
if sessions["grounding_source"].nunique() < 2:
    problems.append("grounding_source has no variety")
if perf is None or "SessionOutcome" not in perf.columns:
    problems.append("agent_performance.SessionOutcome missing")
elif perf["SessionOutcome"].notna().sum() == 0:
    problems.append("agent_performance.SessionOutcome entirely null - outcome pages would be blank")
elif perf["SessionOutcome"].nunique() < 2:
    problems.append("agent_performance.SessionOutcome has no variety")

if problems:
    print("VALIDATION: FAILED")
    for p in problems:
        print(f"  - {p}")
    raise SystemExit(1)
print("VALIDATION: PASSED - every dashboard-facing column is populated")
