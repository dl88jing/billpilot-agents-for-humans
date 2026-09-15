"""Minimal offline Model stub so Strands Agents can be constructed without Bedrock.

The hackathon offline demo primarily uses deterministic orchestration that still
invokes the same @tool functions. When AWS credentials exist, BedrockModel is used.
DemoModel satisfies the Model ABC for agent construction / smoke tests.
"""

from __future__ import annotations

import json
import threading
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any, TypeVar

from pydantic import BaseModel
from strands.models.model import Model
from strands.types.content import Messages, SystemContentBlock
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolChoice, ToolSpec

T = TypeVar("T", bound=BaseModel)


class DemoModel(Model):
    """Deterministic text-only model for offline Agent construction."""

    def __init__(self, agent_name: str = "BillPilot"):
        self.agent_name = agent_name
        self.config: dict[str, Any] = {"model_id": f"billpilot-demo/{agent_name}"}

    def update_config(self, **model_config: Any) -> None:
        self.config.update(model_config)

    def get_config(self) -> dict[str, Any]:
        return dict(self.config)

    async def structured_output(
        self,
        output_model: type[T],
        prompt: Messages,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, T | Any], None]:
        instance = output_model()  # type: ignore[call-arg]
        yield {"output": instance}

    async def stream(
        self,
        messages: Messages,
        tool_specs: list[ToolSpec] | None = None,
        system_prompt: str | None = None,
        *,
        tool_choice: ToolChoice | None = None,
        system_prompt_content: list[SystemContentBlock] | None = None,
        invocation_state: dict[str, Any] | None = None,
        cancel_signal: threading.Event | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamEvent]:
        summary = {
            "agent": self.agent_name,
            "mode": "demo_model",
            "note": (
                "Offline DemoModel — production path uses BedrockModel. "
                "Orchestrator invokes Strands @tools directly in demo mode."
            ),
            "tools_available": [t.get("name") for t in (tool_specs or []) if isinstance(t, dict)],
        }
        text = json.dumps(summary)
        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockStart": {"start": {"text": ""}}}
        yield {"contentBlockDelta": {"delta": {"text": text}}}
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "end_turn"}}
