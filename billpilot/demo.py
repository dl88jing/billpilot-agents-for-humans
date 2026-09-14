"""End-to-end BillPilot demo — works offline with no AWS credentials."""

from __future__ import annotations

import json

from billpilot.agent import run_offline_pipeline


def main() -> None:
    print("=" * 64)
    print("BillPilot — Everyday Agents demo (offline / no AWS keys)")
    print("Strands Agents SDK tools drive intake → anomaly gate → action")
    print("=" * 64)

    outcome = run_offline_pipeline()
    print("\n[1] Tools available:")
    for name in outcome["strands_tools"]:
        print(f"  - {name}")

    print("\n[2] Per-bill decisions:")
    for item in outcome["results"]:
        print(f"  - {item['bill_id']}: {item['action']}")
        anomalies = item["detail"].get("anomalies") or []
        for a in anomalies:
            print(f"      anomaly: {a}")

    state = outcome["state"]
    print("\n[3] Quiet auto-handled:")
    for bill_id in state.get("handled", []):
        print(f"  - {bill_id}")

    print("\n[4] Human decision gate (only when needed):")
    for note in state.get("notifications", []):
        print(f"  - {note['bill_id']}: {note['reason']}")
        print(f"    recommended: {note['recommended_action']}")

    print("\n[5] Payment prep queue:")
    for item in state.get("payment_queue", []):
        print(f"  - {item['payee']} ${item['amount']} due {item['due_date']}")

    print("\nDemo complete. Full state JSON:")
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
