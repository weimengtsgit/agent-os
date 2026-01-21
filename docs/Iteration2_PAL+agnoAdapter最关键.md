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

任务：实现 PAL 接口 + agno Runtime Adapter（最小可运行）。
要求：
- platform-core/pal: 定义 AgentRuntime/ToolExecutor/LLMProvider/MemoryStore/EventSink/TraceSink/PolicyEngine 的接口与最小实现（可用本地文件/内存实现）
- agent-runtime-agno/adapters: 实现 AgnoRuntimeAdapter
  - 输入：AgentSpec + user input json
  - 输出：生成 runs/<runId>/events.jsonl（RunEvent 符合 schema）
  - 事件至少包含：run_start、tool_call、tool_result、run_end；失败时 run_error；取消 run_cancel（取消先留 TODO 也可）
- agentctl run-local：读取 agents/<agent>/agent.yaml，加载 promptRef，选择 runtime=agno，执行并输出最终结果
- 提供一个最简单 tool：echo（返回原文本），并演示工具调用事件
交付：新增/修改文件内容 + 运行命令 + 预期 events.jsonl 示例片段
