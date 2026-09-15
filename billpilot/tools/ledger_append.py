"""Tools that write attested events into the hash-chained ledger."""

from __future__ import annotations

import json
from typing import Any

from strands import tool

from billpilot.ledger import append_event, load_events


def _attest(tool_name: str, result: dict[str, Any], actor: str) -> dict[str, Any]:
    record = append_event(
        event_type=f"tool.{tool_name}",
        payload={"tool": tool_name, "result": result},
        actor=actor,
    )
    return record


@tool
def attest_tool_call(tool_name: str, result_json: str, actor: str = "agent") -> str:
    """Append an attested audit event for a tool invocation to the hash-chained ledger."""
    try:
        result = json.loads(result_json)
    except json.JSONDecodeError:
        result = {"raw": result_json}
    record = _attest(tool_name, result, actor)
    return json.dumps({"attested": True, "seq": record["seq"], "hash": record["hash"]}, indent=2)


@tool
def list_attested_events(limit: int = 20) -> str:
    """List recent attested ledger events (newest last)."""
    events = load_events()
    slice_ = events[-limit:]
    return json.dumps({"count": len(slice_), "events": slice_}, indent=2)


def attest_silent(tool_name: str, result: dict[str, Any], actor: str = "agent") -> None:
    """Internal helper used by other tools to auto-attest every call."""
    _attest(tool_name, result, actor)
