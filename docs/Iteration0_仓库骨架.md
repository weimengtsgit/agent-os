任务：初始化 Agent OS mono-repo 的工程骨架（不实现业务逻辑，也必须可运行）。

【目录结构（必须完全一致）】

agent-os/
├── control-plane/
│   ├── agent_control_plane/
│   │   ├── __init__.py
│   │   ├── specs/
│   │   ├── pal/
│   │   ├── registry/
│   │   └── sdk/
│   │       └── cli/
│   └── pyproject.toml
│
├── agent-runtime/
│   └── agno/
│       ├── agent_runtime_agno/
│       │   ├── __init__.py
│       │   └── adapters/
│       └── pyproject.toml
│
├── agents/
│   └── sample-agent/
│       └── agent.yaml
│
├── runs/
├── README.md

【要求】
1. control-plane 是可安装 Python 包（pip install -e ./control-plane）
2. 提供 agentctl CLI 骨架（Typer 或 argparse 均可）
   - 子命令：validate / run-local / register / list / show / replay
   - 先允许空实现，但必须能运行
3. README 写清楚：
   - 架构说明（Control Plane / Runtime）
   - 本地开发安装方式

【交付】
- 所有文件的完整内容
- 本地运行命令
- agentctl --help 的示例输出
