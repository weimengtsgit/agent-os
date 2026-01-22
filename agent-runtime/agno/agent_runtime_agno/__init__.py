"""
Agent Runtime - Agno

Agno runtime adapter for Agent OS.

This is a data plane implementation that:
- Implements the Runtime interface defined by control-plane
- Adapts agno framework to Agent OS specs
- Produces RunEvent streams for all executions

To use this runtime, import it to register with RuntimeRegistry:
    import agent_runtime_agno
"""

from agent_runtime_agno.adapters import AgnoRuntimeAdapter

__version__ = "0.1.0"

__all__ = ["AgnoRuntimeAdapter"]
