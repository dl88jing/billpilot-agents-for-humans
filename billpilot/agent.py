"""BillPilot Strands agent — Bedrock when available, offline pipeline otherwise."""

from __future__ import annotations

import json
import os
from typing import Any

from billpilot.tools import (
    check_anomaly,
    list_bills,
    mark_auto_handled,
    notify_human,
    parse_bill,
    queue_payment_prep,
    _load_bills,
    _load_state,
    _save_state,
    RUNTIME_DIR,
)

TOOLS = [
    list_bills,
    parse_bill,
    check_anomaly,
    queue_payment_prep,
    notify_human,
    mark_auto_handled,
]

SYSTEM_PROMPT = """You are BillPilot, an Everyday Agent for household bills.
Your job is to handle repetitive bill busywork end-to-end and only surface
the human when a real decision is required (unexpected amount, duplicate charge,
missing funds, ambiguous payee).

Workflow for each due bill:
1) list_bills / parse_bill
2) check_anomaly
3) If safe_to_auto_handle: queue_payment_prep then mark_auto_handled
4) If needs_human_decision: notify_human with a clear reason and recommended action
Stay quiet otherwise. Be concrete and tool-driven — do not only chat.
"""


def build_agent(use_bedrock: bool | None = None):
    """Build a Strands Agent. Uses Bedrock when credentials exist unless forced off."""
    from strands import Agent

    if use_bedrock is None:
        use_bedrock = bool(
            os.getenv("AWS_ACCESS_KEY_ID")
            or os.getenv("AWS_PROFILE")
            or os.getenv("AWS_BEARER_TOKEN_BEDROCK")
        )

    if use_bedrock:
        try:
            from strands.models import BedrockModel

            model = BedrockModel(
                model_id=os.getenv(
                    "BILLPILOT_MODEL_ID",
                    "global.anthropic.claude-sonnet-4-6",
                ),
                region_name=os.getenv("AWS_REGION", "us-west-2"),
                temperature=0.2,
            )
            return Agent(model=model, tools=TOOLS, system_prompt=SYSTEM_PROMPT)
        except Exception as exc:  # pragma: no cover - environment dependent
            print(f"[billpilot] Bedrock unavailable ({exc}); falling back to offline pipeline")

    return None


def run_offline_pipeline() -> dict[str, Any]:
    """Deterministic offline agent loop using the same tools (no LLM keys required)."""
    # Reset runtime state for a clean demo
    if RUNTIME_DIR.exists():
        for path in RUNTIME_DIR.glob("*"):
            path.unlink()
    _save_state({"handled": [], "needs_decision": [], "payment_queue": [], "notifications": []})

    raw = list_bills(status="due")
    payload = json.loads(raw)
    results: list[dict[str, Any]] = []

    for bill in payload["bills"]:
        bill_id = bill["id"]
        parse_bill(bill_id)
        anomaly = json.loads(check_anomaly(bill_id))
        if anomaly.get("needs_human_decision"):
            reason = "; ".join(anomaly.get("anomalies", [])) or "needs review"
            notify_human(
                bill_id,
                reason=reason,
                recommended_action="Review amount/duplicate before paying; approve or dismiss.",
            )
            results.append({"bill_id": bill_id, "action": "notify_human", "detail": anomaly})
        else:
            queue_payment_prep(bill_id, checklist_note="Routine bill within expected range")
            mark_auto_handled(
                bill_id,
                summary=f"Auto-prepared payment for {bill['payee']} (${bill['amount']}) due {bill['due_date']}",
            )
            results.append({"bill_id": bill_id, "action": "auto_handled", "detail": anomaly})

    state = _load_state()
    return {
        "mode": "offline_fixture_pipeline",
        "bills_processed": len(results),
        "results": results,
        "state": state,
        "strands_tools": [t.__name__ for t in TOOLS],
    }


def run_with_strands_agent(prompt: str | None = None) -> Any:
    """Run via Strands Agent when Bedrock/credentials are configured."""
    agent = build_agent(use_bedrock=True)
    if agent is None:
        return run_offline_pipeline()
    user_prompt = prompt or (
        "Process all due household bills. Auto-handle safe ones. "
        "Notify me only for anomalies (unexpected amount or duplicates)."
    )
    return agent(user_prompt)
