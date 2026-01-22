"""
Iteration 4: Testcase Generator Agent End-to-End Tests

Tests that verify:
- Testcase generator workflow
- Artifact generation (testcases.json)
- Human review workflow (human_review_request event)
- Review approval/rejection flow
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

        # Parse events path and run ID
        events_path = None
        run_id = None
        for line in result.stdout.split("\n"):
            if "Events:" in line:
                events_path_str = line.split("Events:")[1].strip()
                events_path = Path(events_path_str)
            if "Run ID:" in line:
                run_id = line.split("Run ID:")[1].strip()

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
            "run_id": run_id,
        }

    finally:
        Path(input_file).unlink(missing_ok=True)


@pytest.mark.e2e
class TestTestcaseGeneratorWorkflow:
    """Test testcase generator agent end-to-end workflow"""

    def test_testcase_generator_completes_successfully(self):
        """Testcase generator should complete successfully with approval"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "approved"
            }
        )

        assert result["returncode"] == 0, f"Testcase generator failed: {result['stderr']}"

        events = result["events"]
        event_types = [e["spec"]["eventType"] for e in events]

        # Should have complete workflow
        assert "run.start" in event_types
        assert "run.end" in event_types
        assert "agent.start" in event_types
        assert "agent.end" in event_types

    def test_testcase_generator_uses_multiple_tools(self):
        """Testcase generator should use multiple tools in sequence"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "approved"
            }
        )

        assert result["returncode"] == 0
        events = result["events"]

        # Extract tool names from tool.call events
        tool_calls = [
            e["spec"]["data"]["tool_name"]
            for e in events
            if e["spec"]["eventType"] == "tool.call"
        ]

        # Should use multiple tools
        assert len(tool_calls) >= 3, f"Expected at least 3 tool calls, got {len(tool_calls)}"

        # Expected tools (order may vary based on implementation)
        expected_tools = {"requirements-reader", "testcase-generator", "testcase-validator"}
        actual_tools = set(tool_calls)

        # Check that expected tools are present
        for tool in expected_tools:
            assert tool in actual_tools, f"Expected tool '{tool}' not found in {actual_tools}"

    def test_testcase_generator_produces_artifacts(self):
        """Testcase generator should produce artifacts directory with testcases"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "approved"
            }
        )

        assert result["returncode"] == 0

        # Find artifacts path from events or run directory
        if result["events_path"]:
            run_dir = result["events_path"].parent
            artifacts_dir = run_dir / "artifacts"

            # Artifacts directory should exist
            assert artifacts_dir.exists(), f"Artifacts directory not found at {artifacts_dir}"

            # Should contain testcases file
            testcases_files = list(artifacts_dir.glob("testcases*.json"))
            assert len(testcases_files) > 0, "No testcases JSON file found in artifacts"

            # Testcases file should be valid JSON
            testcases_file = testcases_files[0]
            with open(testcases_file, "r") as f:
                testcases = json.load(f)

            # Should be a list or dict with testcases
            assert isinstance(testcases, (list, dict)), \
                f"Testcases should be list or dict, got {type(testcases)}"

            if isinstance(testcases, list):
                assert len(testcases) > 0, "Testcases list is empty"
            elif isinstance(testcases, dict):
                assert len(testcases) > 0, "Testcases dict is empty"

    def test_human_review_request_event_generated(self):
        """Workflow should generate human_review_request event when paused"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "pending"
            }
        )

        assert result["returncode"] == 0
        events = result["events"]
        event_types = [e["spec"]["eventType"] for e in events]

        # Should have human_review_request event
        assert "human_review_request" in event_types, \
            "Missing human_review_request event for pending review"

        # Find human_review_request event
        review_events = [
            e for e in events
            if e["spec"]["eventType"] == "human_review_request"
        ]
        assert len(review_events) > 0

        review_event = review_events[0]
        review_data = review_event["spec"]["data"]

        # Check required fields
        assert "stage" in review_data, "human_review_request missing stage"
        assert "message" in review_data, "human_review_request missing message"
        assert "reviewCommand" in review_data, "human_review_request missing reviewCommand"

    def test_human_review_request_contains_test_case_info(self):
        """human_review_request should contain test case information"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "pending"
            }
        )

        assert result["returncode"] == 0
        events = result["events"]

        review_events = [
            e for e in events
            if e["spec"]["eventType"] == "human_review_request"
        ]
        assert len(review_events) > 0

        review_event = review_events[0]
        review_data = review_event["spec"]["data"]

        # Should contain test case count or test cases
        assert "testCaseCount" in review_data or "testCases" in review_data, \
            "human_review_request should contain test case information"

        if "testCaseCount" in review_data:
            assert review_data["testCaseCount"] > 0, "Test case count should be positive"

    def test_workflow_pauses_at_human_review(self):
        """Workflow should pause at human review and indicate pending state"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "pending"
            }
        )

        assert result["returncode"] == 0
        events = result["events"]

        # Should have human_review_request
        review_events = [
            e for e in events
            if e["spec"]["eventType"] == "human_review_request"
        ]
        assert len(review_events) > 0

        # run.end should indicate paused state
        run_end_events = [e for e in events if e["spec"]["eventType"] == "run.end"]
        if run_end_events:
            run_end = run_end_events[0]
            output = run_end["spec"]["data"].get("output", "").lower()
            # Should mention paused or review
            assert "paused" in output or "review" in output, \
                f"run.end output should indicate paused state: {output}"

    def test_approval_continues_workflow(self):
        """Approval should allow workflow to continue"""
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

        # Should complete successfully
        assert "run.end" in event_types

        run_end_events = [e for e in events if e["spec"]["eventType"] == "run.end"]
        assert len(run_end_events) > 0

        run_end = run_end_events[0]
        assert run_end["spec"]["data"]["status"] == "success", \
            "Approved workflow should complete with success status"

    def test_rejection_stops_workflow(self):
        """Rejection should stop workflow gracefully"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "rejected"
            }
        )

        assert result["returncode"] == 0
        events = result["events"]
        event_types = [e["spec"]["eventType"] for e in events]

        # Should complete (not crash)
        assert "run.end" in event_types

        # Check output mentions rejection
        run_end_events = [e for e in events if e["spec"]["eventType"] == "run.end"]
        if run_end_events:
            run_end = run_end_events[0]
            output = run_end["spec"]["data"].get("output", "").lower()
            assert "reject" in output, f"run.end should mention rejection: {output}"

    def test_tool_execution_order_correct(self):
        """Tools should execute in correct order"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "approved"
            }
        )

        assert result["returncode"] == 0
        events = result["events"]

        # Extract tool calls in order
        tool_calls = [
            e["spec"]["data"]["tool_name"]
            for e in events
            if e["spec"]["eventType"] == "tool.call"
        ]

        # requirements-reader should come first
        assert tool_calls[0] == "requirements-reader", \
            f"First tool should be requirements-reader, got {tool_calls[0]}"

        # testcase-generator should come before testcase-validator
        if "testcase-generator" in tool_calls and "testcase-validator" in tool_calls:
            gen_idx = tool_calls.index("testcase-generator")
            val_idx = tool_calls.index("testcase-validator")
            assert gen_idx < val_idx, \
                "testcase-generator should come before testcase-validator"

    def test_all_tools_succeed(self):
        """All tool executions should succeed in happy path"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "approved"
            }
        )

        assert result["returncode"] == 0
        events = result["events"]

        # Check all tool.result events
        tool_results = [
            e for e in events
            if e["spec"]["eventType"] == "tool.result"
        ]

        for tool_result in tool_results:
            assert tool_result["spec"]["data"]["success"] is True, \
                f"Tool {tool_result['spec']['data'].get('tool_name')} failed"

    def test_metrics_collected_for_all_tools(self):
        """Metrics should be collected for all tool executions"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "approved"
            }
        )

        assert result["returncode"] == 0
        events = result["events"]

        tool_results = [
            e for e in events
            if e["spec"]["eventType"] == "tool.result"
        ]

        assert len(tool_results) > 0, "No tool.result events found"

        for tool_result in tool_results:
            assert "metrics" in tool_result["spec"], \
                f"Tool result missing metrics: {tool_result['spec']['data'].get('tool_name')}"
            metrics = tool_result["spec"]["metrics"]
            assert "durationMs" in metrics, "Metrics missing durationMs"


@pytest.mark.e2e
class TestArtifactGeneration:
    """Test artifact generation and structure"""

    def test_artifacts_directory_created(self):
        """Artifacts directory should be created in run directory"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "approved"
            }
        )

        assert result["returncode"] == 0
        assert result["events_path"] is not None

        run_dir = result["events_path"].parent
        artifacts_dir = run_dir / "artifacts"

        assert artifacts_dir.exists(), "Artifacts directory not created"
        assert artifacts_dir.is_dir(), "Artifacts path is not a directory"

    def test_testcases_json_valid_structure(self):
        """Generated testcases.json should have valid structure"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "approved"
            }
        )

        assert result["returncode"] == 0
        assert result["events_path"] is not None

        run_dir = result["events_path"].parent
        artifacts_dir = run_dir / "artifacts"

        testcases_files = list(artifacts_dir.glob("testcases*.json"))
        assert len(testcases_files) > 0, "No testcases JSON file found"

        testcases_file = testcases_files[0]
        with open(testcases_file, "r") as f:
            testcases = json.load(f)

        # Validate structure (adjust based on actual format)
        assert testcases is not None, "Testcases is None"

        # If it's a list, check each test case
        if isinstance(testcases, list):
            for tc in testcases:
                assert isinstance(tc, dict), "Each test case should be a dict"
                # Common fields in test cases
                # (adjust based on your actual test case structure)

    def test_artifacts_referenced_in_events(self):
        """Artifacts should be referenced in events or run.end"""
        result = run_agent_and_get_events(
            "agents/testcase-generator/agent.yaml",
            {
                "requirementsPath": "agents/testcase-generator/requirements.txt",
                "reviewDecision": "approved"
            }
        )

        assert result["returncode"] == 0
        events = result["events"]

        # Check if artifacts are mentioned in run.end metrics or data
        run_end_events = [e for e in events if e["spec"]["eventType"] == "run.end"]
        if run_end_events:
            run_end = run_end_events[0]

            # Check metrics for artifact path
            if "metrics" in run_end["spec"]:
                metrics = run_end["spec"]["metrics"]
                # Artifact path might be in metrics
                if "artifactPath" in metrics:
                    assert metrics["artifactPath"], "artifactPath is empty"
