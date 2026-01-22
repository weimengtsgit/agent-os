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
