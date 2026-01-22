"""
Contract tests for testcase-generator agent

These tests verify:
1. Workflow execution sequence
2. Human review workflow
3. Artifact generation
"""

import json
from pathlib import Path

import pytest


def test_testcase_generator_workflow(agent_runner):
    """Test testcase-generator complete workflow"""
    result = agent_runner(
        "agents/testcase-generator/agent.yaml",
        {
            "requirementsPath": "agents/testcase-generator/requirements.txt",
            "reviewDecision": "pending"
        }
    )

    assert result["status"] == "success"
    events = result["events"]

    # Verify event sequence up to human review
    event_types = [e["spec"]["eventType"] for e in events]

    expected_sequence = [
        "run.start",
        "agent.start",
        "tool.call",      # requirements-reader
        "tool.result",
        "tool.call",      # testcase-generator
        "tool.result",
        "tool.call",      # testcase-validator
        "tool.result",
        "human_review_request",  # Workflow pauses here
        "agent.end",
        "run.end",
    ]

    assert event_types == expected_sequence, f"Event sequence mismatch: {event_types}"

    # Verify human_review_request event
    review_event = next(e for e in events if e["spec"]["eventType"] == "human_review_request")
    assert review_event["spec"]["data"]["stage"] == "after-generation"
    assert "testCaseCount" in review_event["spec"]["data"]
    assert "testCases" in review_event["spec"]["data"]
    assert "message" in review_event["spec"]["data"]
    assert "reviewCommand" in review_event["spec"]["data"]

    # Verify test cases were generated
    test_case_count = review_event["spec"]["data"]["testCaseCount"]
    assert test_case_count > 0, "No test cases generated"

    # Verify run.end indicates paused for review
    run_end = events[-1]
    assert "paused" in run_end["spec"]["data"]["output"].lower()


def test_testcase_generator_with_approval(agent_runner):
    """Test testcase-generator with approved review decision"""
    result = agent_runner(
        "agents/testcase-generator/agent.yaml",
        {
            "requirementsPath": "agents/testcase-generator/requirements.txt",
            "reviewDecision": "approved"
        }
    )

    assert result["status"] == "success"
    events = result["events"]

    # Verify complete workflow with approval
    event_types = [e["spec"]["eventType"] for e in events]

    # Should include human_review_response and testcase-writer
    assert "human_review_request" in event_types
    assert "human_review_response" in event_types

    # Verify human_review_response
    review_response = next(e for e in events if e["spec"]["eventType"] == "human_review_response")
    assert review_response["spec"]["data"]["decision"] == "approved"

    # Verify testcase-writer was called
    tool_calls = [e for e in events if e["spec"]["eventType"] == "tool.call"]
    tool_names = [tc["spec"]["data"]["tool_name"] for tc in tool_calls]
    assert "testcase-writer" in tool_names

    # Verify artifacts were written
    run_end = events[-1]
    assert "metrics" in run_end["spec"]
    assert "artifactPath" in run_end["spec"]["metrics"]

    artifact_path = Path(run_end["spec"]["metrics"]["artifactPath"])
    assert artifact_path.exists(), f"Artifact not found: {artifact_path}"

    # Verify artifact content
    with open(artifact_path, "r") as f:
        test_cases = json.load(f)

    assert isinstance(test_cases, list)
    assert len(test_cases) > 0

    # Verify test case structure
    for tc in test_cases:
        assert "id" in tc
        assert "title" in tc
        assert "description" in tc
        assert "steps" in tc
        assert "expectedResult" in tc


def test_testcase_generator_with_rejection(agent_runner):
    """Test testcase-generator with rejected review decision"""
    result = agent_runner(
        "agents/testcase-generator/agent.yaml",
        {
            "requirementsPath": "agents/testcase-generator/requirements.txt",
            "reviewDecision": "rejected"
        }
    )

    assert result["status"] == "success"
    events = result["events"]

    # Verify workflow stops after rejection
    event_types = [e["spec"]["eventType"] for e in events]

    assert "human_review_request" in event_types
    assert "human_review_response" in event_types

    # Verify human_review_response shows rejection
    review_response = next(e for e in events if e["spec"]["eventType"] == "human_review_response")
    assert review_response["spec"]["data"]["decision"] == "rejected"

    # Verify testcase-writer was NOT called
    tool_calls = [e for e in events if e["spec"]["eventType"] == "tool.call"]
    tool_names = [tc["spec"]["data"]["tool_name"] for tc in tool_calls]
    assert "testcase-writer" not in tool_names

    # Verify run.end indicates rejection
    run_end = events[-1]
    assert "rejected" in run_end["spec"]["data"]["output"].lower()


def test_tool_execution_order(agent_runner):
    """Test that tools execute in correct order"""
    result = agent_runner(
        "agents/testcase-generator/agent.yaml",
        {
            "requirementsPath": "agents/testcase-generator/requirements.txt",
            "reviewDecision": "approved"
        }
    )

    assert result["status"] == "success"
    events = result["events"]

    # Extract tool calls in order
    tool_calls = [
        e["spec"]["data"]["tool_name"]
        for e in events
        if e["spec"]["eventType"] == "tool.call"
    ]

    # Verify order
    expected_order = [
        "requirements-reader",
        "testcase-generator",
        "testcase-validator",
        "testcase-writer",
    ]

    assert tool_calls == expected_order, f"Tool execution order mismatch: {tool_calls}"


def test_all_tools_have_metrics(agent_runner):
    """Test that all tool.result events have metrics"""
    result = agent_runner(
        "agents/testcase-generator/agent.yaml",
        {
            "requirementsPath": "agents/testcase-generator/requirements.txt",
            "reviewDecision": "approved"
        }
    )

    assert result["status"] == "success"
    events = result["events"]

    tool_results = [e for e in events if e["spec"]["eventType"] == "tool.result"]

    for tool_result in tool_results:
        assert "metrics" in tool_result["spec"], f"Missing metrics in {tool_result['spec']['data']['tool_name']}"
        assert "durationMs" in tool_result["spec"]["metrics"]
        assert tool_result["spec"]["metrics"]["durationMs"] > 0
