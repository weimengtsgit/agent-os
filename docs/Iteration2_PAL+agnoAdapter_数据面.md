任务：实现 PAL 接口 + agno Runtime Adapter（最小可运行）。

【PAL 接口（control-plane）】
在 agent_control_plane/pal/ 中定义：
- AgentRuntime
- ToolExecutor
- EventSink
- TraceSink
- PolicyEngine（先空实现）

【Runtime Adapter（agno）】
在 agent_runtime_agno/adapters/ 中实现：
- AgnoRuntimeAdapter
- 输入：AgentSpec + user input（json）
- 输出：runs/<runId>/events.jsonl

【事件要求】
至少包含：
- run_start
- tool_call
- tool_result
- run_end
失败时：run_error

【CLI】
- agentctl run-local --agent agents/sample-agent/agent.yaml --input input.json

【硬约束】
- control-plane 代码禁止 import agno
- agno 依赖只允许在 agent_runtime_agno 内

【交付】
- PAL 接口代码
- agno adapter 完整实现
- events.jsonl 示例片段
