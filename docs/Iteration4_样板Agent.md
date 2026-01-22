你是企业级平台工程师，正在实现一个“Agent OS（Agent 平台）”，其架构严格遵循 Kubernetes 的 CRD / Control Plane / Data Plane 思想。

【核心架构约束（必须遵守）】
1. 使用 Spec-first 架构：
   - Agent / Tool / Policy / RunEvent / Trace 都是正式契约（JSON Schema）
   - 没有通过 Schema 校验的对象，禁止运行
2. 控制面与数据面严格解耦：
   - control-plane = Agent OS 控制面（Spec / Registry / Policy / PAL / CLI）
   - agent-runtime/<name> = Runtime 插件（数据面实现）
3. Runtime 可替换：
   - agno 只是其中一个 runtime 插件
   - control-plane 代码禁止依赖 agno
4. Python 规范：
   - 领域目录可使用 kebab-case（如 control-plane、agent-runtime）
   - Python package 必须使用 snake_case（如 agent_control_plane、agent_runtime_agno）
   - 禁止 sys.path hack 或 importlib 绕过
5. 所有 Agent Run 必须产出 RunEvent（JSONL），事件是唯一事实来源
6. 优先保证“可运行 MVP”，而不是完整功能

【输出要求（每一轮）】
- 列出新增/修改的文件清单
- 给出每个文件的完整代码内容
- 给出本地运行命令
- 给出最小验证方式（CLI 输出 / events.jsonl 示例）


任务：实现样板 Agent：测试用例生成（MVP）。

【工具】
- requirements_reader（先 mock）
- testcase_generator（LLM 输出 JSON）
- testcase_validator（规则校验）
- testcase_writer（写入 runs/<runId>/artifacts/）

【人审】
- 生成 human_review_request 事件
- agentctl review --runId <id> --approve / --reject

【要求】
- 所有步骤产出 RunEvent
- 最终 run_end payload 指向 artifactPath

【交付】
- AgentSpec / ToolSpec
- 示例输入
- 一次完整运行的 demo 命令
