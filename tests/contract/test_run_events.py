"""
Iteration 2: RunEvent Contract Tests

Tests that verify RunEvent contracts:
- Every run produces events.jsonl
- Events follow Kubernetes-style structure
- Minimum event sequence is present
- Events are the single source of truth
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any

import pytest


def run_agent_and_get_events(
    agent_path: str, input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run an agent and return events.

    Returns:
        {
            "returncode": int,
            "stdout": str,
            "stderr": str,
            "events": List[Dict],
            "events_path": Path or None,
        }
    """
    # Create temporary input file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(input_data, f)
        input_file = f.name

    try:
        # Run agent
        result = subprocess.run(
            ["agentctl", "run-local", agent_path, "--input", input_file],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Parse output to find events path
        events_path = None
        for line in result.stdout.split("\n"):
            if "Events:" in line:
                events_path_str = line.split("Events:")[1].strip()
                events_path = Path(events_path_str)
                break

        # Load events
        events = []
        if events_path and events_path.exists():
            with open(events_path, "r") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "events": events,
            "events_path": events_path,
        }

    finally:
        Path(input_file).unlink(missing_ok=True)


@pytest.mark.run_events
class TestRunEventContracts:
    """Test RunEvent contracts and structure"""

    def test_run_produces_events_jsonl(self):
        """Every run must produce events.jsonl file"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml", {"query": "Hello"}
        )

        assert result["returncode"] == 0, f"Run failed: {result['stderr']}"
        assert result["events_path"] is not None, "No events path found"
        assert result["events_path"].exists(), "events.jsonl file not created"

    def test_events_follow_kubernetes_structure(self):
        """All events must follow Kubernetes-style structure"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml", {"query": "Test"}
        )

        assert result["returncode"] == 0
        assert len(result["events"]) > 0, "No events generated"

        for event in result["events"]:
            # Check required top-level fields
            assert "apiVersion" in event, "Event missing apiVersion"
            assert "kind" in event, "Event missing kind"
            assert "metadata" in event, "Event missing metadata"
            assert "spec" in event, "Event missing spec"

            # Check kind
            assert event["kind"] == "RunEvent", f"Expected kind=RunEvent, got {event['kind']}"

            # Check metadata fields
            metadata = event["metadata"]
            assert "runId" in metadata, "Event metadata missing runId"
            assert "timestamp" in metadata, "Event metadata missing timestamp"
            assert "agentName" in metadata, "Event metadata missing agentName"
            assert "sequenceNumber" in metadata, "Event metadata missing sequenceNumber"

            # Check spec fields
            spec = event["spec"]
            assert "eventType" in spec, "Event spec missing eventType"
            assert "data" in spec, "Event spec missing data"

    def test_minimum_event_sequence_present(self):
        """Minimum event sequence must be present: run.start -> run.end"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml", {"query": "Simple test"}
        )

        assert result["returncode"] == 0
        events = result["events"]
        event_types = [e["spec"]["eventType"] for e in events]

        # Must have run.start and run.end
        assert "run.start" in event_types, "Missing run.start event"
        assert "run.end" in event_types or "run.error" in event_types, "Missing run.end/run.error event"

        # run.start must be first
        assert event_types[0] == "run.start", f"First event should be run.start, got {event_types[0]}"

        # run.end or run.error must be last
        assert event_types[-1] in ["run.end", "run.error"], f"Last event should be run.end/run.error, got {event_types[-1]}"

    def test_agent_lifecycle_events(self):
        """Agent lifecycle events must be present"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml", {"query": "Test agent lifecycle"}
        )

        assert result["returncode"] == 0
        event_types = [e["spec"]["eventType"] for e in result["events"]]

        # Must have agent.start and agent.end
        assert "agent.start" in event_types, "Missing agent.start event"
        assert "agent.end" in event_types, "Missing agent.end event"

        # agent.start should come after run.start
        run_start_idx = event_types.index("run.start")
        agent_start_idx = event_types.index("agent.start")
        assert agent_start_idx > run_start_idx, "agent.start should come after run.start"

        # agent.end should come before run.end
        agent_end_idx = event_types.index("agent.end")
        run_end_idx = event_types.index("run.end") if "run.end" in event_types else len(event_types) - 1
        assert agent_end_idx < run_end_idx, "agent.end should come before run.end"

    def test_tool_execution_events(self):
        """Tool execution must produce tool.call and tool.result events"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml",
            {"query": "What is 10 + 5?"}  # Should trigger calculator tool
        )

        assert result["returncode"] == 0
        event_types = [e["spec"]["eventType"] for e in result["events"]]

        # Should have tool.call and tool.result
        assert "tool.call" in event_types, "Missing tool.call event"
        assert "tool.result" in event_types, "Missing tool.result event"

        # tool.result should come after tool.call
        tool_call_indices = [i for i, t in enumerate(event_types) if t == "tool.call"]
        tool_result_indices = [i for i, t in enumerate(event_types) if t == "tool.result"]

        assert len(tool_call_indices) == len(tool_result_indices), "Mismatched tool.call and tool.result counts"

        for call_idx, result_idx in zip(tool_call_indices, tool_result_indices):
            assert result_idx > call_idx, "tool.result should come after tool.call"

    def test_sequence_numbers_are_monotonic(self):
        """Sequence numbers must be monotonically increasing"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml", {"query": "Test sequence"}
        )

        assert result["returncode"] == 0
        events = result["events"]

        sequence_numbers = [e["metadata"]["sequenceNumber"] for e in events]

        # Check monotonic increase
        for i in range(1, len(sequence_numbers)):
            assert sequence_numbers[i] > sequence_numbers[i - 1], \
                f"Sequence numbers not monotonic: {sequence_numbers[i-1]} -> {sequence_numbers[i]}"

        # Check starts at 0
        assert sequence_numbers[0] == 0, f"First sequence number should be 0, got {sequence_numbers[0]}"

    def test_run_id_consistent_across_events(self):
        """All events in a run must have the same runId"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml", {"query": "Test runId"}
        )

        assert result["returncode"] == 0
        events = result["events"]

        run_ids = [e["metadata"]["runId"] for e in events]
        unique_run_ids = set(run_ids)

        assert len(unique_run_ids) == 1, f"Multiple runIds found: {unique_run_ids}"

    def test_timestamps_are_valid_iso8601(self):
        """All event timestamps must be valid ISO8601 format"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml", {"query": "Test timestamps"}
        )

        assert result["returncode"] == 0
        events = result["events"]

        for event in events:
            timestamp = event["metadata"]["timestamp"]
            # Basic ISO8601 format check
            assert "T" in timestamp, f"Invalid timestamp format: {timestamp}"
            assert "Z" in timestamp or "+" in timestamp or "-" in timestamp[-6:], \
                f"Timestamp missing timezone: {timestamp}"

    def test_run_end_contains_status(self):
        """run.end event must contain status field"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml", {"query": "Test status"}
        )

        assert result["returncode"] == 0
        events = result["events"]

        run_end_events = [e for e in events if e["spec"]["eventType"] == "run.end"]
        assert len(run_end_events) == 1, "Should have exactly one run.end event"

        run_end = run_end_events[0]
        assert "status" in run_end["spec"]["data"], "run.end missing status field"
        assert run_end["spec"]["data"]["status"] in ["success", "error"], \
            f"Invalid status: {run_end['spec']['data']['status']}"

    def test_tool_result_contains_metrics(self):
        """tool.result events should contain metrics"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml",
            {"query": "Calculate 5 + 5"}
        )

        assert result["returncode"] == 0
        events = result["events"]

        tool_result_events = [e for e in events if e["spec"]["eventType"] == "tool.result"]
        assert len(tool_result_events) > 0, "No tool.result events found"

        for tool_result in tool_result_events:
            # Should have metrics
            assert "metrics" in tool_result["spec"], "tool.result missing metrics"
            metrics = tool_result["spec"]["metrics"]
            assert "durationMs" in metrics, "tool.result metrics missing durationMs"

    def test_events_are_append_only(self):
        """Events file should be append-only (JSONL format)"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml", {"query": "Test JSONL"}
        )

        assert result["returncode"] == 0
        assert result["events_path"] is not None

        # Read raw file content
        with open(result["events_path"], "r") as f:
            lines = f.readlines()

        # Each line should be valid JSON
        for i, line in enumerate(lines):
            if line.strip():
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Line {i} is not valid JSON: {e}")

        # Number of lines should match number of events
        non_empty_lines = [l for l in lines if l.strip()]
        assert len(non_empty_lines) == len(result["events"]), \
            "Number of lines doesn't match number of events"
