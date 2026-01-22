"""
Agno Runtime Adapter

Adapts the agno framework to Agent OS PAL interfaces.
Integrates ToolExecutor and PolicyEngine for production-grade execution.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from agent_control_plane.pal import (
    AgentRuntime,
    DefaultPolicyEngine,
    DefaultToolExecutor,
    EventSink,
    NoOpPolicyEngine,
    PolicyEngine,
    RunEvent,
    RuntimeRegistry,
    TraceSink,
)


class AgnoRuntimeAdapter(AgentRuntime):
    """
    AgnoRuntimeAdapter implements the AgentRuntime interface for agno.

    This adapter:
    - Converts Agent Spec to agno agent configuration
    - Executes agent runs with ToolExecutor and PolicyEngine
    - Emits RunEvents to event sink
    - Handles errors and produces run_error events
    """

    def __init__(self):
        self.runtime_name = "agno"
        self.runtime_version = "0.2.0"

    def run(
        self,
        agent_spec: Dict[str, Any],
        input_data: Dict[str, Any],
        event_sink: EventSink,
        trace_sink: Optional[TraceSink] = None,
        policy_engine: Optional[PolicyEngine] = None,
    ) -> Dict[str, Any]:
        """
        Run an agent with agno runtime.

        This implementation:
        1. Generates a run_id
        2. Loads and validates policies
        3. Creates ToolExecutor and PolicyEngine
        4. Emits run.start event
        5. Executes agent with policy enforcement
        6. Emits tool events via ToolExecutor
        7. Emits run.end event
        8. Returns run result
        """
        # Generate run ID
        run_id = f"run-{uuid.uuid4().hex[:16]}"
        agent_name = agent_spec.get("metadata", {}).get("name", "unknown")
        sequence = 0

        try:
            # Load policies if not provided
            if policy_engine is None:
                policies = self._load_policies(agent_spec)
                if policies:
                    policy_engine = DefaultPolicyEngine(
                        policies=policies,
                        event_sink=event_sink,
                        run_id=run_id,
                        agent_name=agent_name,
                    )
                    sequence = policy_engine.get_sequence_counter()
                else:
                    policy_engine = NoOpPolicyEngine()

            # Policy check (run-level)
            if not policy_engine.validate_run(agent_spec, input_data):
                error_event = RunEvent(
                    run_id=run_id,
                    event_type="error",
                    data={"message": "Run blocked by policy"},
                    agent_name=agent_name,
                    sequence_number=sequence,
                    error={
                        "code": "POLICY_VIOLATION",
                        "message": "Run blocked by policy engine",
                    },
                )
                event_sink.emit(error_event)
                event_sink.flush()
                return {
                    "run_id": run_id,
                    "status": "error",
                    "error": "Run blocked by policy",
                }

            # Emit run.start event
            start_time = datetime.utcnow()
            start_event = RunEvent(
                run_id=run_id,
                event_type="run.start",
                data={
                    "agent_name": agent_name,
                    "input": input_data,
                    "agent_spec_version": agent_spec.get("apiVersion"),
                },
                agent_name=agent_name,
                sequence_number=sequence,
            )
            event_sink.emit(start_event)
            sequence += 1

            # Emit agent.start event
            agent_start_event = RunEvent(
                run_id=run_id,
                event_type="agent.start",
                data={
                    "agent_name": agent_name,
                    "system_prompt": agent_spec.get("spec", {})
                    .get("behavior", {})
                    .get("systemPrompt", ""),
                },
                agent_name=agent_name,
                sequence_number=sequence,
            )
            event_sink.emit(agent_start_event)
            sequence += 1

            # Create ToolExecutor with current sequence
            tool_executor = DefaultToolExecutor(
                event_sink=event_sink,
                run_id=run_id,
                agent_name=agent_name,
            )
            tool_executor.sequence_counter = sequence

            # Update policy engine sequence if it has one
            if hasattr(policy_engine, 'sequence_counter'):
                policy_engine.sequence_counter = sequence

            # Execute agent logic with ToolExecutor and PolicyEngine
            output = self._execute_agent(
                agent_spec=agent_spec,
                input_data=input_data,
                run_id=run_id,
                agent_name=agent_name,
                event_sink=event_sink,
                tool_executor=tool_executor,
                policy_engine=policy_engine,
                sequence=sequence,
            )
            sequence = output["sequence"]

            # Emit agent.end event
            agent_end_event = RunEvent(
                run_id=run_id,
                event_type="agent.end",
                data={
                    "agent_name": agent_name,
                    "output": output["result"],
                },
                agent_name=agent_name,
                sequence_number=sequence,
            )
            event_sink.emit(agent_end_event)
            sequence += 1

            # Emit run.end event
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            end_event_data = {
                "agent_name": agent_name,
                "status": "success",
                "output": output["result"],
            }

            # Add artifactPath to metrics if present
            end_event_metrics = {
                "durationMs": duration_ms,
                "tokensUsed": output.get("tokens_used", 0),
            }
            if "artifactPath" in output:
                end_event_metrics["artifactPath"] = output["artifactPath"]

            end_event = RunEvent(
                run_id=run_id,
                event_type="run.end",
                data=end_event_data,
                agent_name=agent_name,
                sequence_number=sequence,
                metrics=end_event_metrics,
            )
            event_sink.emit(end_event)
            event_sink.flush()

            result = {
                "run_id": run_id,
                "status": "success",
                "output": output["result"],
                "metrics": {
                    "duration_ms": duration_ms,
                    "tokens_used": output.get("tokens_used", 0),
                },
            }
            if "artifactPath" in output:
                result["metrics"]["artifactPath"] = output["artifactPath"]

            return result

        except Exception as e:
            # Emit error event
            error_event = RunEvent(
                run_id=run_id,
                event_type="error",
                data={
                    "agent_name": agent_name,
                    "error_message": str(e),
                },
                agent_name=agent_name,
                sequence_number=sequence,
                error={
                    "code": "RUNTIME_ERROR",
                    "message": str(e),
                },
            )
            event_sink.emit(error_event)
            event_sink.flush()

            return {
                "run_id": run_id,
                "status": "error",
                "error": str(e),
            }

    def _load_policies(self, agent_spec: Dict[str, Any]) -> list[Dict[str, Any]]:
        """
        Load policy specs referenced by the agent.

        Returns:
            List of validated policy specs
        """
        policies = []
        agent_policies = agent_spec.get("spec", {}).get("policies", [])

        for policy_ref in agent_policies:
            policy_name = policy_ref.get("name")
            if not policy_name:
                continue

            # Try to load policy file (assume it's in the same directory as agent)
            # For MVP, we look for <policy-name>.policy.yaml
            try:
                # This is a simplified approach - in production, use registry
                policy_path = Path(f"agents/sample-agent/{policy_name}.policy.yaml")
                if policy_path.exists():
                    with open(policy_path, "r") as f:
                        policy_spec = yaml.safe_load(f)
                        policies.append(policy_spec)
            except Exception:
                # Policy not found, skip
                pass

        return policies

    def _execute_agent(
        self,
        agent_spec: Dict[str, Any],
        input_data: Dict[str, Any],
        run_id: str,
        agent_name: str,
        event_sink: EventSink,
        tool_executor: DefaultToolExecutor,
        policy_engine: PolicyEngine,
        sequence: int,
    ) -> Dict[str, Any]:
        """
        Execute agent logic with ToolExecutor and PolicyEngine.

        For MVP, this simulates:
        1. LLM request/response
        2. Tool calls (with policy enforcement)
        3. Final response generation
        """
        # Check if this is a workflow-based agent (testcase-generator)
        if agent_name == "testcase-generator":
            return self._execute_testcase_workflow(
                agent_spec, input_data, run_id, agent_name,
                event_sink, tool_executor, policy_engine, sequence
            )

        # Original simple agent logic
        # Get user query from input
        query = input_data.get("query", input_data.get("message", ""))

        # Simulate LLM request
        llm_request_event = RunEvent(
            run_id=run_id,
            event_type="llm.request",
            data={
                "model": agent_spec.get("spec", {}).get("behavior", {}).get("model", "gpt-4"),
                "messages": [
                    {
                        "role": "system",
                        "content": agent_spec.get("spec", {})
                        .get("behavior", {})
                        .get("systemPrompt", ""),
                    },
                    {"role": "user", "content": query},
                ],
                "temperature": agent_spec.get("spec", {})
                .get("behavior", {})
                .get("temperature", 0.7),
            },
            agent_name=agent_name,
            sequence_number=sequence,
        )
        event_sink.emit(llm_request_event)
        sequence += 1

        # Check if agent has tools and if query requires tool use
        tools = agent_spec.get("spec", {}).get("tools", [])
        tool_results = []
        response_text = ""

        # Determine which tool to call based on query
        tool_to_call = None
        if "calculator" in query.lower() or any(
            char in query for char in ["+", "-", "*", "/", "="]
        ):
            tool_to_call = "calculator"
        elif "search" in query.lower() or "web" in query.lower():
            tool_to_call = "web-search"

        if tool_to_call and tools:
            # Sync sequence counters before policy check
            if hasattr(policy_engine, 'sequence_counter'):
                policy_engine.sequence_counter = sequence

            # Check policy before calling tool
            if policy_engine.check_tool_call(tool_to_call, {}):
                # Policy allows - get updated sequence from policy engine
                if hasattr(policy_engine, 'sequence_counter'):
                    sequence = policy_engine.sequence_counter

                # Sync tool executor sequence
                tool_executor.sequence_counter = sequence

                # Load tool spec
                tool_spec = self._load_tool_spec(tool_to_call, agent_name)

                # Prepare parameters
                if tool_to_call == "calculator":
                    # Extract expression from query
                    import re

                    match = re.search(r"(\d+\s*[\+\-\*/]\s*\d+)", query)
                    expression = match.group(1) if match else "2 + 2"
                    parameters = {"expression": expression}
                else:
                    parameters = {"query": query}

                # Execute tool via ToolExecutor
                result = tool_executor.execute(tool_to_call, tool_spec, parameters)

                # Get updated sequence from tool executor
                sequence = tool_executor.get_sequence_counter()

                if result.get("success", True):
                    tool_results.append(f"{tool_to_call} result: {result}")
                    response_text = f"I used the {tool_to_call} tool. Result: {result.get('result', result)}"
                else:
                    response_text = f"I tried to use {tool_to_call} but it failed: {result.get('error', {}).get('message', 'Unknown error')}"
            else:
                # Policy denied - tool was not executed, policy event already emitted
                if hasattr(policy_engine, 'sequence_counter'):
                    sequence = policy_engine.sequence_counter
                response_text = f"I cannot use the {tool_to_call} tool because it is blocked by policy."

        if not response_text:
            response_text = f"Echo: {query}"

        # Simulate LLM response
        llm_response_event = RunEvent(
            run_id=run_id,
            event_type="llm.response",
            data={
                "content": response_text,
                "finish_reason": "stop",
            },
            agent_name=agent_name,
            sequence_number=sequence,
            metrics={
                "tokensUsed": len(response_text.split()),  # Rough estimate
            },
        )
        event_sink.emit(llm_response_event)
        sequence += 1

        return {
            "result": response_text,
            "tokens_used": len(response_text.split()),
            "sequence": sequence,
        }

    def _load_tool_spec(self, tool_name: str, agent_name: str = "sample-agent") -> Dict[str, Any]:
        """
        Load tool spec by name.

        For MVP, returns a minimal spec. In production, use registry.
        """
        # Try to load from file
        tool_path = Path(f"agents/{agent_name}/{tool_name}.tool.yaml")
        if tool_path.exists():
            try:
                with open(tool_path, "r") as f:
                    return yaml.safe_load(f)
            except Exception:
                pass

        # Fallback to minimal spec
        return {
            "apiVersion": "agent-os.dev/v1alpha1",
            "kind": "Tool",
            "metadata": {"name": tool_name},
            "spec": {
                "description": f"{tool_name} tool",
                "type": "function",
                "config": {"timeoutMs": 5000, "retries": 0},
            },
        }

    def _execute_testcase_workflow(
        self,
        agent_spec: Dict[str, Any],
        input_data: Dict[str, Any],
        run_id: str,
        agent_name: str,
        event_sink: EventSink,
        tool_executor: DefaultToolExecutor,
        policy_engine: PolicyEngine,
        sequence: int,
    ) -> Dict[str, Any]:
        """
        Execute testcase-generator workflow with human review.

        Workflow:
        1. Read requirements
        2. Generate test cases (LLM)
        3. Validate test cases
        4. Human review (pause and wait for approval)
        5. Write test cases to artifacts
        """
        requirements_path = input_data.get("requirementsPath", "requirements.txt")

        # Step 1: Read requirements
        tool_spec = self._load_tool_spec("requirements-reader", agent_name)
        tool_executor.sequence_counter = sequence

        result = tool_executor.execute(
            "requirements-reader",
            tool_spec,
            {"requirementsPath": requirements_path}
        )
        sequence = tool_executor.get_sequence_counter()

        if not result.get("success", True):
            return {
                "result": f"Failed to read requirements: {result.get('error', {}).get('message', 'Unknown error')}",
                "tokens_used": 0,
                "sequence": sequence,
            }

        requirements = result.get("result", {}).get("requirements", [])

        # Step 2: Generate test cases
        tool_spec = self._load_tool_spec("testcase-generator", agent_name)
        tool_executor.sequence_counter = sequence

        result = tool_executor.execute(
            "testcase-generator",
            tool_spec,
            {"requirements": requirements, "format": "json"}
        )
        sequence = tool_executor.get_sequence_counter()

        if not result.get("success", True):
            return {
                "result": f"Failed to generate test cases: {result.get('error', {}).get('message', 'Unknown error')}",
                "tokens_used": 0,
                "sequence": sequence,
            }

        test_cases = result.get("result", {}).get("testCases", [])

        # Step 3: Validate test cases
        tool_spec = self._load_tool_spec("testcase-validator", agent_name)
        tool_executor.sequence_counter = sequence

        result = tool_executor.execute(
            "testcase-validator",
            tool_spec,
            {"testCases": test_cases}
        )
        sequence = tool_executor.get_sequence_counter()

        if not result.get("success", True):
            return {
                "result": f"Failed to validate test cases: {result.get('error', {}).get('message', 'Unknown error')}",
                "tokens_used": 0,
                "sequence": sequence,
            }

        validation_result = result.get("result", {})
        if not validation_result.get("valid", False):
            return {
                "result": f"Test cases validation failed: {validation_result.get('errors', [])}",
                "tokens_used": 0,
                "sequence": sequence,
            }

        # Step 4: Human review workflow
        human_review_event = RunEvent(
            run_id=run_id,
            event_type="human_review_request",
            data={
                "stage": "after-generation",
                "testCaseCount": len(test_cases),
                "testCases": test_cases,
                "message": "Please review the generated test cases and approve or reject.",
                "reviewCommand": f"agentctl review {run_id} --approve/--reject"
            },
            agent_name=agent_name,
            sequence_number=sequence,
        )
        event_sink.emit(human_review_event)
        sequence += 1

        # Check for review decision in input_data
        review_decision = input_data.get("reviewDecision", "pending")

        if review_decision == "pending":
            # Workflow paused, waiting for human review
            return {
                "result": f"Workflow paused for human review. Run ID: {run_id}. Use 'agentctl review {run_id} --approve' to continue.",
                "tokens_used": 0,
                "sequence": sequence,
                "status": "pending_review",
            }
        elif review_decision == "rejected":
            # Human rejected
            reject_event = RunEvent(
                run_id=run_id,
                event_type="human_review_response",
                data={
                    "decision": "rejected",
                    "message": "Test cases rejected by human reviewer"
                },
                agent_name=agent_name,
                sequence_number=sequence,
            )
            event_sink.emit(reject_event)
            sequence += 1

            return {
                "result": "Test cases rejected by human reviewer. Workflow terminated.",
                "tokens_used": 0,
                "sequence": sequence,
            }

        # Step 5: Human approved - write test cases
        approve_event = RunEvent(
            run_id=run_id,
            event_type="human_review_response",
            data={
                "decision": "approved",
                "message": "Test cases approved by human reviewer"
            },
            agent_name=agent_name,
            sequence_number=sequence,
        )
        event_sink.emit(approve_event)
        sequence += 1

        tool_spec = self._load_tool_spec("testcase-writer", agent_name)
        tool_executor.sequence_counter = sequence

        result = tool_executor.execute(
            "testcase-writer",
            tool_spec,
            {"testCases": test_cases, "runId": run_id, "filename": "testcases.json"}
        )
        sequence = tool_executor.get_sequence_counter()

        if not result.get("success", True):
            return {
                "result": f"Failed to write test cases: {result.get('error', {}).get('message', 'Unknown error')}",
                "tokens_used": 0,
                "sequence": sequence,
            }

        artifact_path = result.get("result", {}).get("artifactPath", "")
        test_case_count = result.get("result", {}).get("testCaseCount", 0)

        return {
            "result": f"Successfully generated and wrote {test_case_count} test cases to {artifact_path}",
            "tokens_used": 50,  # Rough estimate
            "sequence": sequence,
            "artifactPath": artifact_path,
        }


    def get_runtime_info(self) -> Dict[str, Any]:
        """Get agno runtime information"""
        return {
            "name": self.runtime_name,
            "version": self.runtime_version,
            "capabilities": [
                "agent_execution",
                "tool_calling",
                "event_streaming",
                "policy_enforcement",
                "tool_timeout",
                "tool_retry",
            ],
        }


# Register the runtime
RuntimeRegistry.register("agno", AgnoRuntimeAdapter)
