"""
Policy Engine Implementation

Provides policy enforcement for agent execution:
- Tool call authorization
- Policy decision events
- Configurable allow/deny rules
"""

from typing import Any, Dict, List, Optional

from agent_control_plane.pal.interfaces import EventSink, PolicyEngine, RunEvent


class DefaultPolicyEngine(PolicyEngine):
    """
    DefaultPolicyEngine implements policy enforcement with:
    - Tool call authorization based on policy specs
    - Policy decision event emission
    - Configurable allow/deny rules
    """

    def __init__(
        self,
        policies: List[Dict[str, Any]],
        event_sink: Optional[EventSink] = None,
        run_id: Optional[str] = None,
        agent_name: Optional[str] = None,
    ):
        """
        Initialize policy engine with policies.

        Args:
            policies: List of policy specs (validated)
            event_sink: Optional event sink for policy decisions
            run_id: Optional run ID for events
            agent_name: Optional agent name for events
        """
        self.policies = policies
        self.event_sink = event_sink
        self.run_id = run_id
        self.agent_name = agent_name
        self.sequence_counter = 0

        # Parse policies into rules
        self.tool_deny_list = set()
        self.tool_allow_list = set()
        self._parse_policies()

    def _parse_policies(self) -> None:
        """Parse policy specs into executable rules"""
        for policy in self.policies:
            policy_type = policy.get("spec", {}).get("type")
            policy_config = policy.get("spec", {}).get("config", {})

            # Handle access-control policies
            if policy_type == "access-control":
                access_control = policy_config.get("accessControl", {})
                denied_tools = access_control.get("deniedTools", [])
                allowed_tools = access_control.get("allowedTools", [])

                self.tool_deny_list.update(denied_tools)
                if allowed_tools:
                    self.tool_allow_list.update(allowed_tools)

            # Handle content-filter policies (can block tools)
            elif policy_type == "content-filter":
                content_filter = policy_config.get("contentFilter", {})
                blocked_tools = content_filter.get("blockedTools", [])
                self.tool_deny_list.update(blocked_tools)

    def validate_run(self, agent_spec: Dict[str, Any], input_data: Dict[str, Any]) -> bool:
        """
        Validate if a run is allowed.

        For MVP, always returns True (run-level policies not implemented).
        """
        return True

    def check_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Check if a tool call is allowed.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters

        Returns:
            True if allowed, False if denied
        """
        # Check deny list first
        if tool_name in self.tool_deny_list:
            self._emit_policy_decision(
                decision="deny",
                resource_type="tool",
                resource_name=tool_name,
                reason=f"Tool '{tool_name}' is in deny list",
                parameters=parameters,
            )
            return False

        # Check allow list (if configured)
        if self.tool_allow_list and tool_name not in self.tool_allow_list:
            self._emit_policy_decision(
                decision="deny",
                resource_type="tool",
                resource_name=tool_name,
                reason=f"Tool '{tool_name}' is not in allow list",
                parameters=parameters,
            )
            return False

        # Allow by default
        self._emit_policy_decision(
            decision="allow",
            resource_type="tool",
            resource_name=tool_name,
            reason="No policy restrictions",
            parameters=parameters,
        )
        return True

    def _emit_policy_decision(
        self,
        decision: str,
        resource_type: str,
        resource_name: str,
        reason: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit policy decision event"""
        if not self.event_sink or not self.run_id:
            return

        event_type = f"policy.{decision}"  # policy.allow or policy.deny

        event = RunEvent(
            run_id=self.run_id,
            event_type=event_type,
            data={
                "decision": decision,
                "resource_type": resource_type,
                "resource_name": resource_name,
                "reason": reason,
                "parameters": parameters or {},
            },
            agent_name=self.agent_name,
            sequence_number=self.sequence_counter,
        )
        self.event_sink.emit(event)
        self.sequence_counter += 1

    def get_sequence_counter(self) -> int:
        """Get current sequence counter for event ordering"""
        return self.sequence_counter
