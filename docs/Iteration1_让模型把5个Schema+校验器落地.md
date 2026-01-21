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

任务：落地 Spec-first 的 JSON Schema 校验。
已有约束：schemas 已确定为 agent/tool/run-event/trace-span/policy。
要求：
- 在 platform-core/specs/schemas/ 写入 5 个 JSON Schema 文件（按我提供的 schema 内容原样）
- 实现 platform-core/specs/validator.py：validate_file(path, schema_name) + validate_dir(dir)
- 实现 agentctl validate：校验 agents/ 下的 agent.yaml、*.tool.yaml、policy.yaml（按 kind 自动选 schema）
- 给出一个 sample agent + sample tool 的 YAML（可通过校验）
交付：文件内容 + 运行命令 + 预期输出
