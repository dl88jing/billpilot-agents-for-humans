# BillPilot

**Everyday Agents** submission for [AWS Agents for Humans](https://agentsforhumans.devpost.com/) — built with the **Strands Agents SDK**.

> An autonomous household-bill agent that does the busywork end-to-end and **only pings a human at the decision gate** (unexpected amount, duplicate charge, ambiguity).

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Devpost](https://img.shields.io/badge/Devpost-BillPilot-orange)](https://devpost.com/software/billpilot-ukjmq2)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Demo video

Watch the pitch + end-to-end walkthrough (problem → who → why it matters → working demo):

**https://www.youtube.com/watch?v=AlY--OayjzA**

[![BillPilot demo](https://img.youtube.com/vi/AlY--OayjzA/maxresdefault.jpg)](https://www.youtube.com/watch?v=AlY--OayjzA)

## Why BillPilot wins the theme

AWS asked for agents that **run quietly in the background** and surface people only when there is a real decision. BillPilot encodes that product contract in code:

| Path | When | What happens |
|------|------|----------------|
| Quiet auto-handle | Amount in expected range, no duplicate | `queue_payment_prep` → `mark_auto_handled` — no human ping |
| Decision gate | Unexpected amount **or** duplicate charge | `notify_human` with reason + recommended action |

This is not a chatbot that talks about bills. It **does the work** with Strands `@tool`s.

## Problem

Households lose hours to recurring admin: due dates, “did I already pay that?”, surprise subscription bumps, and duplicate charges. Individually minor; together they drain attention and create late fees / anxiety.

## Who it’s for

Busy households and anyone who wants bill busywork handled autonomously — not another dashboard to open every week.

## Why it matters

- Real money at risk (late fees, double-pays)
- High-frequency repetitive work (perfect Everyday Agents track)
- Clear human-in-the-loop boundary judges can see in the demo

## Architecture

![BillPilot architecture](docs/architecture.svg)

Details: [docs/architecture.md](docs/architecture.md)

```
Bill fixtures / intake
        ↓
 Strands Agent + tools (list → parse → anomaly)
        ↓
   Decision gate
   ├─ safe  → payment prep + auto-handle (quiet)
   └─ risky → notify_human (decision required)
        ↓
 Optional live path: Amazon BedrockModel
 Optional stretch: Bedrock AgentCore deployment
```

## Strands Agents usage (Technical Implementation)

Real Strands surface — not a wrapper:

- `from strands import Agent, tool`
- Six `@tool` functions in `billpilot/tools.py`
- `BedrockModel` path in `billpilot/agent.py` when AWS credentials exist
- Offline fixture pipeline calls the **same tools** so judges can verify without keys

### Tools

| Tool | Role |
|------|------|
| `list_bills` | Intake due / handled / all bills |
| `parse_bill` | Normalize a bill for reasoning |
| `check_anomaly` | Unexpected amount + duplicate detection |
| `queue_payment_prep` | Build payment checklist |
| `notify_human` | Decision-gate ping only |
| `mark_auto_handled` | Quiet completion record |

## Quick start (judges)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
python -m billpilot.demo
```

**Expected demo behavior**

- Auto-handles routine **City Water** and **State Farm** bills
- Escalates **StreamFlix** for unexpected amount ($45.99 vs $15.99)
- Escalates **duplicate PG&E** charges (bill-001 ↔ bill-005)

## Live Bedrock path (optional)

```bash
export AWS_REGION=us-west-2
# AWS credentials with Bedrock model access
python -c "from billpilot.agent import run_with_strands_agent; print(run_with_strands_agent())"
```

## Project layout

```
billpilot/
  agent.py      # Strands Agent + BedrockModel + offline pipeline
  tools.py      # @tool implementations + decision gate
  demo.py       # End-to-end offline demo for judges
data/
  sample_bills.json
docs/
  architecture.md
  architecture.svg
LICENSE         # Apache-2.0
```

## Judging alignment

| Criterion | How BillPilot addresses it |
|-----------|----------------------------|
| Technical Implementation | Non-trivial Strands tools + agent loop; Bedrock-ready; AgentCore noted as stretch |
| Design | Coherent Everyday Agent product: quiet by default, human only at gate |
| Potential Impact | Specific audience + concrete failure modes (duplicates, surprise amounts) |
| Creativity | Decision-gate-as-product, not “chat about my bills” |
| Presentation | Video covers problem / who / why + working demo |

## Links

- Builder.aws bonus post: https://builder.aws.com/content/3JLEXwVExE2NBkjRf5KTT85WsZM/agents-for-humans-building-billpilot-an-everyday-agent-that-only-interrupts-when-it-matters
- Devpost: https://devpost.com/software/billpilot-ukjmq2
- Demo video: https://www.youtube.com/watch?v=AlY--OayjzA
- Hackathon: https://agentsforhumans.devpost.com/

## License

Apache License 2.0 — see [LICENSE](LICENSE).
