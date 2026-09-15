"""Shared helpers for building Strands agents."""

from __future__ import annotations

import os
from typing import Any

from strands import Agent


def credentials_available() -> bool:
    return bool(
        os.getenv("AWS_ACCESS_KEY_ID")
        or os.getenv("AWS_PROFILE")
        or os.getenv("AWS_BEARER_TOKEN_BEDROCK")
        or os.getenv("BILLPILOT_FORCE_BEDROCK")
    )


def build_strands_agent(
    *,
    name: str,
    system_prompt: str,
    tools: list[Any],
    use_bedrock: bool | None = None,
) -> Agent:
    """Build a Strands Agent with Bedrock when available, else DemoModel."""
    if use_bedrock is None:
        use_bedrock = credentials_available()

    model = None
    if use_bedrock:
        try:
            from strands.models import BedrockModel

            model = BedrockModel(
                model_id=os.getenv(
                    "BILLPILOT_MODEL_ID",
                    "global.anthropic.claude-sonnet-4-6",
                ),
                region_name=os.getenv("AWS_REGION", "us-west-2"),
                temperature=0.2,
            )
        except Exception as exc:  # pragma: no cover
            print(f"[billpilot] Bedrock unavailable ({exc}); using DemoModel")

    if model is None:
        from billpilot.models.demo_model import DemoModel

        model = DemoModel(agent_name=name)

    return Agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        name=name,
        agent_id=name.lower().replace(" ", "-"),
    )
