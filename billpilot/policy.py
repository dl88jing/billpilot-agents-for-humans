"""Deterministic policy engine — AUTO vs HUMAN_REQUIRED decisions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from billpilot.paths import DEFAULT_POLICY_PATH


@dataclass
class PolicyConfig:
    version: str = "1.0"
    name: str = "default"
    auto_pay_max_usd: float = 200.0
    trusted_payees: list[str] = field(default_factory=list)
    require_human_on_new_payee: bool = True
    duplicate_window_days: int = 14
    min_funding_buffer: float = 150.0
    amount_surprise_pct: float = 0.25
    always_escalate_categories: list[str] = field(default_factory=list)


@dataclass
class PolicyDecision:
    verdict: str  # AUTO | HUMAN_REQUIRED
    reasons: list[str]
    recommended_action: str
    bill_id: str
    policy_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "reasons": self.reasons,
            "recommended_action": self.recommended_action,
            "bill_id": self.bill_id,
            "policy_name": self.policy_name,
        }


def load_policy(path: Path | None = None) -> PolicyConfig:
    path = path or DEFAULT_POLICY_PATH
    with path.open() as f:
        raw = yaml.safe_load(f) or {}
    return PolicyConfig(
        version=str(raw.get("version", "1.0")),
        name=str(raw.get("name", "default")),
        auto_pay_max_usd=float(raw.get("auto_pay_max_usd", 200.0)),
        trusted_payees=list(raw.get("trusted_payees") or []),
        require_human_on_new_payee=bool(raw.get("require_human_on_new_payee", True)),
        duplicate_window_days=int(raw.get("duplicate_window_days", 14)),
        min_funding_buffer=float(raw.get("min_funding_buffer", 150.0)),
        amount_surprise_pct=float(raw.get("amount_surprise_pct", 0.25)),
        always_escalate_categories=list(raw.get("always_escalate_categories") or []),
    )


def _parse_date(value: str) -> datetime | None:
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def evaluate_bill(
    bill: dict[str, Any],
    *,
    anomalies: list[str] | None = None,
    funding_available: float | None = None,
    known_payees: list[str] | None = None,
    policy: PolicyConfig | None = None,
) -> PolicyDecision:
    """Apply deterministic rules; agents propose, policy decides."""
    policy = policy or load_policy()
    anomalies = anomalies or []
    known = set(known_payees or policy.trusted_payees)
    reasons: list[str] = []

    bill_id = str(bill.get("id", "unknown"))
    payee = str(bill.get("payee", ""))
    amount = float(bill.get("amount", 0))
    category = str(bill.get("category", ""))

    if category in policy.always_escalate_categories:
        reasons.append(f"category_always_escalate:{category}")

    if policy.require_human_on_new_payee and payee not in known:
        reasons.append(f"new_payee:{payee}")

    if amount > policy.auto_pay_max_usd:
        reasons.append(f"over_auto_pay_max:{amount}>{policy.auto_pay_max_usd}")

    low_high = bill.get("expected_amount_range")
    if isinstance(low_high, list) and len(low_high) == 2:
        low, high = float(low_high[0]), float(low_high[1])
        if amount < low or amount > high:
            reasons.append(f"amount_outside_expected:{amount} not in [{low},{high}]")
        elif high > 0 and (amount - high) / high > policy.amount_surprise_pct:
            reasons.append(f"amount_surprise_pct:{(amount - high) / high:.2%}")

    for a in anomalies:
        if a not in reasons:
            reasons.append(a)

    if funding_available is not None:
        remaining = funding_available - amount
        if remaining < policy.min_funding_buffer:
            reasons.append(
                f"low_funding_buffer:available={funding_available} "
                f"after_pay={remaining:.2f} < min={policy.min_funding_buffer}"
            )

    if reasons:
        return PolicyDecision(
            verdict="HUMAN_REQUIRED",
            reasons=reasons,
            recommended_action=(
                "Review flagged bill before payment; approve, adjust amount, "
                "or dismiss duplicate/new payee."
            ),
            bill_id=bill_id,
            policy_name=policy.name,
        )

    return PolicyDecision(
        verdict="AUTO",
        reasons=["policy_clear"],
        recommended_action="Queue payment prep and mark auto-handled.",
        bill_id=bill_id,
        policy_name=policy.name,
    )


def decide_from_json(
    bill_json: str,
    anomaly_json: str = "[]",
    funding_available: float | None = None,
) -> str:
    bill = json.loads(bill_json) if isinstance(bill_json, str) else bill_json
    anomalies = json.loads(anomaly_json) if isinstance(anomaly_json, str) else anomaly_json
    decision = evaluate_bill(
        bill,
        anomalies=anomalies if isinstance(anomalies, list) else anomalies.get("anomalies", []),
        funding_available=funding_available,
    )
    return json.dumps(decision.to_dict(), indent=2)
