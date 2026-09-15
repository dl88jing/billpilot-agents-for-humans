# BillPilot Architecture

BillPilot is a **multi-agent Everyday Agent** for the [AWS Agents for Humans](https://agentsforhumans.devpost.com/) hackathon, built with the [Strands Agents SDK](https://strandsagents.com/).

## Product contract

**Do the bill busywork. Interrupt humans only when policy requires a real decision.**

Agents **propose**; the deterministic policy engine **decides** (`AUTO` vs `HUMAN_REQUIRED`). Every tool call is **attested** into a hash-chained ledger.

## Diagram

![Architecture](architecture.svg)

## Swarm pipeline

```
Fixtures (inbox / calendar / bills / accounts)
        ↓
 [Intake Agent]   list_inbox, parse_email_bill, calendar dues
        ↓
 [Risk Agent]     check_anomaly, detect_duplicates
        ↓
 [Policy Engine]  policies/default.yaml → AUTO | HUMAN_REQUIRED
        ↓
   ┌────┴────┐
   ↓         ↓
[Treasurer] [Comms]
 funding +   quiet mark_auto_handled
 payment     OR notify_human
 prep
        ↓
 Hash-chained audit ledger (verify_ledger → PASS)
```

## Agents (Strands)

| Agent | Package | Tools |
|-------|---------|-------|
| Intake | `billpilot/agents/intake.py` | `list_inbox`, `parse_email_bill`, `list_calendar_dues`, `match_bill_to_calendar` |
| Risk | `billpilot/agents/risk.py` | `check_anomaly`, `detect_duplicates` |
| Treasurer | `billpilot/agents/treasurer.py` | `list_accounts`, `check_funding`, `queue_payment_prep`, `summarize_payment_queue` |
| Comms | `billpilot/agents/comms.py` | `notify_human`, `mark_auto_handled` |

Orchestrator: `billpilot/orchestrator.py` builds the swarm (`DemoModel` offline, `BedrockModel` when AWS credentials exist) and runs intake → risk → policy → treasurer/comms.

## Policy engine

`billpilot/policy.py` + `policies/default.yaml`:

- `auto_pay_max_usd`
- `trusted_payees` / `require_human_on_new_payee`
- `duplicate_window_days`
- `min_funding_buffer`
- amount surprise vs `expected_amount_range`

## Audit ledger

`billpilot/ledger.py` — append-only JSONL with `sha256(prev_hash|seq|ts|type|payload)`.

```bash
python -m billpilot.verify_ledger
```

## Model layer

- **Offline / judges:** deterministic orchestration invoking the **same** Strands `@tool`s; agents constructed with `DemoModel`
- **Live:** Strands `Agent` + `BedrockModel`
- **Stretch:** Amazon Bedrock AgentCore

## Scenarios covered in fixtures

| Scenario | Bill | Expected gate |
|----------|------|----------------|
| Routine utility | bill-001 City path / PG&E first | AUTO (if buffer OK) |
| Surprise subscription | bill-003 StreamFlix $45.99 vs $15.99 | HUMAN_REQUIRED |
| Duplicate utility | bill-005 mirrors bill-001 | HUMAN_REQUIRED |
| New payee | bill-006 GreenLeaf | HUMAN_REQUIRED |
| Low balance buffer | bill-007 Verizon after draws | HUMAN_REQUIRED when buffer breached |
