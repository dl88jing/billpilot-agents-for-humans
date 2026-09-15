# BillPilot

**Everyday Agents** submission for [AWS Agents for Humans](https://agentsforhumans.devpost.com/) — a **multi-agent Strands swarm** that quietly runs household bill busywork and only surfaces a human when **policy** requires a real decision.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Devpost](https://img.shields.io/badge/Devpost-BillPilot-orange)](https://devpost.com/software/billpilot-ukjmq2)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Strands](https://img.shields.io/badge/Strands-Agents%20SDK-purple.svg)](https://strandsagents.com/)

## Live demo

**Production web demo:** https://billpilot-web.vercel.app

Click **Run live demo** to exercise the decision gate (auto-handle vs human escalate).

## Demo video

**https://www.youtube.com/watch?v=AlY--OayjzA**

[![BillPilot demo](https://img.youtube.com/vi/AlY--OayjzA/maxresdefault.jpg)](https://www.youtube.com/watch?v=AlY--OayjzA)

## Why BillPilot wins the Everyday Agents theme

AWS asked for agents that **run quietly in the background** and surface people only when there is a real decision. BillPilot encodes that contract in three layers:

| Layer | Role |
|-------|------|
| **Multi-agent Strands swarm** | Intake → Risk → Treasurer / Comms — specialized agents with real `@tool`s |
| **Deterministic policy engine** | Agents *propose*; `policies/default.yaml` *decides* `AUTO` vs `HUMAN_REQUIRED` |
| **Hash-chained audit ledger** | Every tool call is attested; `verify_ledger` prints **PASS** |

```
Quiet AUTO path     → funding check → payment prep → mark_auto_handled (no ping)
HUMAN_REQUIRED path → notify_human(reason, recommended_action)
```

This is not a chatbot that talks about bills. It **does the work** with a visible swarm, policy gate, and attestation trail.

## Problem

Households lose hours to recurring admin: due dates, “did I already pay that?”, surprise subscription bumps, duplicate charges, and new vendors. Individually minor; together they drain attention and create late fees / anxiety.

## Who it’s for

Busy households who want bill busywork handled autonomously — not another dashboard to babysit every week.

## Why it matters

- Real money at risk (late fees, double-pays, new-payee fraud)
- High-frequency repetitive work (perfect Everyday Agents track)
- Clear human-in-the-loop boundary judges can see in CLI + web demo

## Architecture

![BillPilot architecture](docs/architecture.svg)

Details: [docs/architecture.md](docs/architecture.md)

### Swarm

| Agent | Responsibility | Tools |
|-------|----------------|-------|
| **Intake** | Email + calendar → candidates | `list_inbox`, `parse_email_bill`, `list_calendar_dues`, `match_bill_to_calendar` |
| **Risk** | Surprises & duplicates | `check_anomaly`, `detect_duplicates` |
| **Policy** | Deterministic gate (not an LLM) | `auto_pay_max_usd`, trusted payees, duplicate window, funding buffer |
| **Treasurer** | Funding + payment prep (AUTO) | `list_accounts`, `check_funding`, `queue_payment_prep`, `summarize_payment_queue` |
| **Comms** | Quiet complete / human ping | `mark_auto_handled`, `notify_human` |

Orchestrator (`billpilot/orchestrator.py`) builds the Strands swarm (`DemoModel` offline, `BedrockModel` when AWS credentials exist) and runs the pipeline end-to-end.

### Policy knobs (`policies/default.yaml`)

- `auto_pay_max_usd`
- `trusted_payees` + `require_human_on_new_payee`
- `duplicate_window_days`
- `min_funding_buffer`

### Audit ledger

Append-only JSONL: `sha256(prev_hash + seq + ts + type + payload)`.

```bash
python -m billpilot.verify_ledger
# status: PASS  events: N  by_type: {...}
```

## Strands Agents usage (Technical Implementation)

Real Strands surface — not a wrapper:

- `from strands import Agent, tool`
- Four specialized agents under `billpilot/agents/`
- Fourteen `@tool` functions under `billpilot/tools/`
- `DemoModel` for offline Agent construction; `BedrockModel` when credentials exist
- Offline fixture pipeline **calls the same tools** so judges verify without keys

## Quick start (judges)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
python -m billpilot.demo
python -m billpilot.verify_ledger
```

**Expected demo behavior**

| Scenario | Example | Gate |
|----------|---------|------|
| Routine utility / autopay / insurance | PG&E bill-001, City Water, State Farm | `AUTO` |
| Surprise subscription | StreamFlix $45.99 vs $15.99 | `HUMAN_REQUIRED` |
| Duplicate utility | bill-005 mirrors bill-001 | `HUMAN_REQUIRED` |
| New payee | GreenLeaf Landscaping | `HUMAN_REQUIRED` |
| Low funding buffer | Verizon after cumulative AUTO draws | `HUMAN_REQUIRED` |

## Live Bedrock path (optional)

```bash
export AWS_REGION=us-west-2
# AWS credentials with Bedrock model access
python -c "from billpilot.agents.intake import build_intake_agent; print(build_intake_agent(use_bedrock=True))"
```

## Project layout

```
billpilot/
  agents/           # Intake, Risk, Treasurer, Comms (Strands Agent builders)
  tools/            # @tool implementations + auto-attestation
  models/           # DemoModel for offline Agent construction
  orchestrator.py   # intake → risk → policy → treasurer/comms
  policy.py         # deterministic AUTO / HUMAN_REQUIRED engine
  ledger.py         # hash-chained append-only audit log
  demo.py           # offline end-to-end demo
  verify_ledger.py  # PASS + event counts
policies/
  default.yaml
data/
  household.json  inbox_emails.json  sample_bills.json
  accounts.json   calendar.json
docs/
  architecture.md  architecture.svg  JUDGING.md
LICENSE             # Apache-2.0
```

## Judging alignment

See [docs/JUDGING.md](docs/JUDGING.md).

| Criterion | How BillPilot addresses it |
|-----------|----------------------------|
| Technical Implementation | Multi-agent Strands swarm, policy engine, hash-chained ledger, Bedrock-ready |
| Design | Coherent Everyday Agent: quiet by default, human only at policy gate |
| Potential Impact | Specific audience + concrete failure modes (duplicates, surprises, new payees, buffer) |
| Creativity | Agents propose / policy decides / ledger attests |
| Presentation | Video + live web demo + one-command offline CLI |

## Links

- Live demo: https://billpilot-web.vercel.app
- Demo video: https://www.youtube.com/watch?v=AlY--OayjzA
- Devpost: https://devpost.com/software/billpilot-ukjmq2
- Builder.aws bonus post: https://builder.aws.com/content/3JLEXwVExE2NBkjRf5KTT85WsZM/agents-for-humans-building-billpilot-an-everyday-agent-that-only-interrupts-when-it-matters
- Hackathon: https://agentsforhumans.devpost.com/

## License

Apache License 2.0 — see [LICENSE](LICENSE).
