"""
Agent OS Console - Flask Application

Provides web UI for:
- Listing all runs
- Viewing run details (events + artifacts)
- Human review workflow (approve/reject)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = "agent-os-console-secret-key-change-in-production"

RUNS_DIR = Path("runs")


def load_run_events(run_id: str) -> List[Dict[str, Any]]:
    """Load events from events.jsonl file"""
    events = []
    run_dir = RUNS_DIR / run_id

    # Try both events.jsonl and events_continued.jsonl
    for events_file in ["events.jsonl", "events_continued.jsonl"]:
        events_path = run_dir / events_file
        if events_path.exists():
            with open(events_path, "r") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))

    return events


def get_run_summary(run_id: str) -> Optional[Dict[str, Any]]:
    """Get summary information for a run"""
    events = load_run_events(run_id)
    if not events:
        return None

    # Extract key information
    start_event = next((e for e in events if e["spec"]["eventType"] == "run.start"), None)
    end_event = next((e for e in events if e["spec"]["eventType"] == "run.end"), None)
    review_event = next((e for e in events if e["spec"]["eventType"] == "human_review_request"), None)

    summary = {
        "run_id": run_id,
        "agent_name": events[0]["metadata"]["agentName"] if events else "unknown",
        "status": "completed" if end_event else "running",
        "start_time": start_event["metadata"]["timestamp"] if start_event else None,
        "end_time": end_event["metadata"]["timestamp"] if end_event else None,
        "event_count": len(events),
        "has_review_request": review_event is not None,
        "review_pending": review_event is not None and not any(
            e["spec"]["eventType"] == "human_review_response" for e in events
        ),
    }

    # Check for artifacts
    artifacts_dir = RUNS_DIR / run_id / "artifacts"
    if artifacts_dir.exists():
        summary["artifacts"] = [f.name for f in artifacts_dir.iterdir() if f.is_file()]
    else:
        summary["artifacts"] = []

    return summary


def list_all_runs() -> List[Dict[str, Any]]:
    """List all runs in the runs directory"""
    if not RUNS_DIR.exists():
        return []

    runs = []
    for run_dir in RUNS_DIR.iterdir():
        if run_dir.is_dir() and run_dir.name.startswith("run-"):
            summary = get_run_summary(run_dir.name)
            if summary:
                runs.append(summary)

    # Sort by start time (newest first)
    runs.sort(key=lambda x: x.get("start_time", ""), reverse=True)
    return runs


@app.route("/")
def index():
    """Redirect to runs list"""
    return redirect(url_for("runs"))


@app.route("/runs")
def runs():
    """List all runs"""
    all_runs = list_all_runs()
    return render_template("runs.html", runs=all_runs)


@app.route("/runs/<run_id>")
def run_detail(run_id: str):
    """Show detailed view of a specific run"""
    summary = get_run_summary(run_id)
    if not summary:
        flash(f"Run {run_id} not found", "error")
        return redirect(url_for("runs"))

    events = load_run_events(run_id)

    # Load artifacts
    artifacts = {}
    artifacts_dir = RUNS_DIR / run_id / "artifacts"
    if artifacts_dir.exists():
        for artifact_file in artifacts_dir.iterdir():
            if artifact_file.is_file():
                try:
                    with open(artifact_file, "r") as f:
                        if artifact_file.suffix == ".json":
                            artifacts[artifact_file.name] = json.load(f)
                        else:
                            artifacts[artifact_file.name] = f.read()
                except Exception as e:
                    artifacts[artifact_file.name] = f"Error loading: {e}"

    return render_template(
        "run_detail.html",
        summary=summary,
        events=events,
        artifacts=artifacts,
    )


@app.route("/runs/<run_id>/review", methods=["POST"])
def review_run(run_id: str):
    """Approve or reject a run"""
    decision = request.form.get("decision")

    if decision not in ["approve", "reject"]:
        flash("Invalid decision", "error")
        return redirect(url_for("run_detail", run_id=run_id))

    # Execute agentctl review command
    import subprocess

    try:
        cmd = ["agentctl", "review", run_id, f"--{decision}"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            flash(f"Run {decision}d successfully", "success")
        else:
            flash(f"Review failed: {result.stderr}", "error")
    except Exception as e:
        flash(f"Error executing review: {e}", "error")

    return redirect(url_for("run_detail", run_id=run_id))


@app.route("/api/runs")
def api_runs():
    """API endpoint for runs list"""
    all_runs = list_all_runs()
    return jsonify(all_runs)


@app.route("/api/runs/<run_id>")
def api_run_detail(run_id: str):
    """API endpoint for run detail"""
    summary = get_run_summary(run_id)
    if not summary:
        return jsonify({"error": "Run not found"}), 404

    events = load_run_events(run_id)
    return jsonify({
        "summary": summary,
        "events": events,
    })


@app.template_filter("format_timestamp")
def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp for display"""
    if not timestamp:
        return "N/A"
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return timestamp


@app.template_filter("format_json")
def format_json(data: Any) -> str:
    """Format JSON data for display"""
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
