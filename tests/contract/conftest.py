"""
Pytest configuration and fixtures for contract tests
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any

import pytest


@pytest.fixture
def temp_runs_dir(tmp_path, monkeypatch):
    """Create temporary runs directory"""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    return runs_dir


def run_agent(agent_path: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run an agent and return the result with events.

    Returns:
        {
            "run_id": str,
            "status": str,
            "output": str,
            "events": List[Dict],
            "events_path": Path,
        }
    """
    # Find repo root (where agents/ directory exists)
    repo_root = Path(__file__).parent.parent.parent

    # Create temporary input file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(input_data, f)
        input_file = f.name

    try:
        # Run agent from repo root
        cmd = [
            "agentctl",
            "run-local",
            agent_path,
            "--input",
            input_file,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(repo_root),
        )

        # Parse output to get run ID and events path
        output_lines = result.stdout.split("\n")
        run_id = None
        events_path = None

        for line in output_lines:
            if "Run ID:" in line:
                run_id = line.split("Run ID:")[1].strip()
            elif "Events:" in line:
                events_path_str = line.split("Events:")[1].strip()
                # Make path absolute relative to repo root
                events_path = repo_root / events_path_str

        # Load events
        events = []
        if events_path and events_path.exists():
            with open(events_path, "r") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))

        return {
            "run_id": run_id,
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout,
            "stderr": result.stderr,
            "events": events,
            "events_path": events_path,
            "returncode": result.returncode,
        }

    finally:
        # Cleanup
        Path(input_file).unlink(missing_ok=True)


@pytest.fixture
def agent_runner():
    """Fixture that provides agent runner function"""
    return run_agent
