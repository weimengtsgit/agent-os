"""
Iteration 1: Spec Validation Tests

Tests that verify the Spec-first architecture:
- Valid specs must pass validation
- Invalid specs must be rejected
- Schema validation is enforced before any execution
"""

import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.mark.spec_validation
class TestSpecValidation:
    """Test spec validation for agents, tools, and policies"""

    def test_valid_agent_spec_passes(self):
        """Valid agent spec should pass validation"""
        result = subprocess.run(
            ["agentctl", "validate", "agents/sample-agent/agent.yaml"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Valid spec failed: {result.stderr}"
        assert "Valid Agent spec" in result.stdout

    def test_valid_tool_spec_passes(self):
        """Valid tool spec should pass validation"""
        result = subprocess.run(
            ["agentctl", "validate", "agents/sample-agent/calculator.tool.yaml"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Valid tool spec failed: {result.stderr}"
        assert "Valid Tool spec" in result.stdout

    def test_valid_policy_spec_passes(self):
        """Valid policy spec should pass validation"""
        result = subprocess.run(
            [
                "agentctl",
                "validate",
                "agents/sample-agent/deny-web-search.policy.yaml",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Valid policy spec failed: {result.stderr}"
        assert "Valid Policy spec" in result.stdout

    def test_recursive_validation(self):
        """Recursive validation should validate all specs in directory"""
        result = subprocess.run(
            ["agentctl", "validate", "agents/sample-agent/", "--recursive"],
            capture_output=True,
            text=True,
        )

        # Note: May fail on .json input files, but should validate .yaml specs
        # Check that at least some specs were validated successfully
        assert result.stdout.count("Valid") >= 3, "Should validate multiple spec files"

        # Check that agent.yaml and tool specs passed
        assert "agent.yaml - Valid Agent spec" in result.stdout
        assert "calculator.tool.yaml - Valid Tool spec" in result.stdout

    def test_invalid_spec_rejected_missing_required_field(self):
        """Spec missing required fields should be rejected"""
        invalid_spec = """
apiVersion: agent-os.dev/v1alpha1
kind: Agent
metadata:
  name: invalid-agent
spec:
  # Missing required 'runtime' field
  description: "This agent is invalid"
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(invalid_spec)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["agentctl", "validate", temp_path],
                capture_output=True,
                text=True,
            )

            assert result.returncode != 0, "Invalid spec should fail validation"
            # Should mention validation error
            assert "validation" in result.stdout.lower() or "error" in result.stdout.lower()

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_invalid_spec_rejected_wrong_api_version(self):
        """Spec with wrong apiVersion should be rejected"""
        invalid_spec = """
apiVersion: wrong-version/v1
kind: Agent
metadata:
  name: invalid-agent
spec:
  runtime: agno
  description: "Wrong API version"
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(invalid_spec)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["agentctl", "validate", temp_path],
                capture_output=True,
                text=True,
            )

            assert result.returncode != 0, "Wrong apiVersion should fail validation"

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_invalid_spec_rejected_malformed_yaml(self):
        """Malformed YAML should be rejected"""
        invalid_spec = """
apiVersion: agent-os.dev/v1alpha1
kind: Agent
metadata:
  name: invalid-agent
  this is not valid yaml: [unclosed bracket
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(invalid_spec)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["agentctl", "validate", temp_path],
                capture_output=True,
                text=True,
            )

            assert result.returncode != 0, "Malformed YAML should fail validation"

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_nonexistent_file_rejected(self):
        """Validation of non-existent file should fail gracefully"""
        result = subprocess.run(
            ["agentctl", "validate", "nonexistent/path/to/spec.yaml"],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0, "Non-existent file should fail"
        assert "not found" in result.stdout.lower() or "not found" in result.stderr.lower()

    def test_testcase_generator_agent_valid(self):
        """Testcase generator agent spec should be valid"""
        result = subprocess.run(
            ["agentctl", "validate", "agents/testcase-generator/agent.yaml"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Testcase generator spec failed: {result.stderr}"
        assert "Valid Agent spec" in result.stdout

    def test_all_sample_agent_specs_valid(self):
        """All specs in sample-agent directory should be valid"""
        result = subprocess.run(
            ["agentctl", "validate", "agents/sample-agent/", "--recursive"],
            capture_output=True,
            text=True,
        )

        # Note: .json input files will fail validation (they're not specs)
        # Check that all .yaml spec files are valid
        assert "agent.yaml - Valid Agent spec" in result.stdout
        assert "calculator.tool.yaml - Valid Tool spec" in result.stdout
        assert "deny-web-search.policy.yaml - Valid Policy spec" in result.stdout

        # Check that multiple specs were validated
        valid_count = result.stdout.count("Valid")
        assert valid_count >= 5, f"Expected at least 5 valid specs, got {valid_count}"
