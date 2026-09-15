"""Hash-chained append-only audit ledger for BillPilot attestations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from billpilot.paths import LEDGER_PATH, ensure_runtime

GENESIS_HASH = "0" * 64


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _hash_link(prev_hash: str, seq: int, ts: str, event_type: str, payload: dict[str, Any]) -> str:
    material = f"{prev_hash}|{seq}|{ts}|{event_type}|{_canonical(payload)}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def reset_ledger() -> None:
    ensure_runtime()
    if LEDGER_PATH.exists():
        LEDGER_PATH.unlink()


def _tail() -> tuple[int, str]:
    ensure_runtime()
    if not LEDGER_PATH.exists():
        return 0, GENESIS_HASH
    last: dict[str, Any] | None = None
    with LEDGER_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                last = json.loads(line)
    if last is None:
        return 0, GENESIS_HASH
    return int(last["seq"]), str(last["hash"])


def append_event(event_type: str, payload: dict[str, Any], actor: str = "system") -> dict[str, Any]:
    """Append an attested event; returns the full ledger record."""
    ensure_runtime()
    prev_seq, prev_hash = _tail()
    seq = prev_seq + 1
    ts = datetime.now(timezone.utc).isoformat()
    body = {"actor": actor, **payload}
    digest = _hash_link(prev_hash, seq, ts, event_type, body)
    record = {
        "seq": seq,
        "ts": ts,
        "type": event_type,
        "prev_hash": prev_hash,
        "hash": digest,
        "payload": body,
    }
    with LEDGER_PATH.open("a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def load_events() -> list[dict[str, Any]]:
    ensure_runtime()
    if not LEDGER_PATH.exists():
        return []
    events: list[dict[str, Any]] = []
    with LEDGER_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def verify_ledger() -> dict[str, Any]:
    """Recompute the hash chain. Returns status + counts."""
    events = load_events()
    if not events:
        return {"ok": True, "status": "PASS", "events": 0, "by_type": {}, "message": "empty ledger"}

    by_type: dict[str, int] = {}
    expected_prev = GENESIS_HASH
    for i, ev in enumerate(events, start=1):
        if ev["seq"] != i:
            return {
                "ok": False,
                "status": "FAIL",
                "events": len(events),
                "by_type": by_type,
                "message": f"sequence gap at seq={ev.get('seq')} expected={i}",
            }
        if ev["prev_hash"] != expected_prev:
            return {
                "ok": False,
                "status": "FAIL",
                "events": len(events),
                "by_type": by_type,
                "message": f"prev_hash mismatch at seq={i}",
            }
        recomputed = _hash_link(
            ev["prev_hash"],
            ev["seq"],
            ev["ts"],
            ev["type"],
            ev["payload"],
        )
        if recomputed != ev["hash"]:
            return {
                "ok": False,
                "status": "FAIL",
                "events": len(events),
                "by_type": by_type,
                "message": f"hash mismatch at seq={i}",
            }
        by_type[ev["type"]] = by_type.get(ev["type"], 0) + 1
        expected_prev = ev["hash"]

    return {
        "ok": True,
        "status": "PASS",
        "events": len(events),
        "by_type": by_type,
        "message": f"chain intact ({len(events)} events)",
    }
