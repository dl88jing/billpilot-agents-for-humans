"""CLI: python -m billpilot.verify_ledger — prints PASS with event counts."""

from __future__ import annotations

import json

from billpilot.ledger import verify_ledger


def main() -> None:
    result = verify_ledger()
    print("=" * 48)
    print("BillPilot ledger verification")
    print("=" * 48)
    print(f"status:  {result['status']}")
    print(f"events:  {result['events']}")
    print(f"by_type: {json.dumps(result.get('by_type', {}), indent=2)}")
    print(f"message: {result.get('message')}")
    if not result.get("ok"):
        raise SystemExit(1)
    print("PASS")


if __name__ == "__main__":
    main()
