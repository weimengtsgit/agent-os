# Agent OS - 关键文件内容速查

## 1. pyproject.toml

```toml
[project]
name = "agent-os"
version = "0.1.0"
description = "Spec-first, decoupled Agent OS platform"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1.7",
    "pydantic>=2.5.0",
    "jsonschema>=4.20.0",
    "pyyaml>=6.0.1",
    "rich>=13.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.1",
    "black>=23.12.0",
    "ruff>=0.1.8",
]
runtime-agno = [
    "agno>=0.1.0",
]

[project.scripts]
agentctl = "platform_core.cli.main:cli"
```

## 2. platform_core/sdk/models.py

核心数据模型：
- `AgentSpec` - Agent 规范
- `ToolSpec` - Tool 规范
- `PolicySpec` - Policy 规范
- `RunEvent` - 运行事件（支持 JSONL 序列化）

## 3. platform_core/sdk/validator.py

JSON Schema 校验器：
- 自动加载 specs/ 目录下的所有 schema
- 提供 `validate_agent()`, `validate_tool()`, `validate_policy()` 方法

## 4. platform_core/sdk/runtime.py

`RuntimeAdapter` 抽象接口：
- `initialize()` - 初始化运行时
- `run()` - 执行 agent 并产出事件流
- `cleanup()` - 清理资源

## 5. platform_core/cli/main.py

CLI 命令：
- `validate` - 校验规范文件
- `register` - 注册到注册表
- `list` - 列出已注册项
- `show` - 显示详情
- `run-local` - 本地运行（stub）
- `replay` - 回放事件（stub）

## 6. agent_runtime_agno/adapters/agno_adapter.py

`AgnoRuntimeAdapter` 实现：
- 实现 `RuntimeAdapter` 接口
- 这是唯一可以导入 agno 的地方
- 当前为 stub 实现，产出示例事件

## 7. agents/sample-agent/agent.json

示例 Agent 规范：
```json
{
  "id": "sample-agent",
  "name": "Sample Agent",
  "version": "1.0.0",
  "description": "A sample agent for testing the Agent OS platform",
  "runtime": "agno",
  "tools": ["echo-tool"],
  "policies": ["basic-policy"],
  "config": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

## 8. platform_core/specs/agent.schema.json

Agent JSON Schema：
- 定义 Agent 规范的结构
- 必填字段：id, name, version, runtime, tools, policies
- runtime 枚举：agno, langchain, custom

## 快速命令参考

```bash
# 安装
pip install -e ".[dev]"

# 校验
agentctl validate <file> --type <agent|tool|policy>

# 注册
agentctl register <file> --type <agent|tool|policy>

# 查询
agentctl list --type agent
agentctl show <id> --type agent

# 运行（stub）
agentctl run-local <agent-id> --output-dir runs/xxx

# 测试
pytest tests/ -v

# 验证 MVP
./verify_mvp.sh
```

## 架构关键点

1. **依赖隔离**：
   - `platform_core/` - 无 agno 依赖
   - `agents/` - 无 agno 依赖
   - `agent_runtime_agno/` - 唯一可用 agno

2. **Spec-first**：
   - 所有规范都有 JSON Schema
   - 运行前强制校验
   - 规范即文档

3. **事件驱动**：
   - `RunEvent` 模型
   - JSONL 格式输出
   - 支持回放

4. **可扩展**：
   - `RuntimeAdapter` 接口
   - 可添加新运行时
   - 插件化设计

## 下一步实现优先级

1. **高优先级**：
   - 实现真实的 AgnoRuntimeAdapter
   - 实现事件流式输出
   - 实现回放功能

2. **中优先级**：
   - 实现 Policy 执行
   - 完善 list 命令（tool, policy）
   - 添加版本管理

3. **低优先级**：
   - Web Console
   - 远程注册表
   - 认证授权
