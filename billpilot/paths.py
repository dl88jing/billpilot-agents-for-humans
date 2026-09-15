"""Shared filesystem paths for BillPilot package data and runtime."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RUNTIME_DIR = DATA_DIR / "runtime"
POLICIES_DIR = ROOT / "policies"
DEFAULT_POLICY_PATH = POLICIES_DIR / "default.yaml"
LEDGER_PATH = RUNTIME_DIR / "ledger.jsonl"
STATE_PATH = RUNTIME_DIR / "state.json"

BILLS_PATH = DATA_DIR / "sample_bills.json"
HOUSEHOLD_PATH = DATA_DIR / "household.json"
INBOX_PATH = DATA_DIR / "inbox_emails.json"
ACCOUNTS_PATH = DATA_DIR / "accounts.json"
CALENDAR_PATH = DATA_DIR / "calendar.json"


def ensure_runtime() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
