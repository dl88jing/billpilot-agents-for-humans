"""Human notification and quiet auto-handle tools."""

from __future__ import annotations

import json

from strands import tool

from billpilot.tools._state import load_state, save_state
from billpilot.tools.ledger_append import attest_silent


@tool
def notify_human(bill_id: str, reason: str, recommended_action: str) -> str:
    """Ping the human only when policy requires a real decision."""
    state = load_state()
    note = {
        "bill_id": bill_id,
        "reason": reason,
        "recommended_action": recommended_action,
        "channel": "decision_gate",
    }
    state.setdefault("notifications", []).append(note)
    if bill_id not in state.setdefault("needs_decision", []):
        state["needs_decision"].append(bill_id)
    save_state(state)
    result = {"notified": True, "notification": note}
    attest_silent(
        "notify_human",
        {"bill_id": bill_id, "reason": reason},
        actor="comms",
    )
    return json.dumps(result, indent=2)


@tool
def mark_auto_handled(bill_id: str, summary: str) -> str:
    """Mark a routine bill as quietly handled with no human ping."""
    state = load_state()
    if bill_id not in state.setdefault("handled", []):
        state["handled"].append(bill_id)
    state.setdefault("auto_summaries", []).append({"bill_id": bill_id, "summary": summary})
    save_state(state)
    result = {"handled": True, "bill_id": bill_id, "summary": summary}
    attest_silent("mark_auto_handled", {"bill_id": bill_id}, actor="comms")
    return json.dumps(result, indent=2)
