"""Shared mutable demo state under data/runtime/."""

from __future__ import annotations

import json
from typing import Any

from billpilot.paths import STATE_PATH, ensure_runtime


def load_state() -> dict[str, Any]:
    ensure_runtime()
    if STATE_PATH.exists():
        with STATE_PATH.open() as f:
            return json.load(f)
    return {
        "handled": [],
        "needs_decision": [],
        "payment_queue": [],
        "notifications": [],
        "auto_summaries": [],
        "intake": [],
    }


def save_state(state: dict[str, Any]) -> None:
    ensure_runtime()
    with STATE_PATH.open("w") as f:
        json.dump(state, f, indent=2)


def reset_state() -> dict[str, Any]:
    state = {
        "handled": [],
        "needs_decision": [],
        "payment_queue": [],
        "notifications": [],
        "auto_summaries": [],
        "intake": [],
    }
    save_state(state)
    return state
