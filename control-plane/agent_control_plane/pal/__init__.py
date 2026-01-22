"""
PAL (Policy Abstraction Layer)

Provides policy enforcement and governance:
- Runtime interfaces (AgentRuntime, ToolExecutor, EventSink, TraceSink)
- Default implementations (FileEventSink, NoOpPolicyEngine, DefaultToolExecutor, DefaultPolicyEngine)
- Runtime registry for runtime discovery
"""

from agent_control_plane.pal.implementations import (
    FileEventSink,
    NoOpPolicyEngine,
    NoOpTraceSink,
)
from agent_control_plane.pal.interfaces import (
    AgentRuntime,
    EventSink,
    PolicyEngine,
    RunEvent,
    ToolExecutor,
    TraceSink,
)
from agent_control_plane.pal.policy_engine import DefaultPolicyEngine
from agent_control_plane.pal.registry import RuntimeRegistry
from agent_control_plane.pal.tool_executor import DefaultToolExecutor

__all__ = [
    # Interfaces
    "AgentRuntime",
    "EventSink",
    "TraceSink",
    "ToolExecutor",
    "PolicyEngine",
    "RunEvent",
    # Implementations
    "FileEventSink",
    "NoOpTraceSink",
    "NoOpPolicyEngine",
    "DefaultToolExecutor",
    "DefaultPolicyEngine",
    # Registry
    "RuntimeRegistry",
]
