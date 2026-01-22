"""
Default Tool Executor Implementation

Provides concrete implementation of ToolExecutor with:
- Timeout support
- Retry logic
- Error handling
- Event emission for tool calls
"""

import time
from typing import Any, Dict, Optional

from agent_control_plane.pal.interfaces import EventSink, RunEvent, ToolExecutor


class DefaultToolExecutor(ToolExecutor):
    """
    DefaultToolExecutor implements tool execution with timeout and retry.

    Features:
    - Configurable timeout (from tool spec or default)
    - Retry logic with exponential backoff
    - Emits tool.call and tool.result events
    - Error handling without naked exceptions
    """

    def __init__(
        self,
        event_sink: EventSink,
        run_id: str,
        agent_name: str,
        default_timeout_ms: int = 30000,
        default_retries: int = 0,
    ):
        self.event_sink = event_sink
        self.run_id = run_id
        self.agent_name = agent_name
        self.default_timeout_ms = default_timeout_ms
        self.default_retries = default_retries
        self.sequence_counter = 0

    def execute(
        self,
        tool_name: str,
        tool_spec: Dict[str, Any],
        parameters: Dict[str, Any],
    ) -> Any:
        """
        Execute a tool with timeout and retry support.

        Args:
            tool_name: Name of the tool
            tool_spec: Tool specification (validated)
            parameters: Tool parameters

        Returns:
            Tool execution result or error dict
        """
        # Extract timeout and retry config from tool spec
        tool_config = tool_spec.get("spec", {}).get("config", {})
        timeout_ms = tool_config.get("timeoutMs", self.default_timeout_ms)
        max_retries = tool_config.get("retries", self.default_retries)

        # Emit tool.call event
        self._emit_tool_call(tool_name, parameters, timeout_ms, max_retries)

        # Execute with retry logic
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()

                # Execute the tool (MVP: simulated execution)
                result = self._execute_tool_impl(
                    tool_name, tool_spec, parameters, timeout_ms
                )

                duration_ms = (time.time() - start_time) * 1000

                # Emit tool.result event (success)
                self._emit_tool_result(
                    tool_name,
                    result,
                    success=True,
                    duration_ms=duration_ms,
                    attempt=attempt,
                )

                return result

            except TimeoutError as e:
                last_error = {
                    "code": "TIMEOUT",
                    "message": f"Tool execution timed out after {timeout_ms}ms",
                    "details": str(e),
                }
                if attempt < max_retries:
                    # Exponential backoff
                    backoff_ms = min(1000 * (2 ** attempt), 10000)
                    time.sleep(backoff_ms / 1000)
                    continue
                else:
                    break

            except Exception as e:
                last_error = {
                    "code": "EXECUTION_ERROR",
                    "message": f"Tool execution failed: {str(e)}",
                    "details": str(e),
                }
                if attempt < max_retries:
                    # Exponential backoff
                    backoff_ms = min(1000 * (2 ** attempt), 10000)
                    time.sleep(backoff_ms / 1000)
                    continue
                else:
                    break

        # All retries exhausted, emit error result
        self._emit_tool_result(
            tool_name,
            None,
            success=False,
            error=last_error,
            attempt=max_retries,
        )

        return {"error": last_error, "success": False}

    def _execute_tool_impl(
        self,
        tool_name: str,
        tool_spec: Dict[str, Any],
        parameters: Dict[str, Any],
        timeout_ms: int,
    ) -> Any:
        """
        Internal tool execution implementation.

        For MVP, this simulates tool execution.
        In production, this would:
        - Call actual tool implementations
        - Handle different tool types (function, api, mcp)
        - Enforce timeout
        """
        # Simulate execution time
        execution_time = 0.01  # 10ms
        time.sleep(execution_time)

        # Check timeout (simplified)
        if execution_time * 1000 > timeout_ms:
            raise TimeoutError(f"Execution exceeded {timeout_ms}ms")

        # Simulate tool execution based on tool type
        tool_type = tool_spec.get("spec", {}).get("type", "function")

        if tool_type == "function":
            # Simulate function execution
            if tool_name == "calculator":
                expression = parameters.get("expression", "")
                try:
                    # Simple eval for MVP (UNSAFE in production!)
                    result = eval(expression, {"__builtins__": {}}, {})
                    return {"result": result, "expression": expression}
                except Exception as e:
                    raise ValueError(f"Invalid expression: {e}")

            elif tool_name == "requirements-reader":
                # Read requirements from file
                requirements_path = parameters.get("requirementsPath", "")
                try:
                    from pathlib import Path
                    path = Path(requirements_path)
                    if path.exists():
                        with open(path, "r") as f:
                            content = f.read()
                        # Parse requirements (simple line-based parsing)
                        requirements = [
                            line.strip()
                            for line in content.split("\n")
                            if line.strip() and not line.startswith("#")
                        ]
                        return {
                            "result": {
                                "requirements": requirements,
                                "metadata": {
                                    "source": str(path),
                                    "count": len(requirements)
                                }
                            }
                        }
                    else:
                        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")
                except Exception as e:
                    raise ValueError(f"Failed to read requirements: {e}")

            elif tool_name == "testcase-generator":
                # Generate test cases (mock LLM)
                requirements = parameters.get("requirements", [])
                format_type = parameters.get("format", "json")

                # Mock test case generation
                test_cases = []
                for i, req in enumerate(requirements, 1):
                    test_case = {
                        "id": f"TC-{i:03d}",
                        "title": f"Test case for: {req[:50]}...",
                        "description": f"Verify that {req}",
                        "steps": [
                            "Navigate to the feature",
                            "Perform the action",
                            "Verify the result"
                        ],
                        "expectedResult": "Feature works as specified",
                        "priority": "high" if i <= 3 else "medium",
                        "requirement": req
                    }
                    test_cases.append(test_case)

                return {
                    "result": {
                        "testCases": test_cases,
                        "summary": {
                            "total": len(test_cases),
                            "format": format_type
                        }
                    }
                }

            elif tool_name == "testcase-validator":
                # Validate test cases
                test_cases = parameters.get("testCases", [])
                rules = parameters.get("rules", ["has_description", "has_steps", "has_expected_result"])

                validation_results = []
                errors = []

                for tc in test_cases:
                    tc_errors = []

                    if "has_description" in rules and not tc.get("description"):
                        tc_errors.append("Missing description")

                    if "has_steps" in rules and not tc.get("steps"):
                        tc_errors.append("Missing steps")

                    if "has_expected_result" in rules and not tc.get("expectedResult"):
                        tc_errors.append("Missing expected result")

                    validation_results.append({
                        "testCaseId": tc.get("id", "unknown"),
                        "valid": len(tc_errors) == 0,
                        "errors": tc_errors
                    })

                    if tc_errors:
                        errors.extend([f"{tc.get('id')}: {err}" for err in tc_errors])

                all_valid = all(r["valid"] for r in validation_results)

                return {
                    "result": {
                        "valid": all_valid,
                        "validationResults": validation_results,
                        "errors": errors
                    }
                }

            elif tool_name == "testcase-writer":
                # Write test cases to artifacts
                test_cases = parameters.get("testCases", [])
                run_id = parameters.get("runId", "unknown")
                filename = parameters.get("filename", "testcases.json")

                try:
                    import json
                    from pathlib import Path

                    # Create artifacts directory
                    artifacts_dir = Path("runs") / run_id / "artifacts"
                    artifacts_dir.mkdir(parents=True, exist_ok=True)

                    # Write test cases
                    artifact_path = artifacts_dir / filename
                    with open(artifact_path, "w") as f:
                        json.dump(test_cases, f, indent=2)

                    return {
                        "result": {
                            "success": True,
                            "artifactPath": str(artifact_path),
                            "testCaseCount": len(test_cases)
                        }
                    }
                except Exception as e:
                    raise ValueError(f"Failed to write test cases: {e}")

            else:
                # Generic function result
                return {"result": f"Executed {tool_name}", "parameters": parameters}

        elif tool_type == "api":
            # Simulate API call
            return {
                "status": "success",
                "data": f"API response from {tool_name}",
                "parameters": parameters,
            }

        else:
            # Unknown tool type
            return {"result": f"Executed {tool_name} (type: {tool_type})"}

    def _emit_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout_ms: int,
        max_retries: int,
    ) -> None:
        """Emit tool.call event"""
        event = RunEvent(
            run_id=self.run_id,
            event_type="tool.call",
            data={
                "tool_name": tool_name,
                "parameters": parameters,
                "config": {
                    "timeoutMs": timeout_ms,
                    "maxRetries": max_retries,
                },
            },
            agent_name=self.agent_name,
            sequence_number=self.sequence_counter,
        )
        self.event_sink.emit(event)
        self.sequence_counter += 1

    def _emit_tool_result(
        self,
        tool_name: str,
        result: Any,
        success: bool,
        duration_ms: Optional[float] = None,
        error: Optional[Dict[str, Any]] = None,
        attempt: int = 0,
    ) -> None:
        """Emit tool.result event"""
        data = {
            "tool_name": tool_name,
            "success": success,
            "attempt": attempt,
        }

        if success:
            data["result"] = result
        else:
            data["error"] = error

        event = RunEvent(
            run_id=self.run_id,
            event_type="tool.result",
            data=data,
            agent_name=self.agent_name,
            sequence_number=self.sequence_counter,
            error=error if not success else None,
            metrics={"durationMs": duration_ms} if duration_ms else None,
        )
        self.event_sink.emit(event)
        self.sequence_counter += 1

    def get_sequence_counter(self) -> int:
        """Get current sequence counter for event ordering"""
        return self.sequence_counter
