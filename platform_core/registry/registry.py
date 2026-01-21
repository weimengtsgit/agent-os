"""Registry for managing agents, tools, and policies."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from ..sdk.models import AgentSpec, ToolSpec, PolicySpec


class Registry:
    """Local file-based registry."""

    def __init__(self, registry_dir: Path = None):
        """Initialize registry."""
        if registry_dir is None:
            registry_dir = Path.cwd() / "platform-core" / "registry"
        self.registry_dir = registry_dir
        self.agents_dir = registry_dir / "agents"
        self.tools_dir = registry_dir / "tools"
        self.policies_dir = registry_dir / "policies"

        # Create directories
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.policies_dir.mkdir(parents=True, exist_ok=True)

    def register_agent(self, spec: AgentSpec) -> None:
        """Register an agent."""
        file_path = self.agents_dir / f"{spec.id}.json"
        with open(file_path, "w") as f:
            json.dump(spec.model_dump(), f, indent=2)

    def get_agent(self, agent_id: str) -> Optional[AgentSpec]:
        """Get agent by ID."""
        file_path = self.agents_dir / f"{agent_id}.json"
        if not file_path.exists():
            return None
        with open(file_path) as f:
            return AgentSpec(**json.load(f))

    def list_agents(self) -> List[AgentSpec]:
        """List all registered agents."""
        agents = []
        for file_path in self.agents_dir.glob("*.json"):
            with open(file_path) as f:
                agents.append(AgentSpec(**json.load(f)))
        return agents

    def register_tool(self, spec: ToolSpec) -> None:
        """Register a tool."""
        file_path = self.tools_dir / f"{spec.id}.json"
        with open(file_path, "w") as f:
            json.dump(spec.model_dump(), f, indent=2)

    def get_tool(self, tool_id: str) -> Optional[ToolSpec]:
        """Get tool by ID."""
        file_path = self.tools_dir / f"{tool_id}.json"
        if not file_path.exists():
            return None
        with open(file_path) as f:
            return ToolSpec(**json.load(f))

    def register_policy(self, spec: PolicySpec) -> None:
        """Register a policy."""
        file_path = self.policies_dir / f"{spec.id}.json"
        with open(file_path, "w") as f:
            json.dump(spec.model_dump(), f, indent=2)

    def get_policy(self, policy_id: str) -> Optional[PolicySpec]:
        """Get policy by ID."""
        file_path = self.policies_dir / f"{policy_id}.json"
        if not file_path.exists():
            return None
        with open(file_path) as f:
            return PolicySpec(**json.load(f))
