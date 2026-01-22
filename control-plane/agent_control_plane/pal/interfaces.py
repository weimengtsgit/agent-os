"""
PAL (Policy Abstraction Layer) Interfaces

Defines the contract between control-plane and runtime implementations.
These interfaces ensure runtime-agnostic design.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class RunEvent:
    """
    RunEvent represents a single event in an agent execution.
    Events are the single source of truth for all agent runs.
    """

    def __init__(
        self,
        run_id: str,
        event_type: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        agent_name: Optional[str] = None,
        sequence_number: Optional[int] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        error: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ):
        self.run_id = run_id
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.utcnow()
        self.agent_name = agent_name
        self.sequence_number = sequence_number
        self.trace_id = trace_id
        self.span_id = span_id
        self.error = error
        self.metrics = metrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary matching RunEvent schema"""
        event = {
            "apiVersion": "agent-os.dev/v1alpha1",
            "kind": "RunEvent",
            "metadata": {
                "runId": self.run_id,
                "timestamp": self.timestamp.isoformat() + "Z",
            },
            "spec": {
                "eventType": self.event_type,
                "data": self.data,
            },
        }

        # Add optional metadata fields
        if self.agent_name:
            event["metadata"]["agentName"] = self.agent_name
        if self.sequence_number is not None:
            event["metadata"]["sequenceNumber"] = self.sequence_number

        # Add optional spec fields
        if self.trace_id:
            event["spec"]["traceId"] = self.trace_id
        if self.span_id:
            event["spec"]["spanId"] = self.span_id
        if self.error:
            event["spec"]["error"] = self.error
        if self.metrics:
            event["spec"]["metrics"] = self.metrics

        return event


class EventSink(ABC):
    """
    EventSink receives and persists RunEvents.
    Default implementation writes to JSONL files.
    """

    @abstractmethod
    def emit(self, event: RunEvent) -> None:
        """Emit a single event"""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered events"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the sink and release resources"""
        pass


class TraceSink(ABC):
    """
    TraceSink receives and persists TraceSpans.
    Used for distributed tracing integration.
    """

    @abstractmethod
    def emit_span(self, span: Dict[str, Any]) -> None:
        """Emit a trace span"""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered spans"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the sink and release resources"""
        pass


class ToolExecutor(ABC):
    """
    ToolExecutor executes tools according to Tool specs.
    Runtime implementations provide concrete tool execution.
    """

    @abstractmethod
    def execute(
        self,
        tool_name: str,
        tool_spec: Dict[str, Any],
        parameters: Dict[str, Any],
    ) -> Any:
        """
        Execute a tool with given parameters.

        Args:
            tool_name: Name of the tool to execute
            tool_spec: Tool specification (validated against Tool schema)
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        pass


class PolicyEngine(ABC):
    """
    PolicyEngine enforces policies on agent execution.
    Placeholder for future policy implementation.
    """

    @abstractmethod
    def validate_run(self, agent_spec: Dict[str, Any], input_data: Dict[str, Any]) -> bool:
        """
        Validate if a run is allowed according to policies.

        Args:
            agent_spec: Agent specification
            input_data: Input data for the run

        Returns:
            True if run is allowed, False otherwise
        """
        pass

    @abstractmethod
    def check_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Check if a tool call is allowed.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters

        Returns:
            True if tool call is allowed, False otherwise
        """
        pass


class AgentRuntime(ABC):
    """
    AgentRuntime is the main interface for runtime implementations.
    Each runtime (agno, langchain, etc.) implements this interface.
    """

    @abstractmethod
    def run(
        self,
        agent_spec: Dict[str, Any],
        input_data: Dict[str, Any],
        event_sink: EventSink,
        trace_sink: Optional[TraceSink] = None,
        policy_engine: Optional[PolicyEngine] = None,
    ) -> Dict[str, Any]:
        """
        Run an agent with given input.

        Args:
            agent_spec: Agent specification (validated against Agent schema)
            input_data: Input data for the agent
            event_sink: Sink for emitting RunEvents
            trace_sink: Optional sink for emitting TraceSpans
            policy_engine: Optional policy engine for enforcement

        Returns:
            Run result dictionary with:
                - run_id: Unique run identifier
                - status: "success" or "error"
                - output: Agent output (if successful)
                - error: Error information (if failed)
        """
        pass

    @abstractmethod
    def get_runtime_info(self) -> Dict[str, Any]:
        """
        Get runtime information.

        Returns:
            Dictionary with runtime metadata:
                - name: Runtime name (e.g., "agno")
                - version: Runtime version
                - capabilities: List of supported features
        """
        pass
