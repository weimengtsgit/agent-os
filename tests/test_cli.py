"""Test basic CLI functionality."""

import pytest
from click.testing import CliRunner
from platform_core.cli.main import cli


def test_cli_help():
    """Test that CLI help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Agent OS CLI" in result.output


def test_validate_sample_agent():
    """Test validating the sample agent."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["validate", "agents/sample-agent/agent.json", "--type", "agent"]
    )
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_sample_tool():
    """Test validating the sample tool."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["validate", "agents/sample-agent/tools/echo-tool.json", "--type", "tool"]
    )
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_sample_policy():
    """Test validating the sample policy."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["validate", "agents/sample-agent/policies/basic-policy.json", "--type", "policy"],
    )
    assert result.exit_code == 0
    assert "valid" in result.output.lower()
