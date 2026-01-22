"""
Runtime Registry

Manages runtime implementations and provides runtime discovery.
"""

from typing import Dict, Optional, Type

from agent_control_plane.pal.interfaces import AgentRuntime


class RuntimeRegistry:
    """
    RuntimeRegistry maintains a registry of available runtime implementations.
    Runtimes register themselves at import time.
    """

    _runtimes: Dict[str, Type[AgentRuntime]] = {}

    @classmethod
    def register(cls, name: str, runtime_class: Type[AgentRuntime]) -> None:
        """
        Register a runtime implementation.

        Args:
            name: Runtime name (e.g., "agno", "langchain")
            runtime_class: Runtime class implementing AgentRuntime interface
        """
        cls._runtimes[name] = runtime_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[AgentRuntime]]:
        """
        Get a runtime implementation by name.

        Args:
            name: Runtime name

        Returns:
            Runtime class or None if not found
        """
        return cls._runtimes.get(name)

    @classmethod
    def list_runtimes(cls) -> list[str]:
        """
        List all registered runtime names.

        Returns:
            List of runtime names
        """
        return list(cls._runtimes.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if a runtime is registered.

        Args:
            name: Runtime name

        Returns:
            True if registered, False otherwise
        """
        return name in cls._runtimes
