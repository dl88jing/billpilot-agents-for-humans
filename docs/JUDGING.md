# Notes for judges — BillPilot (Everyday Agents)

## Fastest path to verify (zero AWS keys)

```bash
pip install -e .
python -m billpilot.demo
python -m billpilot.verify_ledger
```

You should see:

- Strands swarm agents: Intake, Risk, Treasurer, Comms
- Policy verdicts `AUTO` vs `HUMAN_REQUIRED`
- Escalations for StreamFlix (surprise), duplicate PG&E, GreenLeaf (new payee), and low-buffer cases
- Ledger verification **PASS** with attested tool-call event counts

## Live product demo

https://billpilot-web.vercel.app

## Video

https://www.youtube.com/watch?v=AlY--OayjzA

## Track

Everyday Agents — AWS Agents for Humans

## Why this is competitive

| Criterion | Evidence in repo |
|-----------|------------------|
| Technical Implementation | Multi-agent Strands swarm, 14 `@tool`s, policy engine, hash-chained ledger, Bedrock-ready |
| Design | Quiet-by-default product contract enforced by policy, not prompt hope |
| Potential Impact | Real household money failure modes: duplicates, surprise subs, new payees, buffer risk |
| Creativity | Agents propose / policy decides / ledger attests |
| Presentation | Video + live web demo + offline CLI judges can run in one minute |

## AWS Builder ID

dl88jing@gmail.com

## Repo

https://github.com/dl88jing/billpilot-agents-for-humans
