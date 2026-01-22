任务：在 control-plane 中落地 Spec-first 机制。

【Spec 范围】
- AgentSpec
- ToolSpec
- PolicySpec
- RunEvent
- TraceSpan

【要求】
1. 在 agent_control_plane/specs/schemas/ 中创建 5 个 JSON Schema 文件
2. 实现 agent_control_plane/specs/validator.py
   - validate_file(path)
   - validate_dir(dir)
   - 根据 kind 自动选择 schema
3. 实现 agentctl validate：
   - 校验 agents/ 下的 agent.yaml、*.tool.yaml、policy.yaml
4. 提供一个 sample agent + sample tool YAML，可通过校验

【硬约束】
- Schema 使用 jsonschema
- 校验失败必须给出明确错误信息

【交付】
- 所有 schema 文件内容
- validator.py 完整代码
- agentctl validate 的运行示例
