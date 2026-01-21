"""Agno Runtime Adapter - Implements RuntimeAdapter for agno framework.

This is the ONLY place where agno dependency is allowed.
"""

from typing import Any, Dict, AsyncIterator
from pathlib import Path
import json
from datetime import datetime
import uuid

from platform_core.sdk.runtime import RuntimeAdapter
from platform_core.sdk.models import AgentSpec, RunEvent


class AgnoRuntimeAdapter(RuntimeAdapter):
    """Agno-specific runtime adapter.

    Note: This is a stub implementation. Real implementation would:
    - Import agno library
    - Initialize agno agent
    - Execute and stream events
    """

    def __init__(self):
        self.agent_spec: AgentSpec = None
        self.config: Dict[str, Any] = {}

    async def initialize(self, agent_spec: AgentSpec, config: Dict[str, Any]) -> None:
        """Initialize the runtime with agent spec."""
        self.agent_spec = agent_spec
        self.config = config
        # TODO: Initialize agno agent here
        # import agno
        # self.agno_agent = agno.Agent(...)

    async def run(
        self, input_data: Dict[str, Any], run_dir: Path
    ) -> AsyncIterator[RunEvent]:
        """Execute agent and yield RunEvents."""
        run_id = str(uuid.uuid4())
        run_dir.mkdir(parents=True, exist_ok=True)
        events_file = run_dir / "events.jsonl"

        # Open events file for writing
        with open(events_file, "w") as f:
            # Start event
            start_event = RunEvent(
                run_id=run_id,
                agent_id=self.agent_spec.id,
                event_type="start",
                data={"input": input_data, "config": self.config},
            )
            f.write(start_event.to_jsonl() + "\n")
            f.flush()
            yield start_event

            # TODO: Execute agno agent and stream real events
            # For now, just emit a placeholder message event
            message_event = RunEvent(
                run_id=run_id,
                agent_id=self.agent_spec.id,
                event_type="message",
                data={"content": "Agno runtime not yet implemented - this is a stub"},
            )
            f.write(message_event.to_jsonl() + "\n")
            f.flush()
            yield message_event

            # End event
            end_event = RunEvent(
                run_id=run_id,
                agent_id=self.agent_spec.id,
                event_type="end",
                data={"status": "completed"},
            )
            f.write(end_event.to_jsonl() + "\n")
            f.flush()
            yield end_event

    async def cleanup(self) -> None:
        """Cleanup runtime resources."""
        # TODO: Cleanup agno resources
        pass
