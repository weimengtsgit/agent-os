"""
Iteration 3: Tool Executor and Policy Engine Stability Tests

Tests that verify:
- Tool timeout handling
- Tool retry mechanism
- Policy enforcement (allow/deny)
- System stability under error conditions
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest


def run_agent_and_get_events(
    agent_path: str, input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Run an agent and return events."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(input_data, f)
        input_file = f.name

    try:
        result = subprocess.run(
            ["agentctl", "run-local", agent_path, "--input", input_file],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Parse events path
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


@pytest.mark.stability
class TestPolicyEngine:
    """Test policy enforcement"""

    def test_policy_allow_event_generated(self):
        """Policy allow decision should generate policy.allow event"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml",
            {"query": "Use calculator to compute 3 + 3"}
        )

        assert result["returncode"] == 0
        events = result["events"]
        event_types = [e["spec"]["eventType"] for e in events]

        # Should have policy.allow event
        assert "policy.allow" in event_types, "Missing policy.allow event"

        # Find policy.allow event
        policy_allow_events = [e for e in events if e["spec"]["eventType"] == "policy.allow"]
        assert len(policy_allow_events) > 0

        # Check policy.allow event structure
        policy_event = policy_allow_events[0]
        assert "decision" in policy_event["spec"]["data"]
        assert policy_event["spec"]["data"]["decision"] == "allow"

    def test_policy_deny_blocks_tool_execution(self):
        """Policy deny should block tool execution and generate policy.deny event"""
        # Use agent with deny policy
        result = run_agent_and_get_events(
            "agents/sample-agent/agent-with-policy.yaml",
            {"query": "Search the web for Agent OS"}
        )

        # Run should complete (not crash)
        assert result["returncode"] == 0, f"Run crashed: {result['stderr']}"

        events = result["events"]
        event_types = [e["spec"]["eventType"] for e in events]

        # Should have policy.deny event
        assert "policy.deny" in event_types, "Missing policy.deny event when policy should deny"

        # Find policy.deny event
        policy_deny_events = [e for e in events if e["spec"]["eventType"] == "policy.deny"]
        assert len(policy_deny_events) > 0

        # Check policy.deny event structure
        policy_event = policy_deny_events[0]
        assert "decision" in policy_event["spec"]["data"]
        assert policy_event["spec"]["data"]["decision"] == "deny"
        assert "reason" in policy_event["spec"]["data"], "policy.deny should include reason"

        # Tool should NOT execute after deny
        # Find index of policy.deny
        deny_index = event_types.index("policy.deny")

        # Check if there's a tool.call after the deny for the same tool
        denied_tool = policy_event["spec"]["data"].get("resource_name")
        if denied_tool:
            for i in range(deny_index + 1, len(events)):
                if events[i]["spec"]["eventType"] == "tool.call":
                    tool_name = events[i]["spec"]["data"].get("tool_name")
                    assert tool_name != denied_tool, \
                        f"Tool {denied_tool} executed after policy.deny"

    def test_policy_deny_does_not_crash_agent(self):
        """Agent should handle policy denial gracefully without crashing"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent-with-policy.yaml",
            {"query": "Can you search the web?"}
        )

        # Should complete successfully even with denial
        assert result["returncode"] == 0, "Agent crashed on policy denial"

        events = result["events"]
        event_types = [e["spec"]["eventType"] for e in events]

        # Should have proper lifecycle
        assert "run.start" in event_types
        assert "run.end" in event_types or "run.error" in event_types
        assert "agent.start" in event_types
        assert "agent.end" in event_types


@pytest.mark.stability
class TestToolExecutorStability:
    """Test tool executor stability and error handling"""

    def test_tool_execution_success_recorded(self):
        """Successful tool execution should be recorded in tool.result"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml",
            {"query": "Calculate 7 + 8"}
        )

        assert result["returncode"] == 0
        events = result["events"]

        tool_result_events = [e for e in events if e["spec"]["eventType"] == "tool.result"]
        assert len(tool_result_events) > 0, "No tool.result events found"

        # Check success field
        for tool_result in tool_result_events:
            assert "success" in tool_result["spec"]["data"], "tool.result missing success field"
            # For calculator, should succeed
            if tool_result["spec"]["data"].get("tool_name") == "calculator":
                assert tool_result["spec"]["data"]["success"] is True

    def test_tool_result_has_attempt_number(self):
        """tool.result should include attempt number for retry tracking"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml",
            {"query": "Use calculator for 9 + 1"}
        )

        assert result["returncode"] == 0
        events = result["events"]

        tool_result_events = [e for e in events if e["spec"]["eventType"] == "tool.result"]
        assert len(tool_result_events) > 0

        for tool_result in tool_result_events:
            assert "attempt" in tool_result["spec"]["data"], \
                "tool.result missing attempt field for retry tracking"
            # First attempt should be 0
            attempt = tool_result["spec"]["data"]["attempt"]
            assert isinstance(attempt, int), f"attempt should be int, got {type(attempt)}"
            assert attempt >= 0, f"attempt should be >= 0, got {attempt}"

    def test_tool_call_has_timeout_config(self):
        """tool.call should include timeout configuration"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml",
            {"query": "Calculate 100 + 200"}
        )

        assert result["returncode"] == 0
        events = result["events"]

        tool_call_events = [e for e in events if e["spec"]["eventType"] == "tool.call"]
        assert len(tool_call_events) > 0

        for tool_call in tool_call_events:
            assert "config" in tool_call["spec"]["data"], "tool.call missing config"
            config = tool_call["spec"]["data"]["config"]
            assert "timeoutMs" in config, "tool.call config missing timeoutMs"
            assert isinstance(config["timeoutMs"], (int, float)), \
                "timeoutMs should be numeric"
            assert config["timeoutMs"] > 0, "timeoutMs should be positive"

    def test_tool_call_has_retry_config(self):
        """tool.call should include retry configuration"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml",
            {"query": "Calculate 50 + 50"}
        )

        assert result["returncode"] == 0
        events = result["events"]

        tool_call_events = [e for e in events if e["spec"]["eventType"] == "tool.call"]
        assert len(tool_call_events) > 0

        for tool_call in tool_call_events:
            assert "config" in tool_call["spec"]["data"], "tool.call missing config"
            config = tool_call["spec"]["data"]["config"]
            assert "maxRetries" in config, "tool.call config missing maxRetries"
            assert isinstance(config["maxRetries"], int), "maxRetries should be int"
            assert config["maxRetries"] >= 0, "maxRetries should be >= 0"

    def test_tool_result_includes_duration_metric(self):
        """tool.result should include execution duration metric"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml",
            {"query": "Calculate 25 + 25"}
        )

        assert result["returncode"] == 0
        events = result["events"]

        tool_result_events = [e for e in events if e["spec"]["eventType"] == "tool.result"]
        assert len(tool_result_events) > 0

        for tool_result in tool_result_events:
            assert "metrics" in tool_result["spec"], "tool.result missing metrics"
            metrics = tool_result["spec"]["metrics"]
            assert "durationMs" in metrics, "tool.result metrics missing durationMs"
            assert isinstance(metrics["durationMs"], (int, float)), \
                "durationMs should be numeric"
            assert metrics["durationMs"] >= 0, "durationMs should be non-negative"

    def test_multiple_tools_execute_in_sequence(self):
        """Multiple tool calls should execute in proper sequence"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "approved"
            }
        )

        assert result["returncode"] == 0
        events = result["events"]
        event_types = [e["spec"]["eventType"] for e in events]

        # Should have multiple tool.call and tool.result events
        tool_call_count = event_types.count("tool.call")
        tool_result_count = event_types.count("tool.result")

        assert tool_call_count > 1, "Should have multiple tool calls"
        assert tool_call_count == tool_result_count, \
            f"Mismatched tool.call ({tool_call_count}) and tool.result ({tool_result_count})"

        # Each tool.call should be followed by tool.result before next tool.call
        tool_call_indices = [i for i, t in enumerate(event_types) if t == "tool.call"]
        tool_result_indices = [i for i, t in enumerate(event_types) if t == "tool.result"]

        for i in range(len(tool_call_indices)):
            call_idx = tool_call_indices[i]
            result_idx = tool_result_indices[i]
            assert result_idx > call_idx, \
                f"tool.result at {result_idx} should come after tool.call at {call_idx}"

            # If there's a next tool.call, it should come after this tool.result
            if i < len(tool_call_indices) - 1:
                next_call_idx = tool_call_indices[i + 1]
                assert next_call_idx > result_idx, \
                    f"Next tool.call at {next_call_idx} should come after tool.result at {result_idx}"


@pytest.mark.stability
class TestSystemStability:
    """Test overall system stability"""

    def test_agent_completes_without_crash(self):
        """Agent should complete without crashing"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml",
            {"query": "Hello, test stability"}
        )

        # Should not crash
        assert result["returncode"] == 0, f"Agent crashed: {result['stderr']}"

        events = result["events"]
        event_types = [e["spec"]["eventType"] for e in events]

        # Should have complete lifecycle
        assert "run.start" in event_types
        assert "run.end" in event_types or "run.error" in event_types

    def test_events_file_always_created(self):
        """events.jsonl should always be created, even on errors"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml",
            {"query": "Test events file creation"}
        )

        # Events file should exist
        assert result["events_path"] is not None, "No events path found"
        assert result["events_path"].exists(), "events.jsonl not created"

    def test_run_end_always_present(self):
        """run.end or run.error should always be the last event"""
        result = run_agent_and_get_events(
            "agents/sample-agent/agent.yaml",
            {"query": "Test run completion"}
        )

        events = result["events"]
        assert len(events) > 0, "No events generated"

        last_event = events[-1]
        last_event_type = last_event["spec"]["eventType"]

        assert last_event_type in ["run.end", "run.error"], \
            f"Last event should be run.end or run.error, got {last_event_type}"
