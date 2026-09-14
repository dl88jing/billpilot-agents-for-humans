"""Strands tools for BillPilot bill intake, anomaly checks, and decision gates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strands import tool

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BILLS_PATH = DATA_DIR / "sample_bills.json"
RUNTIME_DIR = DATA_DIR / "runtime"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
STATE_PATH = RUNTIME_DIR / "state.json"


def _load_bills() -> list[dict[str, Any]]:
    with BILLS_PATH.open() as f:
        return json.load(f)


def _load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        with STATE_PATH.open() as f:
            return json.load(f)
    return {"handled": [], "needs_decision": [], "payment_queue": [], "notifications": []}


def _save_state(state: dict[str, Any]) -> None:
    with STATE_PATH.open("w") as f:
        json.dump(state, f, indent=2)


@tool
def list_bills(status: str = "due") -> str:
    """List household bills filtered by status (due, all, handled)."""
    bills = _load_bills()
    state = _load_state()
    handled = set(state.get("handled", []))
    if status == "all":
        selected = bills
    elif status == "handled":
        selected = [b for b in bills if b["id"] in handled]
    else:
        selected = [b for b in bills if b.get("status") == "due" and b["id"] not in handled]
    return json.dumps({"count": len(selected), "bills": selected}, indent=2)


@tool
def parse_bill(bill_id: str) -> str:
    """Parse a single bill into a normalized summary for agent reasoning."""
    bills = {b["id"]: b for b in _load_bills()}
    bill = bills.get(bill_id)
    if not bill:
        return json.dumps({"error": f"Unknown bill_id {bill_id}"})
    low, high = bill.get("expected_amount_range", [bill["amount"], bill["amount"]])
    summary = {
        "id": bill["id"],
        "payee": bill["payee"],
        "amount": bill["amount"],
        "due_date": bill["due_date"],
        "category": bill["category"],
        "autopay": bill.get("autopay", False),
        "expected_low": low,
        "expected_high": high,
        "notes": bill.get("notes", ""),
    }
    return json.dumps(summary, indent=2)


@tool
def check_anomaly(bill_id: str) -> str:
    """Detect anomalies: amount outside expected range, or duplicate payee/amount/due_date."""
    bills = _load_bills()
    by_id = {b["id"]: b for b in bills}
    bill = by_id.get(bill_id)
    if not bill:
        return json.dumps({"error": f"Unknown bill_id {bill_id}"})

    anomalies: list[str] = []
    low, high = bill.get("expected_amount_range", [bill["amount"], bill["amount"]])
    if bill["amount"] < low or bill["amount"] > high:
        anomalies.append(
            f"amount_unexpected: {bill['amount']} outside expected [{low}, {high}]"
        )

    duplicates = [
        other["id"]
        for other in bills
        if other["id"] != bill_id
        and other["payee"] == bill["payee"]
        and other["amount"] == bill["amount"]
        and other["due_date"] == bill["due_date"]
    ]
    if duplicates:
        anomalies.append(f"duplicate_charge: mirrors {', '.join(duplicates)}")

    needs_human = len(anomalies) > 0
    return json.dumps(
        {
            "bill_id": bill_id,
            "anomalies": anomalies,
            "needs_human_decision": needs_human,
            "safe_to_auto_handle": not needs_human,
        },
        indent=2,
    )


@tool
def queue_payment_prep(bill_id: str, checklist_note: str = "") -> str:
    """Queue payment preparation steps for a bill that is safe to auto-handle."""
    bills = {b["id"]: b for b in _load_bills()}
    bill = bills.get(bill_id)
    if not bill:
        return json.dumps({"error": f"Unknown bill_id {bill_id}"})
    state = _load_state()
    item = {
        "bill_id": bill_id,
        "payee": bill["payee"],
        "amount": bill["amount"],
        "due_date": bill["due_date"],
        "checklist": [
            "Confirm payee and account_last4",
            "Verify available balance / funding source",
            "Schedule payment on or before due_date",
            "Record confirmation number after payment",
        ],
        "note": checklist_note,
    }
    state.setdefault("payment_queue", []).append(item)
    _save_state(state)
    return json.dumps({"queued": True, "item": item}, indent=2)


@tool
def notify_human(bill_id: str, reason: str, recommended_action: str) -> str:
    """Ping the human only when a real decision is required."""
    state = _load_state()
    note = {
        "bill_id": bill_id,
        "reason": reason,
        "recommended_action": recommended_action,
        "channel": "decision_gate",
    }
    state.setdefault("notifications", []).append(note)
    state.setdefault("needs_decision", []).append(bill_id)
    _save_state(state)
    return json.dumps({"notified": True, "notification": note}, indent=2)


@tool
def mark_auto_handled(bill_id: str, summary: str) -> str:
    """Mark a routine bill as quietly handled with no human ping."""
    state = _load_state()
    if bill_id not in state.setdefault("handled", []):
        state["handled"].append(bill_id)
    state.setdefault("auto_summaries", []).append({"bill_id": bill_id, "summary": summary})
    _save_state(state)
    return json.dumps({"handled": True, "bill_id": bill_id, "summary": summary}, indent=2)
