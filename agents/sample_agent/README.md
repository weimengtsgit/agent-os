# Sample Agent

This is a sample agent demonstrating the Agent OS platform structure.

## Files

- `agent.json` - Agent specification
- `tools/echo-tool.json` - Tool specification
- `policies/basic-policy.json` - Policy specification

## Usage

```bash
# Validate the agent spec
agentctl validate agents/sample-agent/agent.json --type agent

# Register the agent
agentctl register agents/sample-agent/agent.json --type agent

# Run the agent
agentctl run-local sample-agent --output-dir runs/sample-run-001
```
