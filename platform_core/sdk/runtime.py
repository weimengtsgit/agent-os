"""Runtime adapter interface - NO direct agno dependency."""

from abc import ABC, abstractmethod
from typing import Any, Dict, AsyncIterator
from pathlib import Path

from .models import AgentSpec, RunEvent


class RuntimeAdapter(ABC):
    """Abstract base class for runtime adapters.

    This interface is runtime-agnostic. Concrete implementations
    (e.g., AgnoRuntimeAdapter) live in agent-runtime-agno/.
    """

    @abstractmethod
    async def initialize(self, agent_spec: AgentSpec, config: Dict[str, Any]) -> None:
        """Initialize the runtime with agent spec."""
        pass

    @abstractmethod
    async def run(
        self, input_data: Dict[str, Any], run_dir: Path
    ) -> AsyncIterator[RunEvent]:
        """Execute agent and yield RunEvents."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup runtime resources."""
        pass
