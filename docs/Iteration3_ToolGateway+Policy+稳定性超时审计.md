你是企业级平台工程师。你要在一个 mono-repo 中实现 Agent OS（Spec-first、可解耦）。
硬性要求：
1) 业务 agents/ 与 platform-core/sdk 不得直接依赖 agno；agno 只能出现在 agent-runtime-agno/ 内。
2) 所有 Agent 运行必须产出 RunEvent（JSONL）并可回放。
3) 启动 Agent 前必须通过 JSON Schema 校验（Agent/Tool/Policy）。
4) 以可运行 MVP 为目标；每次改动必须附带最小可运行示例与命令。
5) 代码优先：Python（CLI + runtime），Console 用最小 Web（可选）。
输出要求：
- 给出需要新增/修改的文件列表
- 给出每个文件的完整内容
- 给出本地运行命令与预期输出
- 给出最小测试（pytest）或验证步骤

任务：实现 ToolExecutor 的生产化最小能力 + PolicyEngine。
要求：
- ToolExecutor.execute 必须：
  - 发 tool_call / tool_result 事件
  - 支持 timeoutMs、retry（来自 ToolSpec）
  - 失败记录 error payload（不抛出裸异常）
- PolicyEngine 最小实现：
  - allow/deny tool.call（基于 AgentSpec.policiesRef 或 AgentSpec.spec.tools 白名单）
  - 每次决策发 policy_allow/policy_deny 事件（RunEvent）
- 在 run-local 的执行中接入 policy 与 tool gateway
交付：文件内容 + 最小测试（pytest）覆盖超时/重试/deny
