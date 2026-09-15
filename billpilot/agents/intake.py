"""Intake agent — email inbox + calendar dues → candidate bills."""

from __future__ import annotations

import json
from typing import Any

from billpilot.agents._common import build_strands_agent
from billpilot.paths import BILLS_PATH, HOUSEHOLD_PATH
from billpilot.tools.calendar_dues import list_calendar_dues, match_bill_to_calendar
from billpilot.tools.inbox_sim import list_inbox, parse_email_bill

INTAKE_TOOLS = [list_inbox, parse_email_bill, list_calendar_dues, match_bill_to_calendar]

SYSTEM_PROMPT = """You are BillPilot Intake, a specialized Everyday Agent.
Collect household bill candidates from email and calendar. Normalize payee,
amount, due date, and scenario tags. Do not pay anything — hand off structured
candidates to Risk. Use tools; stay quiet except for structured outputs.
"""


def build_intake_agent(use_bedrock: bool | None = None):
    return build_strands_agent(
        name="Intake",
        system_prompt=SYSTEM_PROMPT,
        tools=INTAKE_TOOLS,
        use_bedrock=use_bedrock,
    )


def run_intake_offline() -> dict[str, Any]:
    """Deterministic intake that still CALLS Strands @tools."""
    inbox_raw = list_inbox(status="unread")
    inbox = json.loads(inbox_raw)
    candidates: list[dict[str, Any]] = []
    for email in inbox.get("emails", []):
        parsed = json.loads(parse_email_bill(email["id"]))
        if parsed.get("bill_id"):
            match_bill_to_calendar(parsed["bill_id"])
        candidates.append(parsed)

    dues = json.loads(list_calendar_dues(days_ahead=21))
    with BILLS_PATH.open() as f:
        bills = json.load(f)
    with HOUSEHOLD_PATH.open() as f:
        household = json.load(f)

    return {
        "agent": "intake",
        "household": household.get("name"),
        "emails_processed": len(candidates),
        "candidates": candidates,
        "calendar_dues": dues.get("dues", []),
        "bills": bills,
        "tools_invoked": [t.__name__ for t in INTAKE_TOOLS],
        "strands_agent": build_intake_agent(use_bedrock=False).name,
    }
