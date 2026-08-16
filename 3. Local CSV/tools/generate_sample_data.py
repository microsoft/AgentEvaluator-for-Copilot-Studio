"""Generate demo-scale synthetic data for Agent Evaluator (local CSV mode).

Produces two CSVs that let anyone open the template with **no Dataverse tenant,
no Fabric capacity and no real customer data**:

    conversationtranscripts.csv   -> Transcript CSV Path   (Source Mode = "TranscriptCSV")
    copilot_org_data.csv          -> Org Data CSV          (required)

Everything is synthetic and seeded, so re-running reproduces identical output.
No real users, tenants, agents or message text.

Usage:
    python generate_sample_data.py [--conversations 2400] [--days 90] [--seed 42]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "data"

# --------------------------------------------------------------------------------------
# Reference data - all fictional
# --------------------------------------------------------------------------------------

DEPARTMENTS = [
    ("Human Resources", ["HR Advisor", "People Partner", "Talent Coordinator", "HR Manager"]),
    ("Finance", ["Financial Analyst", "Accounts Payable Clerk", "Controller", "Finance Manager"]),
    ("Information Technology", ["Support Engineer", "Systems Administrator", "IT Manager", "Service Desk Analyst"]),
    ("Sales", ["Account Executive", "Sales Development Rep", "Sales Manager", "Solution Specialist"]),
    ("Marketing", ["Campaign Manager", "Content Strategist", "Marketing Analyst"]),
    ("Operations", ["Operations Analyst", "Logistics Coordinator", "Operations Manager"]),
    ("Legal", ["Legal Counsel", "Contracts Analyst", "Compliance Officer"]),
    ("Customer Service", ["Support Advisor", "Escalations Specialist", "Team Lead"]),
    ("Engineering", ["Software Engineer", "QA Engineer", "Engineering Manager", "Site Reliability Engineer"]),
    ("Facilities", ["Facilities Coordinator", "Workplace Manager"]),
]

OFFICES = [
    ("London", "United Kingdom"),
    ("Manchester", "United Kingdom"),
    ("Dublin", "Ireland"),
    ("Amsterdam", "Netherlands"),
    ("New York", "United States"),
    ("Seattle", "United States"),
    ("Singapore", "Singapore"),
    ("Sydney", "Australia"),
]

FIRST_NAMES = [
    "Alex", "Sam", "Jordan", "Riley", "Morgan", "Casey", "Jamie", "Taylor", "Avery", "Quinn",
    "Rowan", "Skyler", "Harper", "Emerson", "Finley", "Dakota", "Reese", "Sawyer", "Elliot", "Marlow",
    "Priya", "Arun", "Mei", "Hiro", "Ines", "Luca", "Nadia", "Omar", "Sofia", "Tomas",
]
LAST_NAMES = [
    "Bennett", "Carver", "Delgado", "Ellery", "Fairbanks", "Grady", "Hollis", "Ingram", "Jarvis", "Keane",
    "Lockhart", "Mercer", "Novak", "Oakley", "Prescott", "Quill", "Rutherford", "Sinclair", "Thorne", "Underwood",
    "Vance", "Whitlock", "Yates", "Ziegler", "Amara", "Barros", "Chandra", "Duval", "Espinosa", "Fontaine",
]

# Each agent gets a distinct performance profile so the Agent Evaluation page ranks meaningfully.
AGENTS = [
    {
        "schema": "cr9a2_hrLeaveAgent", "name": "HR Leave Assistant", "share": 0.18,
        "resolved": 0.82, "escalated": 0.07, "error_rate": 0.03, "knowledge_rate": 0.70,
        "positive_bias": 0.86, "web_rate": 0.02, "avg_turns": 3,
        "topics": ["LeaveBalance", "BookLeave", "CancelLeave", "CarryOverPolicy", "SicknessAbsence"],
    },
    {
        "schema": "cr9a2_itSupportAgent", "name": "IT Support Agent", "share": 0.20,
        "resolved": 0.64, "escalated": 0.21, "error_rate": 0.11, "knowledge_rate": 0.62,
        "positive_bias": 0.64, "web_rate": 0.18, "avg_turns": 5,
        "topics": ["PasswordReset", "VPNAccess", "SoftwareInstall", "HardwareRequest", "MailboxIssue", "PrinterIssue"],
    },
    {
        "schema": "cr9a2_payrollAgent", "name": "Payroll Helper", "share": 0.11,
        "resolved": 0.47, "escalated": 0.29, "error_rate": 0.22, "knowledge_rate": 0.41,
        "positive_bias": 0.42, "web_rate": 0.01, "avg_turns": 6,
        "topics": ["PaySlipStatus", "TaxCodeQuery", "OvertimeClaim", "PensionContribution", "ExpenseReimbursement"],
    },
    {
        "schema": "cr9a2_employeeSelfService", "name": "Employee Self-Service", "share": 0.16,
        "resolved": 0.71, "escalated": 0.14, "error_rate": 0.06, "knowledge_rate": 0.55,
        "positive_bias": 0.74, "web_rate": 0.05, "avg_turns": 5,
        "topics": ["GeneralEnquiry", "PolicyLookup", "RouteToSpecialist", "BenefitsOverview"],
        "orchestrator": True,
    },
    {
        "schema": "cr9a2_procurementAgent", "name": "Procurement Advisor", "share": 0.09,
        "resolved": 0.79, "escalated": 0.09, "error_rate": 0.04, "knowledge_rate": 0.78,
        "positive_bias": 0.81, "web_rate": 0.09, "avg_turns": 4,
        "topics": ["RaisePurchaseOrder", "SupplierLookup", "InvoiceQuery", "ContractRenewal"],
    },
    {
        "schema": "cr9a2_onboardingAgent", "name": "Onboarding Guide", "share": 0.10,
        "resolved": 0.68, "escalated": 0.12, "error_rate": 0.07, "knowledge_rate": 0.66,
        "positive_bias": 0.70, "web_rate": 0.03, "avg_turns": 4,
        "topics": ["FirstDayChecklist", "EquipmentSetup", "BuddyAssignment", "TrainingPlan"],
    },
    {
        "schema": "cr9a2_travelAgent", "name": "Travel & Expense Agent", "share": 0.10,
        "resolved": 0.61, "escalated": 0.18, "error_rate": 0.13, "knowledge_rate": 0.50,
        "positive_bias": 0.58, "web_rate": 0.24, "avg_turns": 5,
        "topics": ["BookTravel", "ExpenseClaim", "MileageRate", "VisaGuidance", "TravelPolicy"],
    },
    {
        "schema": "cr9a2_facilitiesAgent", "name": "Facilities Bot", "share": 0.06,
        "resolved": 0.55, "escalated": 0.16, "error_rate": 0.15, "knowledge_rate": 0.38,
        "positive_bias": 0.51, "web_rate": 0.02, "avg_turns": 3,
        "topics": ["DeskBooking", "MeetingRoom", "AccessBadge", "MaintenanceRequest"],
    },
]

SUB_AGENT_TARGETS = [
    "cr9a2_itSupportAgent", "cr9a2_payrollAgent", "cr9a2_hrLeaveAgent", "cr9a2_procurementAgent",
]

ERROR_CODES = [
    ("KnowledgeSearchFailed", False), ("PluginInvocationTimeout", False), ("AuthenticationFailed", True),
    ("ConnectorRequestFailed", False), ("RateLimitExceeded", False), ("InvalidUserInput", True),
    ("ContentFilterBlocked", False), ("BackendUnavailable", False),
]

KNOWLEDGE_SOURCES = [
    "HR Policy Handbook 2026.pdf", "Annual Leave Policy.docx", "IT Service Catalogue.pdf",
    "VPN Setup Guide.docx", "Payroll Calendar 2026.xlsx", "Expense Policy v4.pdf",
    "Procurement Thresholds.docx", "Onboarding Checklist.pdf", "Travel Booking Guide.pdf",
    "Facilities Handbook.pdf", "Benefits Summary 2026.pdf", "Code of Conduct.pdf",
]

USER_PROMPTS = {
    "LeaveBalance": "How many days annual leave do I have left this year?",
    "BookLeave": "I want to book leave from the 12th to the 19th",
    "CancelLeave": "Can I cancel the leave I booked for next Friday?",
    "CarryOverPolicy": "How many leave days can I carry into next year?",
    "SicknessAbsence": "How do I report a sickness absence?",
    "PasswordReset": "I'm locked out and need my password reset",
    "VPNAccess": "The VPN keeps disconnecting when I work from home",
    "SoftwareInstall": "How do I get Visio installed on my laptop?",
    "HardwareRequest": "I need a second monitor for my desk",
    "MailboxIssue": "My mailbox is full and I can't send email",
    "PrinterIssue": "The printer on level 3 isn't responding",
    "PaySlipStatus": "Where can I find last month's payslip?",
    "TaxCodeQuery": "My tax code looks wrong on this month's pay",
    "OvertimeClaim": "How do I claim overtime for last weekend?",
    "PensionContribution": "Can I increase my pension contribution?",
    "ExpenseReimbursement": "When will my expense claim be reimbursed?",
    "GeneralEnquiry": "Who do I speak to about a contract change?",
    "PolicyLookup": "What's the policy on working from abroad?",
    "RouteToSpecialist": "I need help with something payroll related",
    "BenefitsOverview": "What benefits am I entitled to?",
    "RaisePurchaseOrder": "I need to raise a PO for a new supplier",
    "SupplierLookup": "Is Contoso Ltd an approved supplier?",
    "InvoiceQuery": "An invoice hasn't been paid, can you check?",
    "ContractRenewal": "When does our licence contract renew?",
    "FirstDayChecklist": "What do I need to do on my first day?",
    "EquipmentSetup": "How do I set up my new laptop?",
    "BuddyAssignment": "Who is my onboarding buddy?",
    "TrainingPlan": "What training do I need to complete this month?",
    "BookTravel": "I need to book a flight to Amsterdam next month",
    "ExpenseClaim": "How do I submit an expense claim for a hotel?",
    "MileageRate": "What's the current mileage rate?",
    "VisaGuidance": "Do I need a visa to travel to Singapore for work?",
    "TravelPolicy": "Can I book premium economy on a long haul flight?",
    "DeskBooking": "How do I book a desk for Tuesday?",
    "MeetingRoom": "I need a meeting room for 8 people",
    "AccessBadge": "My access badge isn't working at the main door",
    "MaintenanceRequest": "The air conditioning on level 2 is broken",
}

BOT_RESOLVED = [
    "You have {n} days remaining. Anything else I can help with?",
    "That's all sorted for you - confirmation is on its way.",
    "Done. I've updated the record and sent you a summary.",
    "Here's what you need: I've linked the relevant policy below.",
]
BOT_ESCALATED = [
    "I'll pass this to a specialist who can help further.",
    "This needs a human review - I'm routing you to the service desk now.",
    "Let me connect you with the team that handles this.",
]
BOT_ABANDONED = [
    "Could you give me a bit more detail about what you need?",
    "I'm not sure I follow - can you rephrase that?",
    "I couldn't find a match for that. Would you like to try again?",
]
BOT_ERROR = [
    "Sorry, I couldn't retrieve that right now. Please try again shortly.",
    "Something went wrong on my side - I wasn't able to complete that.",
]

FEEDBACK_POSITIVE = [
    "Quick and accurate, thanks.", "Exactly what I needed.", "Saved me a call to the service desk.",
    "Really helpful, sorted in seconds.", "",
]
FEEDBACK_NEGATIVE = [
    "Didn't answer my question.", "Kept looping back to the same reply.",
    "Had to contact the service desk anyway.", "Couldn't understand what I was asking.", "",
]


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

def stable_guid(rng: random.Random) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def weighted_choice(rng: random.Random, items, weight_key: str):
    total = sum(i[weight_key] for i in items)
    r = rng.uniform(0, total)
    acc = 0.0
    for i in items:
        acc += i[weight_key]
        if r <= acc:
            return i
    return items[-1]


def business_timestamp(rng: random.Random, start: datetime, days: int) -> datetime:
    """Weekday- and business-hours-weighted timestamp so trend charts look real."""
    d = start
    for _ in range(12):
        day_offset = rng.randint(0, days - 1)
        d = start + timedelta(days=day_offset)
        if d.weekday() >= 5 and rng.random() > 0.12:   # keep ~12% weekend traffic
            continue
        break
    hour = rng.choices(
        population=list(range(7, 20)),
        weights=[3, 7, 12, 14, 13, 10, 11, 13, 12, 9, 5, 3, 2],
        k=1,
    )[0]
    return d.replace(hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59), microsecond=0)


def build_users(rng: random.Random, n_users: int):
    users = []
    seen = set()
    for _ in range(n_users):
        dept, titles = rng.choice(DEPARTMENTS)
        city, country = rng.choice(OFFICES)
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        base = f"{first.lower()}.{last.lower()}"
        upn = f"{base}@contoso.com"
        n = 2
        while upn in seen:
            upn = f"{base}{n}@contoso.com"
            n += 1
        seen.add(upn)
        users.append({
            "id": stable_guid(rng),
            "userPrincipalName": upn,
            "displayName": f"{first} {last}",
            "department": dept,
            "jobTitle": rng.choice(titles),
            "officeLocation": city,
            "country": country,
            "companyName": "Contoso Ltd",
            "usageLocation": country,
        })
    for u in users:
        peers = [p for p in users if p["department"] == u["department"] and p is not u]
        u["managerUPN"] = rng.choice(peers)["userPrincipalName"] if peers else ""
    return users


# --------------------------------------------------------------------------------------
# Transcript construction
# --------------------------------------------------------------------------------------

def build_conversation(rng, agent, user, started: datetime):
    """Return the Copilot Studio `content` JSON for one conversation."""
    acts = []
    ts = int(started.timestamp() * 1000)

    def bump(lo=800, hi=9000):
        nonlocal ts
        ts += rng.randint(lo, hi)
        return ts

    topic = rng.choice(agent["topics"])
    anonymous = rng.random() < 0.08
    user_ref = (
        {"role": "user", "id": user["userPrincipalName"], "aadObjectId": user["id"]}
        if not anonymous else {"role": "user", "id": "anonymous"}
    )
    bot_ref = {"role": "bot", "id": agent["schema"], "name": agent["name"]}

    roll = rng.random()
    if roll < agent["resolved"]:
        outcome = "Resolved"
    elif roll < agent["resolved"] + agent["escalated"]:
        outcome = "Escalated"
    else:
        outcome = "Abandoned"

    has_error = rng.random() < agent["error_rate"]
    searched_knowledge = rng.random() < agent["knowledge_rate"]

    # IMPORTANT - how the shipped parser scores outcome (build_agent_performance):
    #   connected agents present            -> Escalated
    #   user turns but NO bot reply         -> Abandoned
    #   otherwise                           -> Resolved
    # The explicit SessionInfo.outcome trace is NOT read by the parser, so the
    # generated conversation SHAPE has to produce the intended outcome. We still
    # emit SessionInfo because real transcripts carry it.
    escalates = outcome == "Escalated"
    abandons = outcome == "Abandoned"

    acts.append({
        "type": "trace", "valueType": "InitializeTraceData", "timestampMs": ts,
        "value": {"botSchemaName": agent["schema"], "locale": "en-US", "channelId": "msteams"},
    })
    if not anonymous:
        acts.append({
            "type": "trace", "valueType": "AuthenticationTraceData", "timestampMs": bump(100, 600),
            "value": {"isAuthenticated": True, "userId": user["id"], "connectionName": "Authorization"},
        })

    turns = max(1, int(rng.gauss(agent["avg_turns"], 1.4)))
    if abandons:
        # Abandoned: the user asked (once or twice) and never got a bot reply.
        turns = rng.randint(1, 2)

    for turn_idx in range(turns):
        user_msg_id = "msg-" + uuid.UUID(int=rng.getrandbits(128), version=4).hex[:12]
        text = USER_PROMPTS.get(topic, "Can you help me with something?") if turn_idx == 0 else rng.choice([
            "That's not quite what I meant.", "Can you check again please?",
            "Thanks - and what about next month?", "Okay, and where do I find that?",
        ])
        acts.append({
            "type": "message", "id": user_msg_id, "timestampMs": bump(1200, 20000),
            "channelId": "msteams", "from": dict(user_ref), "text": text,
        })
        score = round(rng.uniform(0.82, 0.99) if outcome == "Resolved" else rng.uniform(0.38, 0.86), 3)
        acts.append({
            "type": "trace", "valueType": "IntentRecognition", "timestampMs": bump(80, 500),
            "replyToId": user_msg_id,
            "value": {"intentTitle": topic, "intentId": "topic-" + topic, "intentScore": score},
        })

        bot_msg_id = "msg-" + uuid.UUID(int=rng.getrandbits(128), version=4).hex[:12]

        if searched_knowledge and turn_idx == 0:
            cited = rng.sample(KNOWLEDGE_SOURCES, rng.randint(1, 3))
            answered = outcome == "Resolved" or rng.random() < 0.5
            acts.append({
                "type": "trace", "valueType": "KnowledgeTraceData", "timestampMs": bump(200, 2500),
                "replyToId": bot_msg_id,
                "value": {
                    "isKnowledgeSearched": True,
                    "completionState": "Answered" if answered else "NotAnswered",
                    "citedKnowledgeSources": cited,
                },
            })

        if rng.random() < agent["web_rate"]:
            acts.append({
                "type": "trace", "name": "UniversalSearchTrace", "timestampMs": bump(150, 1800),
                "value": {
                    "knowledgeSources": ["SharePoint"],
                    "searchContextTraceInfo": {
                        "endpoints": ["https://www.bing.com/search", "https://contoso.sharepoint.com"]
                    },
                },
            })

        if rng.random() < 0.55:
            acts.append({
                "type": "trace", "valueType": "GenerativeAIResponseTraceData", "timestampMs": bump(200, 2000),
                "value": {"responseType": "GenerativeAnswer",
                          "promptTokenCount": rng.randint(180, 1400),
                          "completionTokenCount": rng.randint(40, 420)},
            })
        if rng.random() < 0.22:
            acts.append({
                "type": "trace", "valueType": "PluginInvocationTraceData", "timestampMs": bump(200, 3000),
                "value": {"pluginName": topic + "Connector", "isSuccess": rng.random() > 0.18},
            })

        if has_error and turn_idx == turns - 1:
            code, is_user_err = rng.choice(ERROR_CODES)
            acts.append({
                "type": "trace", "valueType": "ErrorTraceData", "timestampMs": bump(150, 1200),
                "value": {"errorCode": code, "isUserError": is_user_err,
                          "errorMessage": code + " raised while handling " + topic},
            })
            bot_text = rng.choice(BOT_ERROR)
        elif turn_idx < turns - 1:
            bot_text = rng.choice([
                "Let me check that for you.", "One moment while I look that up.",
                "I've found a couple of options - which suits you?",
            ])
        elif outcome == "Resolved":
            bot_text = rng.choice(BOT_RESOLVED).replace("{n}", str(rng.randint(3, 25)))
        elif outcome == "Escalated":
            bot_text = rng.choice(BOT_ESCALATED)
        else:
            bot_text = rng.choice(BOT_ABANDONED)

        bot_act = {
            "type": "message", "id": bot_msg_id, "timestampMs": bump(300, 6000),
            "channelId": "msteams", "from": dict(bot_ref), "text": bot_text,
        }

        if turn_idx == turns - 1 and not abandons and rng.random() < 0.60:
            fl = {"type": "feedbackLoop"}
            if rng.random() < 0.42:
                positive = rng.random() < agent["positive_bias"]
                fl["value"] = "like" if positive else "dislike"
                comment = rng.choice(FEEDBACK_POSITIVE if positive else FEEDBACK_NEGATIVE)
                if comment:
                    fl["feedbackText"] = comment
            bot_act["channelData"] = {"feedbackLoop": fl}

        # Abandoned conversations get no bot reply at all - that shape is what the
        # parser heuristic reads as "Abandoned".
        if not abandons:
            acts.append(bot_act)

        if turn_idx == 0:
            acts.append({
                "type": "trace", "valueType": "VariableAssignment", "timestampMs": bump(50, 400),
                "value": {"name": "ESS_UserContext_UPN",
                          "newValue": user["userPrincipalName"] if not anonymous else "anonymous"},
            })
            acts.append({
                "type": "trace", "valueType": "VariableAssignment", "timestampMs": bump(50, 400),
                "value": {"name": "Topic", "newValue": topic},
            })
            if rng.random() < 0.4:
                acts.append({
                    "type": "trace", "valueType": "VariableAssignment", "timestampMs": bump(50, 400),
                    "value": {"name": "ESS_UserContext_Department", "newValue": user["department"]},
                })

    # Escalation is modelled as a hand-off to a connected agent, which is exactly what
    # the parser heuristic treats as "Escalated". Orchestrator agents hand off to a
    # specialist; everyone else hands off to the human service desk.
    connected = []
    if escalates:
        pool = SUB_AGENT_TARGETS if agent.get("orchestrator") else ["cr9a2_humanServiceDesk"]
        pool = [t for t in pool if t != agent["schema"]] or ["cr9a2_humanServiceDesk"]
        n_targets = rng.randint(1, 2) if agent.get("orchestrator") and len(pool) > 1 else 1
        for step, target in enumerate(rng.sample(pool, n_targets), start=1):
            connected.append(target)
            uid = user["id"] if not anonymous else None
            acts.append({
                "type": "trace", "valueType": "ConnectedAgentInitializeTraceData", "timestampMs": bump(200, 1500),
                "value": {"parentBotSchemaName": agent["schema"], "connectedAgentBotSchemaName": target,
                          "planStepId": "step-" + str(step), "userId": uid},
            })
            acts.append({
                "type": "trace", "valueType": "ConnectedAgentCompletedTraceData", "timestampMs": bump(2000, 15000),
                "value": {"parentBotSchemaName": agent["schema"], "connectedAgentBotSchemaName": target,
                          "planStepId": "step-" + str(step), "userId": uid},
            })

    reason = {
        "Resolved": rng.choice(["TopicCompleted", "UserConfirmedResolved"]),
        "Escalated": rng.choice(["EscalatedToAgent", "TransferredToHuman"]),
        "Abandoned": rng.choice(["UserAbandoned", "NoUserResponse", "IntentNotRecognised"]),
    }[outcome]
    acts.append({
        "type": "trace", "valueType": "SessionInfo", "timestampMs": bump(500, 4000),
        "value": {"outcome": outcome, "outcomeReason": reason,
                  "sessionType": "Escalated" if outcome == "Escalated" else "Standard"},
    })

    return {"activities": acts}, topic, outcome, connected


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Agent Evaluator demo data")
    ap.add_argument("--conversations", type=int, default=2400)
    ap.add_argument("--users", type=int, default=420)
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--end-date", type=str, default=None,
                    help="Last day of the window (YYYY-MM-DD). Default: today (UTC).")
    args = ap.parse_args()

    rng = random.Random(args.seed)

    end = (datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
           if args.end_date else datetime.now(timezone.utc).replace(microsecond=0))
    start = (end - timedelta(days=args.days)).replace(hour=0, minute=0, second=0, microsecond=0)

    users = build_users(rng, args.users)
    power_users = rng.sample(users, max(1, len(users) // 5))

    rows = []
    for _ in range(args.conversations):
        agent = weighted_choice(rng, AGENTS, "share")
        user = rng.choice(power_users) if rng.random() < 0.45 else rng.choice(users)
        started = business_timestamp(rng, start, args.days)
        content, topic, outcome, _connected = build_conversation(rng, agent, user, started)
        rows.append({
            "conversationtranscriptid": stable_guid(rng),
            "content": json.dumps(content, separators=(",", ":")),
            "conversationstarttime": started.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "schemaversion": "1.0",
            "schematype": "Conversation",
            "name": agent["name"] + " - " + topic,
            "metadata": "{}",
            "statecode": 0,
            "statuscode": 1,
            "createdon": started.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "bot_conversationtranscriptid.schemaname": agent["schema"],
            "agent_schema_hint": agent["schema"],
            "bot_name_hint": agent["name"],
            "environment": "https://contoso.crm.dynamics.com",
        })

    rows.sort(key=lambda r: r["conversationstarttime"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    transcripts_path = OUT_DIR / "conversationtranscripts.csv"
    with transcripts_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)

    org_path = OUT_DIR / "copilot_org_data.csv"
    org_cols = ["id", "userPrincipalName", "displayName", "department", "jobTitle",
                "officeLocation", "country", "companyName", "usageLocation", "managerUPN"]
    with org_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=org_cols, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for u in users:
            w.writerow({c: u.get(c, "") for c in org_cols})

    by_agent = {}
    for r in rows:
        by_agent[r["agent_schema_hint"]] = by_agent.get(r["agent_schema_hint"], 0) + 1

    print("Wrote {:<32} {:>6,} conversations".format(transcripts_path.name, len(rows)))
    print("Wrote {:<32} {:>6,} users".format(org_path.name, len(users)))
    print("Window: {} -> {}  ({} days, seed {})".format(start.date(), end.date(), args.days, args.seed))
    print("\nConversations per agent:")
    for schema, count in sorted(by_agent.items(), key=lambda kv: -kv[1]):
        name = next(a["name"] for a in AGENTS if a["schema"] == schema)
        print("  {:<26} {:>6,}".format(name, count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
