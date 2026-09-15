"""Strands @tool surface used by the BillPilot multi-agent swarm."""

from billpilot.tools.anomaly import check_anomaly, detect_duplicates
from billpilot.tools.calendar_dues import list_calendar_dues, match_bill_to_calendar
from billpilot.tools.funding_accounts import check_funding, list_accounts
from billpilot.tools.inbox_sim import list_inbox, parse_email_bill
from billpilot.tools.ledger_append import attest_tool_call, list_attested_events
from billpilot.tools.notify import mark_auto_handled, notify_human
from billpilot.tools.payment_prep import queue_payment_prep, summarize_payment_queue

ALL_TOOLS = [
    list_inbox,
    parse_email_bill,
    list_calendar_dues,
    match_bill_to_calendar,
    list_accounts,
    check_funding,
    check_anomaly,
    detect_duplicates,
    queue_payment_prep,
    summarize_payment_queue,
    notify_human,
    mark_auto_handled,
    attest_tool_call,
    list_attested_events,
]

__all__ = [
    "ALL_TOOLS",
    "list_inbox",
    "parse_email_bill",
    "list_calendar_dues",
    "match_bill_to_calendar",
    "list_accounts",
    "check_funding",
    "check_anomaly",
    "detect_duplicates",
    "queue_payment_prep",
    "summarize_payment_queue",
    "notify_human",
    "mark_auto_handled",
    "attest_tool_call",
    "list_attested_events",
]
