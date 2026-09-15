"""Payment preparation tools for the treasurer agent."""

from __future__ import annotations

import json

from strands import tool

from billpilot.paths import BILLS_PATH
from billpilot.tools._state import load_state, save_state
from billpilot.tools.ledger_append import attest_silent


@tool
def queue_payment_prep(bill_id: str, checklist_note: str = "", funding_account: str = "checking-primary") -> str:
    """Queue payment preparation steps for a bill approved for AUTO handling."""
    with BILLS_PATH.open() as f:
        bills = {b["id"]: b for b in json.load(f)}
    bill = bills.get(bill_id)
    if not bill:
        result = {"error": f"Unknown bill_id {bill_id}"}
        attest_silent("queue_payment_prep", result, actor="treasurer")
        return json.dumps(result)

    state = load_state()
    item = {
        "bill_id": bill_id,
        "payee": bill["payee"],
        "amount": bill["amount"],
        "due_date": bill["due_date"],
        "funding_account": funding_account,
        "checklist": [
            "Confirm payee and account_last4",
            "Verify available balance / funding source",
            "Schedule payment on or before due_date",
            "Record confirmation number after payment",
            "Append attestation to audit ledger",
        ],
        "note": checklist_note,
        "status": "queued",
    }
    state.setdefault("payment_queue", []).append(item)
    save_state(state)
    result = {"queued": True, "item": item}
    attest_silent(
        "queue_payment_prep",
        {"bill_id": bill_id, "amount": bill["amount"], "payee": bill["payee"]},
        actor="treasurer",
    )
    return json.dumps(result, indent=2)


@tool
def summarize_payment_queue() -> str:
    """Summarize the current payment preparation queue."""
    state = load_state()
    queue = state.get("payment_queue", [])
    total = sum(float(i.get("amount", 0)) for i in queue)
    result = {"count": len(queue), "total_usd": total, "queue": queue}
    attest_silent("summarize_payment_queue", {"count": len(queue), "total_usd": total}, actor="treasurer")
    return json.dumps(result, indent=2)
