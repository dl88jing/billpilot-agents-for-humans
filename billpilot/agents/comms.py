"""Comms agent — quiet auto-handle records + human decision-gate pings."""

from __future__ import annotations

import json
from typing import Any

from billpilot.agents._common import build_strands_agent
from billpilot.tools.notify import mark_auto_handled, notify_human

COMMS_TOOLS = [notify_human, mark_auto_handled]

SYSTEM_PROMPT = """You are BillPilot Comms. Stay quiet by default.
Only notify_human when policy verdict is HUMAN_REQUIRED.
For AUTO bills, mark_auto_handled with a concise summary. Never invent payments.
"""


def build_comms_agent(use_bedrock: bool | None = None):
    return build_strands_agent(
        name="Comms",
        system_prompt=SYSTEM_PROMPT,
        tools=COMMS_TOOLS,
        use_bedrock=use_bedrock,
    )


def run_comms_offline(
    auto_bills: list[dict[str, Any]],
    human_required: list[dict[str, Any]],
) -> dict[str, Any]:
    handled: list[dict[str, Any]] = []
    notifications: list[dict[str, Any]] = []

    for bill in auto_bills:
        summary = (
            f"Auto-prepared payment for {bill['payee']} "
            f"(${bill['amount']}) due {bill['due_date']}"
        )
        result = json.loads(mark_auto_handled(bill["id"], summary=summary))
        handled.append(result)

    for item in human_required:
        bill = item["bill"]
        decision = item["decision"]
        reason = "; ".join(decision.get("reasons") or ["needs review"])
        result = json.loads(
            notify_human(
                bill["id"],
                reason=reason,
                recommended_action=decision.get(
                    "recommended_action",
                    "Review before paying.",
                ),
            )
        )
        notifications.append(result)

    return {
        "agent": "comms",
        "auto_handled": handled,
        "notifications": notifications,
        "tools_invoked": [t.__name__ for t in COMMS_TOOLS],
        "strands_agent": build_comms_agent(use_bedrock=False).name,
    }
