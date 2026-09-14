# BillPilot

**Everyday Agents** submission for the [AWS Agents for Humans](https://agentsforhumans.devpost.com/) hackathon.

BillPilot is an autonomous agent built with the **Strands Agents SDK** that takes over household bill busywork — intake, anomaly detection, payment prep — and **only pings you when a real decision is required**.

## Problem

People lose hours to small recurring admin: due dates, duplicate charges, surprise subscription bumps, and “did I already pay that?” anxiety. Individually minor; together they drain attention.

## Who it’s for

Busy households and anyone who wants bills handled quietly in the background — not another dashboard to babysit.

## Why it matters

The hackathon theme is agents that run autonomously and surface humans only at decision points. BillPilot encodes that pattern with an explicit **decision gate**: unexpected amounts and duplicates escalate; routine bills are prepared silently.

## How it works

| Step | Tool | Behavior |
|------|------|----------|
| Intake | `list_bills`, `parse_bill` | Load and normalize due bills |
| Analyze | `check_anomaly` | Flag amount outliers + duplicates |
| Auto path | `queue_payment_prep`, `mark_auto_handled` | Quiet prep for safe bills |
| Human path | `notify_human` | Decision-gate ping with recommended action |

- **Offline demo (judges):** deterministic pipeline calling the same Strands `@tool` functions — **no AWS keys required**
- **Live path:** Strands `Agent` + `BedrockModel` (Amazon Bedrock) with the identical tool surface
- **Stretch:** deploy with Amazon Bedrock AgentCore to strengthen Technical Implementation

See [docs/architecture.md](docs/architecture.md) and [docs/architecture.svg](docs/architecture.svg).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m billpilot.demo
```

Expected demo highlights:

- Auto-handles routine utility / insurance bills
- Escalates **StreamFlix** unexpected amount jump
- Escalates **duplicate** Pacific Gas & Electric charge

## Live Bedrock (optional)

```bash
export AWS_REGION=us-west-2
# configure AWS credentials with Bedrock access
python -c "from billpilot.agent import run_with_strands_agent; print(run_with_strands_agent())"
```

## Project layout

```
billpilot/          # Strands agent + tools + offline demo
data/               # sample bills + runtime state
docs/               # architecture write-up + diagram
LICENSE             # Apache-2.0
```

## License

Apache License 2.0 — see [LICENSE](LICENSE).

## Hackathon track

**Everyday Agents** — AWS Agents for Humans (Strands Agents SDK).
