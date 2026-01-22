"""
Contract tests for sample-agent

These tests verify:
1. Event sequence is correct
2. Required fields are present
3. Agent behavior is deterministic
"""

import pytest


def test_sample_agent_calculator(agent_runner):
    """Test sample-agent with calculator tool"""
    result = agent_runner(
        "agents/sample-agent/agent.yaml",
        {"query": "What is 5 + 3?"}
    )

    # Assert run succeeded
    assert result["status"] == "success", f"Run failed: {result['stderr']}"
    assert result["run_id"] is not None

    events = result["events"]
    assert len(events) > 0, "No events generated"

    # Verify event sequence
    event_types = [e["spec"]["eventType"] for e in events]

    # Expected sequence for calculator
    expected_sequence = [
        "run.start",
        "agent.start",
        "llm.request",
        "policy.allow",  # Policy check for calculator
        "tool.call",
        "tool.result",
        "llm.response",
        "agent.end",
        "run.end",
    ]

    assert event_types == expected_sequence, f"Event sequence mismatch: {event_types}"

    # Verify required fields in run.start
    run_start = events[0]
    assert run_start["apiVersion"] == "agent-os.dev/v1alpha1"
    assert run_start["kind"] == "RunEvent"
    assert "runId" in run_start["metadata"]
    assert "timestamp" in run_start["metadata"]
    assert "agentName" in run_start["metadata"]
    assert "sequenceNumber" in run_start["metadata"]
    assert run_start["spec"]["eventType"] == "run.start"
    assert "agent_name" in run_start["spec"]["data"]
    assert "input" in run_start["spec"]["data"]

    # Verify tool.call event
    tool_call = next(e for e in events if e["spec"]["eventType"] == "tool.call")
    assert tool_call["spec"]["data"]["tool_name"] == "calculator"
    assert "parameters" in tool_call["spec"]["data"]
    assert "config" in tool_call["spec"]["data"]

    # Verify tool.result event
    tool_result = next(e for e in events if e["spec"]["eventType"] == "tool.result")
    assert tool_result["spec"]["data"]["tool_name"] == "calculator"
    assert tool_result["spec"]["data"]["success"] is True
    assert "result" in tool_result["spec"]["data"]
    assert "metrics" in tool_result["spec"]
    assert "durationMs" in tool_result["spec"]["metrics"]

    # Verify run.end event
    run_end = events[-1]
    assert run_end["spec"]["eventType"] == "run.end"
    assert run_end["spec"]["data"]["status"] == "success"
    assert "output" in run_end["spec"]["data"]
    assert "metrics" in run_end["spec"]
    assert "durationMs" in run_end["spec"]["metrics"]
    assert "tokensUsed" in run_end["spec"]["metrics"]


def test_sample_agent_echo(agent_runner):
    """Test sample-agent with simple echo (no tools)"""
    result = agent_runner(
        "agents/sample-agent/agent.yaml",
        {"query": "Hello, Agent OS!"}
    )

    assert result["status"] == "success"
    events = result["events"]

    # Verify basic event sequence (no tool calls)
    event_types = [e["spec"]["eventType"] for e in events]

    expected_sequence = [
        "run.start",
        "agent.start",
        "llm.request",
        "llm.response",
        "agent.end",
        "run.end",
    ]

    assert event_types == expected_sequence

    # Verify sequence numbers are monotonic
    sequence_numbers = [e["metadata"]["sequenceNumber"] for e in events]
    assert sequence_numbers == list(range(len(events)))


def test_sample_agent_with_policy_deny(agent_runner):
    """Test sample-agent with policy that denies web-search"""
    result = agent_runner(
        "agents/sample-agent/agent-with-policy.yaml",
        {"query": "Can you search the web for Agent OS?"}
    )

    assert result["status"] == "success"
    events = result["events"]

    # Verify policy.deny event is present
    event_types = [e["spec"]["eventType"] for e in events]
    assert "policy.deny" in event_types, "Expected policy.deny event"

    # Verify tool was NOT executed
    assert "tool.call" not in event_types, "Tool should not be called when denied"

    # Verify policy.deny event structure
    policy_deny = next(e for e in events if e["spec"]["eventType"] == "policy.deny")
    assert policy_deny["spec"]["data"]["decision"] == "deny"
    assert policy_deny["spec"]["data"]["resource_type"] == "tool"
    assert policy_deny["spec"]["data"]["resource_name"] == "web-search"
    assert "reason" in policy_deny["spec"]["data"]


def test_event_metadata_consistency(agent_runner):
    """Test that all events have consistent metadata"""
    result = agent_runner(
        "agents/sample-agent/agent.yaml",
        {"query": "Test metadata"}
    )

    assert result["status"] == "success"
    events = result["events"]

    run_id = events[0]["metadata"]["runId"]
    agent_name = events[0]["metadata"]["agentName"]

    for event in events:
        # All events must have same runId
        assert event["metadata"]["runId"] == run_id

        # All events must have same agentName
        assert event["metadata"]["agentName"] == agent_name

        # All events must have required metadata fields
        assert "timestamp" in event["metadata"]
        assert "sequenceNumber" in event["metadata"]

        # All events must have required spec fields
        assert "eventType" in event["spec"]
        assert "data" in event["spec"]

        # All events must have correct apiVersion and kind
        assert event["apiVersion"] == "agent-os.dev/v1alpha1"
        assert event["kind"] == "RunEvent"
