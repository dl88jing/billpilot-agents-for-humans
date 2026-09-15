"""End-to-end BillPilot multi-agent demo — works offline with no AWS credentials."""

from __future__ import annotations

import json

from billpilot.orchestrator import run_pipeline


def main() -> None:
    print("=" * 72)
    print("BillPilot — Multi-Agent Everyday Agents demo (offline / no AWS keys)")
    print("Strands swarm: Intake → Risk → Policy → Treasurer / Comms")
    print("Hash-chained audit ledger + deterministic policy engine")
    print("=" * 72)

    outcome = run_pipeline(reset=True)

    print("\n[1] Strands swarm agents constructed:")
    for role, name in outcome["swarm_agents"].items():
        print(f"  - {role}: {name}")

    print("\n[2] Intake:")
    print(f"  emails processed: {outcome['intake']['emails_processed']}")
    print(f"  calendar dues:    {outcome['intake']['calendar_dues']}")
    print(f"  tools:            {', '.join(outcome['intake']['tools'])}")

    print("\n[3] Risk assessments:")
    print(f"  bills assessed: {outcome['risk']['assessed']}")
    print(f"  tools:          {', '.join(outcome['risk']['tools'])}")

    print("\n[4] Policy decisions (AUTO vs HUMAN_REQUIRED):")
    for d in outcome["decisions"]:
        tag = d["verdict"]
        reasons = "; ".join(d["reasons"]) if d["verdict"] != "AUTO" else "policy_clear"
        scenario = d.get("scenario") or "-"
        print(f"  - {d['bill_id']}: {tag:16}  scenario={scenario}")
        if d["verdict"] != "AUTO":
            print(f"      reasons: {reasons}")

    print("\n[5] Treasurer (AUTO payment prep):")
    qs = outcome["treasurer"]["queue_summary"]
    print(f"  queued: {qs.get('count', 0)}  total_usd: {qs.get('total_usd', 0)}")
    for action in outcome["treasurer"]["actions"]:
        rem = action.get("funding", {}).get("remaining_after")
        print(f"  - {action['bill_id']}: queued={action['queued']} remaining_after={rem}")

    print("\n[6] Comms:")
    print(f"  quiet auto-handled: {outcome['comms']['auto_handled']}")
    print("  human decision gate:")
    for note in outcome["comms"]["notifications"]:
        print(f"  - {note.get('bill_id')}: {note.get('reason')}")
        print(f"    recommended: {note.get('recommended_action')}")

    print("\n[7] Audit ledger verification:")
    ledger = outcome["ledger"]
    print(f"  status: {ledger['status']}  events: {ledger['events']}")
    print(f"  by_type: {json.dumps(ledger.get('by_type', {}), indent=2)}")
    print(f"  message: {ledger.get('message')}")

    print("\nDemo complete.")
    if ledger.get("status") != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
