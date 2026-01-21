"""agentctl CLI - Main entry point."""

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Agent OS CLI - Manage and run agents."""
    pass


@cli.command()
@click.argument("spec_file", type=click.Path(exists=True))
@click.option("--type", type=click.Choice(["agent", "tool", "policy"]), required=True)
def validate(spec_file, type):
    """Validate a spec file against JSON schema."""
    import json
    from pathlib import Path
    from platform_core.sdk.validator import SpecValidator

    console.print(f"[cyan]Validating {type} spec: {spec_file}[/cyan]")

    try:
        with open(spec_file) as f:
            spec = json.load(f)

        validator = SpecValidator()

        if type == "agent":
            validator.validate_agent(spec)
        elif type == "tool":
            validator.validate_tool(spec)
        elif type == "policy":
            validator.validate_policy(spec)

        console.print(f"[green]✓ {type.capitalize()} spec is valid[/green]")
    except Exception as e:
        console.print(f"[red]✗ Validation failed: {e}[/red]")
        raise click.Abort()


@cli.command()
@click.argument("agent_id")
@click.option("--input", type=click.Path(exists=True), help="Input JSON file")
@click.option("--output-dir", type=click.Path(), default="runs", help="Output directory for run events")
def run_local(agent_id, input, output_dir):
    """Run an agent locally."""
    from pathlib import Path
    from platform_core.registry import Registry

    console.print(f"[cyan]Running agent: {agent_id}[/cyan]")

    registry = Registry()
    agent_spec = registry.get_agent(agent_id)

    if not agent_spec:
        console.print(f"[red]✗ Agent '{agent_id}' not found in registry[/red]")
        raise click.Abort()

    console.print(f"[yellow]⚠ Run execution not yet implemented[/yellow]")
    console.print(f"Agent: {agent_spec.name} v{agent_spec.version}")
    console.print(f"Runtime: {agent_spec.runtime}")
    console.print(f"Output dir: {output_dir}")


@cli.command()
@click.argument("spec_file", type=click.Path(exists=True))
@click.option("--type", type=click.Choice(["agent", "tool", "policy"]), required=True)
def register(spec_file, type):
    """Register a spec in the registry."""
    import json
    from platform_core.registry import Registry
    from platform_core.sdk.models import AgentSpec, ToolSpec, PolicySpec
    from platform_core.sdk.validator import SpecValidator

    console.print(f"[cyan]Registering {type}: {spec_file}[/cyan]")

    try:
        with open(spec_file) as f:
            spec_data = json.load(f)

        # Validate first
        validator = SpecValidator()
        if type == "agent":
            validator.validate_agent(spec_data)
            spec = AgentSpec(**spec_data)
        elif type == "tool":
            validator.validate_tool(spec_data)
            spec = ToolSpec(**spec_data)
        elif type == "policy":
            validator.validate_policy(spec_data)
            spec = PolicySpec(**spec_data)

        # Register
        registry = Registry()
        if type == "agent":
            registry.register_agent(spec)
        elif type == "tool":
            registry.register_tool(spec)
        elif type == "policy":
            registry.register_policy(spec)

        console.print(f"[green]✓ {type.capitalize()} '{spec.id}' registered successfully[/green]")
    except Exception as e:
        console.print(f"[red]✗ Registration failed: {e}[/red]")
        raise click.Abort()


@cli.command()
@click.option("--type", type=click.Choice(["agent", "tool", "policy"]), default="agent")
def list(type):
    """List registered specs."""
    from platform_core.registry import Registry

    registry = Registry()

    if type == "agent":
        items = registry.list_agents()
    else:
        console.print(f"[yellow]⚠ Listing {type}s not yet implemented[/yellow]")
        return

    if not items:
        console.print(f"[yellow]No {type}s registered[/yellow]")
        return

    console.print(f"[cyan]Registered {type}s:[/cyan]\n")
    for item in items:
        console.print(f"  • {item.id} - {item.name} (v{item.version})")


@cli.command()
@click.argument("item_id")
@click.option("--type", type=click.Choice(["agent", "tool", "policy"]), default="agent")
def show(item_id, type):
    """Show details of a registered spec."""
    import json
    from platform_core.registry import Registry

    registry = Registry()

    if type == "agent":
        item = registry.get_agent(item_id)
    elif type == "tool":
        item = registry.get_tool(item_id)
    elif type == "policy":
        item = registry.get_policy(item_id)

    if not item:
        console.print(f"[red]✗ {type.capitalize()} '{item_id}' not found[/red]")
        raise click.Abort()

    console.print(f"[cyan]{type.capitalize()}: {item.id}[/cyan]\n")
    console.print(json.dumps(item.model_dump(), indent=2))


@cli.command()
@click.argument("run_dir", type=click.Path(exists=True))
def replay(run_dir):
    """Replay a run from JSONL events."""
    from pathlib import Path

    console.print(f"[cyan]Replaying run from: {run_dir}[/cyan]")
    console.print(f"[yellow]⚠ Replay not yet implemented[/yellow]")

    run_path = Path(run_dir)
    events_file = run_path / "events.jsonl"

    if events_file.exists():
        console.print(f"Found events file: {events_file}")
    else:
        console.print(f"[red]✗ No events.jsonl found in {run_dir}[/red]")


if __name__ == "__main__":
    cli()
