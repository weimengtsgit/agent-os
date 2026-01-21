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

任务：初始化 mono-repo 骨架（不实现业务逻辑也要可运行）。
要求：
- 创建目录结构：platform-core/specs/pal/registry/sdk/cli，agent-runtime-agno/adapters，agents/sample-agent，console/minimal，runs/
- 提供 pyproject.toml（使用 uv 或 poetry 均可，任选其一，但要能安装运行）
- 提供 agentctl CLI 骨架：agentctl --help 能工作，包含子命令 validate/run-local/register/list/show/replay（先空实现也行）
- 提供 README：包含环境安装与运行命令
交付：给出所有文件内容
