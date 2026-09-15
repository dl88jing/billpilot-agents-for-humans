"""Orchestrator — intake → risk → policy → treasurer/comms swarm pipeline."""

from __future__ import annotations

import json
from typing import Any

from billpilot.agents.comms import build_comms_agent, run_comms_offline
from billpilot.agents.intake import build_intake_agent, run_intake_offline
from billpilot.agents.risk import build_risk_agent, run_risk_offline
from billpilot.agents.treasurer import build_treasurer_agent, run_treasurer_offline
from billpilot.ledger import append_event, reset_ledger, verify_ledger
from billpilot.paths import ACCOUNTS_PATH, HOUSEHOLD_PATH
from billpilot.policy import evaluate_bill, load_policy
from billpilot.tools._state import reset_state


def build_swarm(use_bedrock: bool | None = None) -> dict[str, Any]:
    """Construct the four specialized Strands agents."""
    return {
        "intake": build_intake_agent(use_bedrock=use_bedrock),
        "risk": build_risk_agent(use_bedrock=use_bedrock),
        "treasurer": build_treasurer_agent(use_bedrock=use_bedrock),
        "comms": build_comms_agent(use_bedrock=use_bedrock),
    }


def run_pipeline(reset: bool = True) -> dict[str, Any]:
    """Full offline multi-agent pipeline. Calls real Strands @tools; zero AWS keys."""
    if reset:
        reset_state()
        reset_ledger()

    append_event("pipeline.start", {"mode": "offline_swarm"}, actor="orchestrator")

    # Materialize Strands agents (DemoModel offline / Bedrock when creds exist)
    swarm = build_swarm(use_bedrock=False)
    append_event(
        "swarm.built",
        {"agents": list(swarm.keys()), "model": "DemoModel"},
        actor="orchestrator",
    )

    # 1) Intake
    intake = run_intake_offline()
    append_event(
        "stage.intake",
        {"emails": intake["emails_processed"], "bills": len(intake["bills"])},
        actor="orchestrator",
    )

    bills = intake["bills"]
    policy = load_policy()

    with HOUSEHOLD_PATH.open() as f:
        household = json.load(f)
    known_payees = list(
        set(policy.trusted_payees) | set(household.get("trusted_payees") or [])
    )

    with ACCOUNTS_PATH.open() as f:
        accounts = {a["id"]: a for a in json.load(f)}
    primary_balance = float(accounts.get("checking-primary", {}).get("available_balance", 0))

    # 2) Risk
    risk = run_risk_offline(bills)
    append_event(
        "stage.risk",
        {"assessed": len(risk["assessments"])},
        actor="orchestrator",
    )

    # 3) Policy gate
    auto_bills: list[dict[str, Any]] = []
    human_required: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []

    # Track cumulative funding draw for buffer checks
    remaining_funds = primary_balance
    seen_duplicate_ids: set[str] = set()

    assessment_by_id = {a["bill_id"]: a for a in risk["assessments"]}
    for bill in bills:
        assess = assessment_by_id.get(bill["id"], {})
        # Start from non-duplicate anomalies; duplicates handled with first-wins policy
        anomalies = [
            a
            for a in (assess.get("anomalies") or [])
            if not str(a).startswith("duplicate_charge")
        ]

        # First bill in a duplicate cluster may AUTO; later twins escalate
        if assess.get("is_duplicate"):
            twin_ids = [
                d["other_bill_id"]
                for d in (assess.get("duplicate_detail") or {}).get("duplicates", [])
            ]
            if any(t in seen_duplicate_ids for t in twin_ids):
                anomalies.append(
                    "duplicate_charge: mirrors "
                    + ", ".join(t for t in twin_ids if t in seen_duplicate_ids)
                )

        decision = evaluate_bill(
            bill,
            anomalies=anomalies,
            funding_available=remaining_funds,
            known_payees=known_payees,
            policy=policy,
        )
        d = decision.to_dict()
        d["scenario"] = bill.get("scenario")
        decisions.append(d)
        append_event(
            "policy.decision",
            {"bill_id": bill["id"], "verdict": d["verdict"], "reasons": d["reasons"]},
            actor="policy",
        )

        if decision.verdict == "AUTO":
            auto_bills.append(bill)
            remaining_funds -= float(bill["amount"])
            seen_duplicate_ids.add(bill["id"])
        else:
            human_required.append({"bill": bill, "decision": d})
            seen_duplicate_ids.add(bill["id"])

    # 4a) Treasurer for AUTO
    treasurer = run_treasurer_offline(auto_bills)
    append_event(
        "stage.treasurer",
        {"auto_count": len(auto_bills), "queued": len(treasurer.get("actions", []))},
        actor="orchestrator",
    )

    # 4b) Comms for AUTO quiet-complete + HUMAN pings
    comms = run_comms_offline(auto_bills, human_required)
    append_event(
        "stage.comms",
        {
            "auto_handled": len(comms["auto_handled"]),
            "notifications": len(comms["notifications"]),
        },
        actor="orchestrator",
    )

    ledger_status = verify_ledger()
    append_event(
        "pipeline.complete",
        {
            "auto": len(auto_bills),
            "human_required": len(human_required),
            "ledger_events_before_final": ledger_status["events"],
        },
        actor="orchestrator",
    )
    # Re-verify including pipeline.complete
    ledger_status = verify_ledger()

    return {
        "mode": "multi_agent_offline_swarm",
        "swarm_agents": {k: v.name for k, v in swarm.items()},
        "policy": {"name": policy.name, "version": policy.version},
        "intake": {
            "emails_processed": intake["emails_processed"],
            "calendar_dues": len(intake["calendar_dues"]),
            "tools": intake["tools_invoked"],
        },
        "risk": {
            "assessed": len(risk["assessments"]),
            "tools": risk["tools_invoked"],
        },
        "decisions": decisions,
        "treasurer": {
            "actions": treasurer["actions"],
            "queue_summary": treasurer["queue_summary"],
            "tools": treasurer["tools_invoked"],
        },
        "comms": {
            "auto_handled": [h.get("bill_id") for h in comms["auto_handled"]],
            "notifications": [
                n.get("notification", {}) for n in comms["notifications"]
            ],
            "tools": comms["tools_invoked"],
        },
        "ledger": ledger_status,
        "strands_agents_constructed": True,
    }
