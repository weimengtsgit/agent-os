"""
Agent OS Control Plane

Control Plane is the core of Agent OS, providing:
- Spec definitions (Agent, Tool, Policy, RunEvent, Trace)
- Registry for agent/tool discovery
- PAL (Policy Abstraction Layer)
- SDK and CLI tools

Architecture:
- Spec-first: All entities are validated against JSON Schema
- Runtime-agnostic: No dependency on specific runtime implementations
- Event-driven: All runs produce RunEvent streams (JSONL)
"""

__version__ = "0.1.0"
