"""Funding account balance tools."""

from __future__ import annotations

import json

from strands import tool

from billpilot.paths import ACCOUNTS_PATH
from billpilot.tools.ledger_append import attest_silent


@tool
def list_accounts() -> str:
    """List household funding accounts and available balances."""
    with ACCOUNTS_PATH.open() as f:
        accounts = json.load(f)
    result = {"count": len(accounts), "accounts": accounts}
    attest_silent("list_accounts", {"count": result["count"]}, actor="treasurer")
    return json.dumps(result, indent=2)


@tool
def check_funding(amount_usd: float, account_id: str = "checking-primary") -> str:
    """Check whether an account can fund a payment while respecting the buffer policy."""
    with ACCOUNTS_PATH.open() as f:
        accounts = {a["id"]: a for a in json.load(f)}
    acct = accounts.get(account_id)
    if not acct:
        result = {"error": f"Unknown account_id {account_id}"}
        attest_silent("check_funding", result, actor="treasurer")
        return json.dumps(result)
    available = float(acct["available_balance"])
    remaining = available - float(amount_usd)
    result = {
        "account_id": account_id,
        "available_balance": available,
        "requested_amount": float(amount_usd),
        "remaining_after": remaining,
        "sufficient_for_amount": available >= float(amount_usd),
        "currency": acct.get("currency", "USD"),
        "scenario": acct.get("scenario"),
    }
    attest_silent(
        "check_funding",
        {
            "account_id": account_id,
            "amount": amount_usd,
            "sufficient": result["sufficient_for_amount"],
            "remaining_after": remaining,
        },
        actor="treasurer",
    )
    return json.dumps(result, indent=2)
