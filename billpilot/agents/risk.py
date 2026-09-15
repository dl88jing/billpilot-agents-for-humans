"""Risk agent — anomaly + duplicate analysis."""

from __future__ import annotations

import json
from typing import Any

from billpilot.agents._common import build_strands_agent
from billpilot.tools.anomaly import check_anomaly, detect_duplicates

RISK_TOOLS = [check_anomaly, detect_duplicates]

SYSTEM_PROMPT = """You are BillPilot Risk. Score each bill for surprises:
unexpected amounts, duplicate charges, and suspicious scenarios.
Return structured anomaly lists. Do not notify humans or queue payments —
Policy + Treasurer/Comms handle that.
"""


def build_risk_agent(use_bedrock: bool | None = None):
    return build_strands_agent(
        name="Risk",
        system_prompt=SYSTEM_PROMPT,
        tools=RISK_TOOLS,
        use_bedrock=use_bedrock,
    )


def run_risk_offline(bills: list[dict[str, Any]]) -> dict[str, Any]:
    """Run anomaly + duplicate tools for each bill."""
    assessments: list[dict[str, Any]] = []
    for bill in bills:
        bill_id = bill["id"]
        anomaly = json.loads(check_anomaly(bill_id))
        dup = json.loads(detect_duplicates(bill_id))
        combined = list(anomaly.get("anomalies") or []) + list(dup.get("anomalies") or [])
        assessments.append(
            {
                "bill_id": bill_id,
                "payee": bill.get("payee"),
                "amount": bill.get("amount"),
                "scenario": bill.get("scenario"),
                "anomalies": combined,
                "is_duplicate": bool(dup.get("is_duplicate")),
                "anomaly_detail": anomaly,
                "duplicate_detail": dup,
            }
        )
    return {
        "agent": "risk",
        "assessments": assessments,
        "tools_invoked": [t.__name__ for t in RISK_TOOLS],
        "strands_agent": build_risk_agent(use_bedrock=False).name,
    }
