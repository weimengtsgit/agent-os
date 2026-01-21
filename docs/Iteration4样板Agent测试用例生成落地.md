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

任务：实现样板 Agent：测试用例生成（MVP）。
范围（先 mock 再对接）：
- requirements_reader tool：输入 requirementId 或 text，输出 {title, description, acceptanceCriteria}
- testcase_generator：LLM 输出结构化 testcases.json（按我给的 JSON 格式）
- testcase_validator tool：检查必填、重复、覆盖（输出报告）
- human_review：生成 human_review_request 事件，提供一个简易的 approve/reject CLI（agentctl review --runId ...）
- testcase_writer tool：把最终用例写到 runs/<runId>/artifacts/testcases.json（或 markdown）
要求：
- 所有步骤都有 RunEvent 记录
- 最终 run_end payload 指向 artifactPath
交付：代码 + 示例输入 + 一次完整运行的 demo 命令
