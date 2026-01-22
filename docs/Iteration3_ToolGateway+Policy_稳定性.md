任务：实现 ToolExecutor + PolicyEngine（最小生产级能力）。

【ToolExecutor】
- 支持 timeoutMs / retry（来自 ToolSpec）
- 每次调用必须发：
  - tool_call
  - tool_result
- 失败不抛裸异常，写 error payload

【PolicyEngine（最小）】
- allow / deny tool.call
- 决策必须产出：
  - policy_allow
  - policy_deny 事件

【集成】
- run-local 中接入 ToolExecutor + PolicyEngine

【交付】
- ToolExecutor 实现
- PolicyEngine 实现
- 一个 deny tool 的示例
