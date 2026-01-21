"""Core data models for Agent OS."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AgentSpec(BaseModel):
    """Agent specification model."""

    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    name: str
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    description: Optional[str] = None
    runtime: str = Field(..., pattern=r"^(agno|langchain|custom)$")
    tools: List[str] = Field(default_factory=list)
    policies: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)


class ToolSpec(BaseModel):
    """Tool specification model."""

    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    name: str
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    type: str = Field(..., pattern=r"^(function|api|mcp)$")
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    returns: Optional[Dict[str, Any]] = None


class PolicySpec(BaseModel):
    """Policy specification model."""

    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    name: str
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    description: Optional[str] = None
    rules: List[Dict[str, Any]] = Field(default_factory=list)


class RunEvent(BaseModel):
    """Event emitted during agent execution."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    run_id: str
    agent_id: str
    event_type: str  # start, tool_call, tool_result, message, error, end
    data: Dict[str, Any] = Field(default_factory=dict)

    def to_jsonl(self) -> str:
        """Convert to JSONL format."""
        return self.model_dump_json()
