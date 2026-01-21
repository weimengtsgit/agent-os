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

任务：补齐平台可用性与可维护性。
要求：
- console/minimal：提供两个 HTTP 页面：
  1) /runs：列出 runs（读取 runs 目录或 sqlite）
  2) /runs/<id>：展示 events.jsonl + artifacts
  3) 如果有 human_review_request，提供 approve/reject 操作
- contract tests：固定输入跑 sample agent，断言 events 序列与关键字段
- dependency guard：CI 中阻止 agents/ 与 platform-core/sdk import agno
交付：代码 + 本地启动命令 + CI workflow 文件
