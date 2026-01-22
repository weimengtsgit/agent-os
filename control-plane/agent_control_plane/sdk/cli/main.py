"""
agentctl - Agent OS Control Plane CLI

Main command-line interface for Agent OS operations.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agent_control_plane.specs import validator

app = typer.Typer(
    name="agentctl",
    help="Agent OS Control Plane CLI - Manage agents, tools, and policies",
    add_completion=False,
)

console = Console()


@app.command()
def validate(
    path: str = typer.Argument(..., help="Path to spec file or directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r", help="Recursively validate directories"),
):
    """
    Validate agent/tool/policy specs against JSON Schema.

    Examples:
        agentctl validate agents/sample-agent/agent.yaml
        agentctl validate agents/sample-agent/
        agentctl validate agents/ --recursive
    """
    path_obj = Path(path)

    if not path_obj.exists():
        console.print(f"[red]✗ Path not found: {path}[/red]")
        sys.exit(1)

    try:
        if path_obj.is_file():
            # Validate single file
            success = validator.validate_file(path_obj, verbose=verbose)
            sys.exit(0 if success else 1)
        elif path_obj.is_dir():
            # Validate directory
            valid_count, total_count = validator.validate_dir(
                path_obj, recursive=recursive, verbose=verbose
            )
            sys.exit(0 if valid_count == total_count else 1)
        else:
            console.print(f"[red]✗ Invalid path: {path}[/red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Validation error: {e}[/red]")
        sys.exit(1)


@app.command()
def run_local(
    agent_path: str = typer.Argument(..., help="Path to agent spec file or directory"),
    input_file: Optional[str] = typer.Option(None, "--input", "-i", help="Path to input JSON file"),
    input_json: Optional[str] = typer.Option(None, "--input-json", "-j", help="Input data as JSON string"),
    runtime: str = typer.Option("agno", "--runtime", "-r", help="Runtime to use (default: agno)"),
    output_dir: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory for events (default: runs/<run-id>)"),
):
    """
    Run an agent locally using specified runtime.

    Examples:
        agentctl run-local agents/sample-agent/agent.yaml --input input.json
        agentctl run-local agents/sample-agent/agent.yaml --input-json '{"query": "hello"}'
        agentctl run-local agents/sample-agent/ --input input.json --runtime agno
    """
    import json
    import yaml
    from pathlib import Path
    from agent_control_plane.specs import validator
    from agent_control_plane.pal import FileEventSink, NoOpTraceSink, NoOpPolicyEngine, RuntimeRegistry

    # Resolve agent spec path
    agent_path_obj = Path(agent_path)
    if not agent_path_obj.exists():
        console.print(f"[red]✗ Agent path not found: {agent_path}[/red]")
        sys.exit(1)

    # Find agent.yaml
    if agent_path_obj.is_file():
        agent_spec_path = agent_path_obj
    elif agent_path_obj.is_dir():
        agent_spec_path = agent_path_obj / "agent.yaml"
        if not agent_spec_path.exists():
            console.print(f"[red]✗ agent.yaml not found in: {agent_path}[/red]")
            sys.exit(1)
    else:
        console.print(f"[red]✗ Invalid agent path: {agent_path}[/red]")
        sys.exit(1)

    console.print(f"[yellow]Running agent: {agent_spec_path}[/yellow]")

    # Load and validate agent spec
    try:
        with open(agent_spec_path, "r") as f:
            agent_spec = yaml.safe_load(f)

        # Validate spec
        is_valid, errors = validator.validate_spec(agent_spec, path=str(agent_spec_path))
        if not is_valid:
            console.print(f"[red]✗ Agent spec validation failed:[/red]")
            for error in errors:
                console.print(f"  [red]→ {error}[/red]")
            sys.exit(1)

        console.print(f"[green]✓[/green] Agent spec validated")
    except Exception as e:
        console.print(f"[red]✗ Failed to load agent spec: {e}[/red]")
        sys.exit(1)

    # Load input data
    input_data = {}
    if input_file:
        try:
            with open(input_file, "r") as f:
                input_data = json.load(f)
            console.print(f"[green]✓[/green] Input loaded from: {input_file}")
        except Exception as e:
            console.print(f"[red]✗ Failed to load input file: {e}[/red]")
            sys.exit(1)
    elif input_json:
        try:
            input_data = json.loads(input_json)
            console.print(f"[green]✓[/green] Input parsed from JSON string")
        except Exception as e:
            console.print(f"[red]✗ Failed to parse input JSON: {e}[/red]")
            sys.exit(1)
    else:
        console.print("[yellow]⚠[/yellow] No input provided, using empty input")

    # Get runtime
    console.print(f"[dim]→ Runtime: {runtime}[/dim]")

    # Import runtime to trigger registration (dynamic import to avoid direct dependency)
    if runtime == "agno":
        try:
            __import__("agent_runtime_agno")
        except ImportError:
            console.print(f"[red]✗ Runtime '{runtime}' not installed. Install with: pip install -e ./agent-runtime/agno[/red]")
            sys.exit(1)

    runtime_class = RuntimeRegistry.get(runtime)
    if not runtime_class:
        console.print(f"[red]✗ Runtime '{runtime}' not found. Available: {RuntimeRegistry.list_runtimes()}[/red]")
        sys.exit(1)

    # Create runtime instance
    runtime_instance = runtime_class()
    runtime_info = runtime_instance.get_runtime_info()
    console.print(f"[dim]→ Runtime version: {runtime_info.get('version')}[/dim]")

    # Setup output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        # Generate run ID for output directory
        import uuid
        run_id = f"run-{uuid.uuid4().hex[:16]}"
        output_path = Path("runs") / run_id

    output_path.mkdir(parents=True, exist_ok=True)
    events_path = output_path / "events.jsonl"

    console.print(f"[dim]→ Output: {events_path}[/dim]")
    console.print()

    # Run agent
    try:
        with FileEventSink(events_path) as event_sink:
            console.print("[bold]Running agent...[/bold]")

            result = runtime_instance.run(
                agent_spec=agent_spec,
                input_data=input_data,
                event_sink=event_sink,
                trace_sink=NoOpTraceSink(),
                policy_engine=None,  # Let runtime load policies from agent spec
            )

            console.print()
            if result["status"] == "success":
                console.print(f"[green]✓ Run completed successfully[/green]")
                console.print(f"[dim]→ Run ID: {result['run_id']}[/dim]")
                console.print(f"[dim]→ Events: {events_path}[/dim]")
                console.print()
                console.print("[bold]Output:[/bold]")
                console.print(result.get("output", ""))

                if "metrics" in result:
                    console.print()
                    console.print("[bold]Metrics:[/bold]")
                    console.print(f"  Duration: {result['metrics'].get('duration_ms', 0):.2f}ms")
                    console.print(f"  Tokens: {result['metrics'].get('tokens_used', 0)}")
            else:
                console.print(f"[red]✗ Run failed[/red]")
                console.print(f"[dim]→ Run ID: {result['run_id']}[/dim]")
                console.print(f"[dim]→ Events: {events_path}[/dim]")
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Runtime error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@app.command()
def register(
    path: str = typer.Argument(..., help="Path to agent or tool directory"),
    registry_url: Optional[str] = typer.Option(None, "--registry", help="Registry URL"),
):
    """
    Register an agent or tool to the registry.

    Example:
        agentctl register agents/sample-agent
    """
    console.print(f"[yellow]Registering from: {path}[/yellow]")
    console.print(f"[dim]→ Registry: {registry_url or '(local)'}[/dim]")
    console.print("[dim]→ Registration not yet implemented[/dim]")
    console.print("[green]✓ Register placeholder executed[/green]")


@app.command()
def list(
    resource_type: str = typer.Argument("agents", help="Resource type: agents, tools, policies"),
    registry_url: Optional[str] = typer.Option(None, "--registry", help="Registry URL"),
):
    """
    List registered agents, tools, or policies.

    Example:
        agentctl list agents
        agentctl list tools
    """
    console.print(f"[yellow]Listing {resource_type}[/yellow]")
    console.print(f"[dim]→ Registry: {registry_url or '(local)'}[/dim]")
    console.print("[dim]→ List not yet implemented[/dim]")
    console.print("[green]✓ List placeholder executed[/green]")


@app.command()
def show(
    resource_name: str = typer.Argument(..., help="Resource name (e.g., agent-name, tool-name)"),
    resource_type: str = typer.Option("agent", "--type", "-t", help="Resource type: agent, tool, policy"),
):
    """
    Show details of a specific agent, tool, or policy.

    Example:
        agentctl show sample-agent --type agent
    """
    console.print(f"[yellow]Showing {resource_type}: {resource_name}[/yellow]")
    console.print("[dim]→ Show not yet implemented[/dim]")
    console.print("[green]✓ Show placeholder executed[/green]")


@app.command()
def replay(
    run_id: str = typer.Argument(..., help="Run ID to replay"),
    events_path: Optional[str] = typer.Option(None, "--events", help="Path to events.jsonl file"),
):
    """
    Replay a previous agent run from RunEvent stream.

    Example:
        agentctl replay run-123 --events runs/run-123/events.jsonl
    """
    console.print(f"[yellow]Replaying run: {run_id}[/yellow]")
    console.print(f"[dim]→ Events: {events_path or '(auto-detect)'}[/dim]")
    console.print("[dim]→ Replay not yet implemented[/dim]")
    console.print("[green]✓ Replay placeholder executed[/green]")


@app.command()
def review(
    run_id: str = typer.Argument(..., help="Run ID to review"),
    approve: bool = typer.Option(False, "--approve", help="Approve the review"),
    reject: bool = typer.Option(False, "--reject", help="Reject the review"),
):
    """
    Review and approve/reject a paused agent run.

    Example:
        agentctl review run-123 --approve
        agentctl review run-123 --reject
    """
    import json
    import yaml
    from pathlib import Path
    from agent_control_plane.pal import FileEventSink, NoOpTraceSink, RuntimeRegistry

    # Validate options
    if approve and reject:
        console.print("[red]✗ Cannot specify both --approve and --reject[/red]")
        sys.exit(1)

    if not approve and not reject:
        console.print("[red]✗ Must specify either --approve or --reject[/red]")
        sys.exit(1)

    decision = "approved" if approve else "rejected"

    # Find run directory
    run_dir = Path("runs") / run_id
    if not run_dir.exists():
        console.print(f"[red]✗ Run directory not found: {run_dir}[/red]")
        sys.exit(1)

    events_path = run_dir / "events.jsonl"
    if not events_path.exists():
        console.print(f"[red]✗ Events file not found: {events_path}[/red]")
        sys.exit(1)

    console.print(f"[yellow]Reviewing run: {run_id}[/yellow]")
    console.print(f"[dim]→ Decision: {decision}[/dim]")

    # Load events to find agent spec and input
    agent_name = None
    agent_spec_path = None
    original_input = {}
    has_review_request = False

    try:
        with open(events_path, "r") as f:
            for line in f:
                if line.strip():
                    event = json.loads(line)
                    if event.get("spec", {}).get("eventType") == "run.start":
                        agent_name = event.get("spec", {}).get("data", {}).get("agent_name")
                        original_input = event.get("spec", {}).get("data", {}).get("input", {})
                    elif event.get("spec", {}).get("eventType") == "human_review_request":
                        has_review_request = True

        if not has_review_request:
            console.print("[red]✗ No human review request found in this run[/red]")
            sys.exit(1)

        if not agent_name:
            console.print("[red]✗ Could not determine agent name from events[/red]")
            sys.exit(1)

        # Find agent spec
        agent_spec_path = Path(f"agents/{agent_name}/agent.yaml")
        if not agent_spec_path.exists():
            console.print(f"[red]✗ Agent spec not found: {agent_spec_path}[/red]")
            sys.exit(1)

        console.print(f"[green]✓[/green] Found agent: {agent_name}")

        # Load agent spec
        with open(agent_spec_path, "r") as f:
            agent_spec = yaml.safe_load(f)

        # Validate spec
        is_valid, errors = validator.validate_spec(agent_spec, path=str(agent_spec_path))
        if not is_valid:
            console.print(f"[red]✗ Agent spec validation failed:[/red]")
            for error in errors:
                console.print(f"  [red]→ {error}[/red]")
            sys.exit(1)

        console.print(f"[green]✓[/green] Agent spec validated")

        # Get runtime (handle both string and object format)
        runtime_spec = agent_spec.get("spec", {}).get("runtime", "agno")
        if isinstance(runtime_spec, dict):
            runtime = runtime_spec.get("type", "agno")
        else:
            runtime = runtime_spec
        console.print(f"[dim]→ Runtime: {runtime}[/dim]")

        # Import runtime to trigger registration (dynamic import to avoid direct dependency)
        if runtime == "agno":
            try:
                __import__("agent_runtime_agno")
            except ImportError:
                console.print(f"[red]✗ Runtime '{runtime}' not installed. Install with: pip install -e ./agent-runtime/agno[/red]")
                sys.exit(1)

        runtime_class = RuntimeRegistry.get(runtime)
        if not runtime_class:
            console.print(f"[red]✗ Runtime '{runtime}' not found. Available: {RuntimeRegistry.list_runtimes()}[/red]")
            sys.exit(1)

        # Create runtime instance
        runtime_instance = runtime_class()

        # Prepare input with review decision
        review_input = original_input.copy()
        review_input["reviewDecision"] = decision

        # Setup output directory (reuse same run directory)
        output_path = run_dir
        events_path_new = output_path / "events_continued.jsonl"

        console.print(f"[dim]→ Output: {events_path_new}[/dim]")
        console.print()

        # Run agent with review decision
        with FileEventSink(events_path_new) as event_sink:
            console.print(f"[bold]Resuming agent with {decision} decision...[/bold]")

            result = runtime_instance.run(
                agent_spec=agent_spec,
                input_data=review_input,
                event_sink=event_sink,
                trace_sink=NoOpTraceSink(),
                policy_engine=None,
            )

            console.print()
            if result["status"] == "success":
                console.print(f"[green]✓ Review {decision} - Run completed successfully[/green]")
                console.print(f"[dim]→ Run ID: {result['run_id']}[/dim]")
                console.print(f"[dim]→ Events: {events_path_new}[/dim]")
                console.print()
                console.print("[bold]Output:[/bold]")
                console.print(result.get("output", ""))

                if "artifactPath" in result.get("metrics", {}):
                    console.print()
                    console.print(f"[green]✓ Artifacts written to: {result['metrics']['artifactPath']}[/green]")
            else:
                console.print(f"[red]✗ Review {decision} - Run failed[/red]")
                console.print(f"[dim]→ Run ID: {result['run_id']}[/dim]")
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Review error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@app.callback()
def main():
    """
    Agent OS Control Plane CLI

    Architecture:
    - Control Plane: Spec, Registry, Policy, PAL
    - Data Plane: Runtime plugins (agno, etc.)
    - Event-driven: All runs produce RunEvent streams
    """
    pass


if __name__ == "__main__":
    app()
