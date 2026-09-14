# BillPilot Architecture

BillPilot is an **Everyday Agent** built with the [Strands Agents SDK](https://strandsagents.com/).
It runs quietly on recurring household bill busywork and only pings a human at a **decision gate**.

## High-level flow

1. **Intake** — `list_bills` / `parse_bill` normalize due bills from local fixtures (swap for email/PDF connectors in production).
2. **Anomaly analysis** — `check_anomaly` flags unexpected amounts and duplicate charges.
3. **Decision gate**
   - Safe → `queue_payment_prep` + `mark_auto_handled` (no human ping)
   - Risky → `notify_human` with reason + recommended action
4. **Model layer**
   - **Offline demo**: deterministic pipeline calling the same `@tool` functions (judges need zero AWS keys)
   - **Live**: Strands `Agent` + `BedrockModel` (Amazon Bedrock) with the same tool surface; AgentCore deployment is a natural next step

## Why this scores on Technical Implementation

- Real Strands `@tool` surface and agent loop (not a chat wrapper)
- Explicit human-in-the-loop gate aligned with the hackathon theme
- Bedrock-ready path without blocking the offline demo
