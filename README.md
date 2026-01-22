# Agent OS

**Enterprise-grade Agent Platform following Kubernetes CRD / Control Plane / Data Plane architecture**

## Architecture Overview

Agent OS is designed with strict separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Control Plane                            │
│  ┌──────────┐  ┌──────────┐  ┌──────┐  ┌──────────────┐   │
│  │   Spec   │  │ Registry │  │ PAL  │  │ SDK/CLI      │   │
│  │ (Schema) │  │          │  │      │  │ (agentctl)   │   │
│  └──────────┘  └──────────┘  └──────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Runtime Interface
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Data Plane                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Runtime:   │  │   Runtime:   │  │   Runtime:   │     │
│  │    agno      │  │   langchain  │  │   custom     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Spec-First Architecture**
   - All entities (Agent, Tool, Policy, RunEvent, Trace) are formal contracts (JSON Schema)
   - No object runs without passing schema validation
   - Kubernetes CRD-style specifications

2. **Control Plane / Data Plane Separation**
   - **Control Plane**: Spec definitions, Registry, Policy, PAL, CLI
   - **Data Plane**: Runtime implementations (agno, langchain, etc.)
   - Control plane NEVER depends on specific runtime implementations

3. **Runtime Pluggability**
   - Multiple runtimes can coexist
   - agno is just one runtime adapter
   - Easy to add new runtime implementations

4. **Event-Driven Observability**
   - All agent runs produce RunEvent streams (JSONL format)
   - Events are the single source of truth
   - Enables replay, debugging, and auditing

## Directory Structure

```
agent-os/
├── control-plane/              # Control Plane (runtime-agnostic)
│   ├── agent_control_plane/
│   │   ├── specs/             # JSON Schema definitions
│   │   ├── registry/          # Agent/Tool registry
│   │   ├── pal/               # Policy Abstraction Layer
│   │   └── sdk/
│   │       └── cli/           # agentctl CLI
│   └── pyproject.toml
│
├── agent-runtime/              # Data Plane (runtime implementations)
│   └── agno/                  # Agno runtime adapter
│       ├── agent_runtime_agno/
│       │   └── adapters/      # Agno-specific adapters
│       └── pyproject.toml
│
├── agents/                     # Agent definitions
│   └── sample-agent/
│       └── agent.yaml         # Agent spec
│
├── runs/                       # Runtime execution outputs
│   └── <run-id>/
│       └── events.jsonl       # RunEvent stream
│
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd agent-os
   ```

2. **Install Control Plane**
   ```bash
   pip install -e ./control-plane
   ```

3. **Install Runtime (for running agents)**
   ```bash
   pip install -e ./agent-runtime/agno
   ```

4. **Install Console (optional, for web UI)**
   ```bash
   pip install -e ./console
   ```

5. **Install Contract Tests (optional, for testing)**
   ```bash
   pip install -e ./tests/contract
   ```

6. **Verify installation**
   ```bash
   agentctl --help
   python scripts/check_imports.py
   ```

### Quick Start

1. **Validate an agent spec**
   ```bash
   agentctl validate agents/sample-agent/agent.yaml
   ```

2. **Run an agent locally**
   ```bash
   agentctl run-local agents/sample-agent/agent.yaml --input agents/sample-agent/input.json
   ```

3. **View run results**
   ```bash
   cat runs/run-<id>/events.jsonl
   ```

4. **Launch Console UI**
   ```bash
   cd console
   python -m console.app
   # Open http://localhost:5000
   ```

5. **Run contract tests**
   ```bash
   cd tests/contract
   pytest -v
   ```

## Console Features

The web console provides:

- **Runs List**: View all agent runs with status, timestamps, and review state
- **Run Detail**: Inspect complete event streams and artifacts
- **Human Review**: Approve/reject workflows directly from the UI
- **API Endpoints**: RESTful API at `/api/runs` and `/api/runs/<id>`

Access at `http://localhost:5000` after starting the console.

## Testing

### Contract Tests

Contract tests verify:
- Event sequence correctness
- Required field presence
- Agent behavior determinism
- Tool execution order
- Metrics collection

```bash
cd tests/contract
pytest -v
```

### Import Guard

Enforces architectural boundaries:
- control-plane MUST NOT import agno
- agents MUST NOT import agno
- console MUST NOT import agno

```bash
python scripts/check_imports.py
```

### CI Pipeline

GitHub Actions workflow runs on every push/PR:
- Import guard checks
- Spec validation
- Contract tests
- Console import checks

## CLI Reference

The `agentctl` CLI provides the following commands:

- `validate <path>` - Validate agent/tool/policy specs against JSON Schema
- `run-local <agent> --input <file>` - Run an agent locally using specified runtime
- `review <run-id> --approve/--reject` - Approve or reject a paused workflow
- `register <path>` - Register an agent/tool to the registry (placeholder)
- `list <type>` - List registered agents, tools, or policies (placeholder)
- `show <name>` - Show details of a specific resource (placeholder)
- `replay <run-id>` - Replay a previous agent run from RunEvent stream (placeholder)

Run `agentctl --help` for detailed usage.

## Event Types

Agent OS uses a comprehensive event system:

- `run.start` / `run.end` - Run lifecycle events
- `agent.start` / `agent.end` - Agent lifecycle events
- `llm.request` / `llm.response` - LLM interaction events
- `tool.call` / `tool.result` - Tool execution events
- `policy.allow` / `policy.deny` - Policy decision events
- `human_review_request` / `human_review_response` - Human review workflow events

All events follow the Kubernetes-style structure with `apiVersion`, `kind`, `metadata`, and `spec`.

## Development

### Python Package Naming Convention

- **Directory names**: Use `kebab-case` for domain directories
  - `control-plane/`, `agent-runtime/`
- **Python packages**: Use `snake_case` for Python packages
  - `agent_control_plane`, `agent_runtime_agno`
- **No sys.path hacks**: Proper package structure only

### Adding a New Runtime

1. Create directory: `agent-runtime/<runtime-name>/`
2. Create package: `agent_runtime_<runtime_name>/`
3. Implement adapters in `adapters/` subdirectory
4. Add `pyproject.toml` with dependency on `agent-control-plane`

### Project Status

**All 5 iterations completed!** ✅

- ✅ Iteration 0: Repository skeleton with control/data plane separation
- ✅ Iteration 1: Spec definitions and validators (JSON Schema)
- ✅ Iteration 2: PAL interfaces and agno runtime adapter
- ✅ Iteration 3: ToolExecutor with timeout/retry + PolicyEngine with allow/deny
- ✅ Iteration 4: Test case generator agent with human-in-the-loop workflow
- ✅ Iteration 5: Console UI + Contract tests + Import guard

## Architecture Constraints

1. ✅ Spec-first: All entities validated against JSON Schema
2. ✅ Control/Data plane separation: No runtime dependencies in control-plane
3. ✅ Runtime pluggability: Multiple runtimes supported
4. ✅ Python conventions: kebab-case dirs, snake_case packages
5. ✅ Event-driven: All runs produce RunEvent streams
6. ✅ MVP-first: Runnable skeleton before full implementation

## License

[Your License Here]

## Contributing

[Contributing Guidelines Here]
