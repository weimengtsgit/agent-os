"""
Default Implementations of PAL Interfaces

Provides concrete implementations for EventSink, TraceSink, and PolicyEngine.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from agent_control_plane.pal.interfaces import EventSink, PolicyEngine, RunEvent, TraceSink


class FileEventSink(EventSink):
    """
    FileEventSink writes RunEvents to a JSONL file.
    This is the default event sink for local runs.
    """

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_handle = open(self.output_path, "w")
        self.event_count = 0

    def emit(self, event: RunEvent) -> None:
        """Write event to JSONL file"""
        event_dict = event.to_dict()
        json_line = json.dumps(event_dict, ensure_ascii=False)
        self.file_handle.write(json_line + "\n")
        self.file_handle.flush()
        self.event_count += 1

    def flush(self) -> None:
        """Flush file buffer"""
        self.file_handle.flush()

    def close(self) -> None:
        """Close file handle"""
        self.file_handle.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class NoOpTraceSink(TraceSink):
    """
    NoOpTraceSink is a no-op implementation of TraceSink.
    Used when tracing is not enabled.
    """

    def emit_span(self, span: Dict[str, Any]) -> None:
        """No-op"""
        pass

    def flush(self) -> None:
        """No-op"""
        pass

    def close(self) -> None:
        """No-op"""
        pass


class NoOpPolicyEngine(PolicyEngine):
    """
    NoOpPolicyEngine is a permissive policy engine.
    Allows all operations (used for MVP).
    """

    def validate_run(self, agent_spec: Dict[str, Any], input_data: Dict[str, Any]) -> bool:
        """Always allow runs"""
        return True

    def check_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """Always allow tool calls"""
        return True
