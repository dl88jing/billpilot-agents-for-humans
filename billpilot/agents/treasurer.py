"""Treasurer agent — funding checks + payment prep for AUTO bills."""

from __future__ import annotations

import json
from typing import Any

from billpilot.agents._common import build_strands_agent
from billpilot.tools.funding_accounts import check_funding, list_accounts
from billpilot.tools.payment_prep import queue_payment_prep, summarize_payment_queue

TREASURER_TOOLS = [list_accounts, check_funding, queue_payment_prep, summarize_payment_queue]

SYSTEM_PROMPT = """You are BillPilot Treasurer. For AUTO-approved bills, verify funding
buffer, queue payment prep checklists, and summarize the queue. Never bypass policy.
Never notify humans — that is Comms.
"""


def build_treasurer_agent(use_bedrock: bool | None = None):
    return build_strands_agent(
        name="Treasurer",
        system_prompt=SYSTEM_PROMPT,
        tools=TREASURER_TOOLS,
        use_bedrock=use_bedrock,
    )


def run_treasurer_offline(auto_bills: list[dict[str, Any]]) -> dict[str, Any]:
    accounts = json.loads(list_accounts())
    primary = "checking-primary"
    actions: list[dict[str, Any]] = []
    for bill in auto_bills:
        funding = json.loads(check_funding(float(bill["amount"]), account_id=primary))
        note = f"AUTO via policy; funding remaining≈{funding.get('remaining_after')}"
        queued = json.loads(
            queue_payment_prep(bill["id"], checklist_note=note, funding_account=primary)
        )
        actions.append(
            {
                "bill_id": bill["id"],
                "funding": funding,
                "queued": queued.get("queued", False),
            }
        )
    summary = json.loads(summarize_payment_queue())
    return {
        "agent": "treasurer",
        "accounts": accounts,
        "actions": actions,
        "queue_summary": summary,
        "tools_invoked": [t.__name__ for t in TREASURER_TOOLS],
        "strands_agent": build_treasurer_agent(use_bedrock=False).name,
    }
