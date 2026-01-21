# Agent OS

Spec-first, decoupled Agent OS platform for enterprise use.

## Architecture

```
agent-os/
├── platform_core/         # Core platform (NO agno dependency)
│   ├── specs/             # JSON schemas for validation
│   ├── sdk/               # Core SDK (models, validator, runtime interface)
│   ├── registry/          # Agent/tool/policy registry
│   └── cli/               # agentctl CLI
├── agent_runtime_agno/    # Agno runtime adapter (ONLY place with agno)
│   └── adapters/
├── agents/                # Business agents
│   └── sample_agent/
├── console/               # Web console (optional)
└── runs/                  # Run outputs (JSONL events)
```

## Key Principles

1. **Spec-first**: All agents/tools/policies defined via JSON specs with schema validation
2. **Decoupled**: Business agents and platform-core SDK have NO direct agno dependency
3. **Observable**: All runs produce JSONL events for replay and audit
4. **Validated**: JSON Schema validation before execution

## Installation

### Using uv (recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e ".[dev]"
```

## Quick Start

### 1. Verify Installation

```bash
agentctl --help
```

Expected output:
```
Usage: agentctl [OPTIONS] COMMAND [ARGS]...

  Agent OS CLI - Manage and run agents.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  list       List registered specs.
  register   Register a spec in the registry.
  replay     Replay a run from JSONL events.
  run-local  Run an agent locally.
  show       Show details of a registered spec.
  validate   Validate a spec file against JSON schema.
```

### 2. Validate Sample Agent

```bash
agentctl validate agents/sample-agent/agent.json --type agent
```

Expected output:
```
Validating agent spec: agents/sample-agent/agent.json
✓ Agent spec is valid
```

### 3. Register Sample Agent

```bash
# Register the agent
agentctl register agents/sample-agent/agent.json --type agent

# Register the tool
agentctl register agents/sample-agent/tools/echo-tool.json --type tool

# Register the policy
agentctl register agents/sample-agent/policies/basic-policy.json --type policy
```

### 4. List Registered Agents

```bash
agentctl list --type agent
```

Expected output:
```
Registered agents:

  • sample-agent - Sample Agent (v1.0.0)
```

### 5. Show Agent Details

```bash
agentctl show sample-agent --type agent
```

### 6. Run Agent (stub implementation)

```bash
agentctl run-local sample-agent --output-dir runs/sample-run-001
```

## CLI Commands

### validate

Validate a spec file against JSON schema:

```bash
agentctl validate <spec-file> --type <agent|tool|policy>
```

### register

Register a spec in the registry:

```bash
agentctl register <spec-file> --type <agent|tool|policy>
```

### list

List registered specs:

```bash
agentctl list --type <agent|tool|policy>
```

### show

Show details of a registered spec:

```bash
agentctl show <id> --type <agent|tool|policy>
```

### run-local

Run an agent locally (stub - not yet implemented):

```bash
agentctl run-local <agent-id> [--input <input.json>] [--output-dir <dir>]
```

### replay

Replay a run from JSONL events (stub - not yet implemented):

```bash
agentctl replay <run-dir>
```

## Testing

Run tests with pytest:

```bash
pytest
```

## Development

### Project Structure

- `platform_core/` - Core platform package
  - `sdk/` - SDK with models, validator, runtime interface
  - `registry/` - Registry implementation
  - `cli/` - CLI implementation
  - `specs/` - JSON schemas
- `agent_runtime_agno/` - Agno runtime adapter (isolated)
- `agents/` - Business agents (no agno dependency)

### Adding a New Agent

1. Create agent directory: `agents/my-agent/`
2. Create `agent.json` following the schema
3. Validate: `agentctl validate agents/my-agent/agent.json --type agent`
4. Register: `agentctl register agents/my-agent/agent.json --type agent`

### Adding a New Runtime

1. Create adapter in `agent-runtime-<name>/`
2. Implement `RuntimeAdapter` interface
3. Update agent spec to use new runtime

## Next Steps

- [ ] Implement actual agno runtime execution
- [ ] Implement replay functionality
- [ ] Add policy enforcement
- [ ] Add web console
- [ ] Add remote registry support
- [ ] Add authentication/authorization

## License

MIT
