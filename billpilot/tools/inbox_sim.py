"""Inbox simulation tools — email → candidate bills."""

from __future__ import annotations

import json
from typing import Any

from strands import tool

from billpilot.paths import BILLS_PATH, INBOX_PATH
from billpilot.tools._state import load_state, save_state
from billpilot.tools.ledger_append import attest_silent


def _load_json(path) -> Any:
    with path.open() as f:
        return json.load(f)


@tool
def list_inbox(status: str = "unread") -> str:
    """List simulated household bill emails from the inbox fixture."""
    emails = _load_json(INBOX_PATH)
    if status != "all":
        emails = [e for e in emails if e.get("status", "unread") == status]
    result = {"count": len(emails), "emails": emails}
    attest_silent("list_inbox", {"count": result["count"], "status": status}, actor="intake")
    return json.dumps(result, indent=2)


@tool
def parse_email_bill(email_id: str) -> str:
    """Parse an inbox email into a normalized bill candidate linked to sample_bills."""
    emails = {e["id"]: e for e in _load_json(INBOX_PATH)}
    email = emails.get(email_id)
    if not email:
        result = {"error": f"Unknown email_id {email_id}"}
        attest_silent("parse_email_bill", result, actor="intake")
        return json.dumps(result)

    bills = {b["id"]: b for b in _load_json(BILLS_PATH)}
    bill_id = email.get("linked_bill_id")
    bill = bills.get(bill_id, {})
    candidate = {
        "email_id": email_id,
        "from": email.get("from"),
        "subject": email.get("subject"),
        "received_at": email.get("received_at"),
        "bill_id": bill_id,
        "payee": bill.get("payee") or email.get("payee_hint"),
        "amount": bill.get("amount") or email.get("amount_hint"),
        "due_date": bill.get("due_date") or email.get("due_hint"),
        "category": bill.get("category", "unknown"),
        "scenario": email.get("scenario"),
        "raw_snippet": email.get("body_snippet", ""),
    }
    state = load_state()
    state.setdefault("intake", []).append(candidate)
    save_state(state)
    attest_silent("parse_email_bill", {"email_id": email_id, "bill_id": bill_id}, actor="intake")
    return json.dumps(candidate, indent=2)
