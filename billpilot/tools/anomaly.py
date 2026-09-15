"""Anomaly and duplicate detection tools."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from strands import tool

from billpilot.paths import BILLS_PATH
from billpilot.policy import load_policy
from billpilot.tools.ledger_append import attest_silent


def _load_bills() -> list[dict[str, Any]]:
    with BILLS_PATH.open() as f:
        return json.load(f)


def _parse_date(value: str) -> datetime | None:
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


@tool
def check_anomaly(bill_id: str) -> str:
    """Detect amount surprises and other anomalies for a bill."""
    bills = _load_bills()
    by_id = {b["id"]: b for b in bills}
    bill = by_id.get(bill_id)
    if not bill:
        result = {"error": f"Unknown bill_id {bill_id}"}
        attest_silent("check_anomaly", result, actor="risk")
        return json.dumps(result)

    anomalies: list[str] = []
    low, high = bill.get("expected_amount_range", [bill["amount"], bill["amount"]])
    if bill["amount"] < low or bill["amount"] > high:
        anomalies.append(
            f"amount_unexpected: {bill['amount']} outside expected [{low}, {high}]"
        )

    if bill.get("scenario") == "surprise_subscription":
        anomalies.append("surprise_subscription: plan/amount changed vs household baseline")

    result = {
        "bill_id": bill_id,
        "payee": bill["payee"],
        "amount": bill["amount"],
        "anomalies": anomalies,
        "needs_human_decision": len(anomalies) > 0,
        "safe_to_auto_handle": len(anomalies) == 0,
    }
    attest_silent(
        "check_anomaly",
        {"bill_id": bill_id, "anomaly_count": len(anomalies)},
        actor="risk",
    )
    return json.dumps(result, indent=2)


@tool
def detect_duplicates(bill_id: str) -> str:
    """Detect duplicate charges for the same payee within the policy window."""
    policy = load_policy()
    bills = _load_bills()
    by_id = {b["id"]: b for b in bills}
    bill = by_id.get(bill_id)
    if not bill:
        result = {"error": f"Unknown bill_id {bill_id}"}
        attest_silent("detect_duplicates", result, actor="risk")
        return json.dumps(result)

    due = _parse_date(bill.get("due_date", ""))
    duplicates: list[dict[str, Any]] = []
    for other in bills:
        if other["id"] == bill_id:
            continue
        if other["payee"] != bill["payee"]:
            continue
        if other["amount"] != bill["amount"]:
            continue
        other_due = _parse_date(other.get("due_date", ""))
        if due and other_due:
            delta = abs((due - other_due).days)
            if delta <= policy.duplicate_window_days:
                duplicates.append(
                    {
                        "other_bill_id": other["id"],
                        "days_apart": delta,
                        "amount": other["amount"],
                        "due_date": other["due_date"],
                    }
                )
        elif other.get("due_date") == bill.get("due_date"):
            duplicates.append(
                {
                    "other_bill_id": other["id"],
                    "days_apart": 0,
                    "amount": other["amount"],
                    "due_date": other["due_date"],
                }
            )

    result = {
        "bill_id": bill_id,
        "duplicate_window_days": policy.duplicate_window_days,
        "duplicates": duplicates,
        "is_duplicate": len(duplicates) > 0,
        "anomalies": (
            [f"duplicate_charge: mirrors {', '.join(d['other_bill_id'] for d in duplicates)}"]
            if duplicates
            else []
        ),
    }
    attest_silent(
        "detect_duplicates",
        {"bill_id": bill_id, "duplicate_count": len(duplicates)},
        actor="risk",
    )
    return json.dumps(result, indent=2)
