"""Calendar due-date tools."""

from __future__ import annotations

import json

from strands import tool

from billpilot.paths import CALENDAR_PATH
from billpilot.tools.ledger_append import attest_silent


@tool
def list_calendar_dues(days_ahead: int = 14) -> str:
    """List upcoming bill-related calendar dues within the next N days."""
    with CALENDAR_PATH.open() as f:
        events = json.load(f)
    # Fixture already scoped; days_ahead kept for API realism
    selected = [e for e in events if e.get("type") == "bill_due"][: max(days_ahead, 1)]
    result = {"count": len(selected), "dues": selected, "days_ahead": days_ahead}
    attest_silent("list_calendar_dues", {"count": result["count"]}, actor="intake")
    return json.dumps(result, indent=2)


@tool
def match_bill_to_calendar(bill_id: str) -> str:
    """Match a bill id to a calendar due event if present."""
    with CALENDAR_PATH.open() as f:
        events = json.load(f)
    matches = [e for e in events if e.get("bill_id") == bill_id]
    result = {"bill_id": bill_id, "matched": bool(matches), "events": matches}
    attest_silent("match_bill_to_calendar", result, actor="intake")
    return json.dumps(result, indent=2)
