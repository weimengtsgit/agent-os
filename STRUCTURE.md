# Agent OS 目录结构说明

## ✅ 正确的目录命名

**使用下划线（Python 包命名规范）**：
- ✅ `platform_core/` - 核心平台包
- ✅ `agent_runtime_agno/` - Agno 运行时包
- ✅ `agents/` - 业务 agents

**为什么用下划线？**
- Python 包名不能包含连字符（-）
- 下划线（_）是 Python 包的标准命名方式
- 可以直接 `import platform_core` 和 `import agent_runtime_agno`

## 完整目录树

```
agent-os/                          # 项目根目录（可以用连字符）
├── pyproject.toml                 # 项目配置
├── README.md                      # 使用文档
├── DELIVERY.md                    # 交付文档
├── QUICKREF.md                    # 快速参考
├── STRUCTURE.md                   # 本文件
├── .gitignore                     # Git 忽略
├── verify_mvp.sh                  # 验证脚本
│
├── platform_core/                 # ✅ 核心平台（Python 包）
│   ├── __init__.py
│   ├── specs/                     # JSON Schema 定义
│   │   ├── agent.schema.json
│   │   ├── tool.schema.json
│   │   └── policy.schema.json
│   ├── sdk/                       # 核心 SDK
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── validator.py
│   │   └── runtime.py
│   ├── registry/                  # 注册表
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   ├── agents/                # 已注册的 agents
│   │   ├── tools/                 # 已注册的 tools
│   │   └── policies/              # 已注册的 policies
│   └── cli/                       # CLI
│       ├── __init__.py
│       └── main.py
│
├── agent_runtime_agno/            # ✅ Agno 运行时（Python 包）
│   ├── __init__.py
│   └── adapters/
│       ├── __init__.py
│       └── agno_adapter.py
│
├── agents/                        # 业务 agents
│   └── sample-agent/              # 示例 agent（目录名可用连字符）
│       ├── README.md
│       ├── agent.json
│       ├── tools/
│       │   └── echo-tool.json
│       └── policies/
│           └── basic-policy.json
│
├── console/                       # Web 控制台（可选）
│   └── minimal/
│
├── runs/                          # 运行输出
│
└── tests/                         # 测试
    ├── __init__.py
    └── test_cli.py
```

## 命名规则总结

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| Python 包目录 | 下划线 | `platform_core/`, `agent_runtime_agno/` |
| Python 模块文件 | 下划线 | `models.py`, `agno_adapter.py` |
| 项目根目录 | 连字符 | `agent-os/` |
| Agent 目录 | 连字符 | `sample-agent/` |
| JSON 文件 | 连字符 | `agent.json`, `echo-tool.json` |

## 导入示例

```python
# ✅ 正确 - 使用下划线
from platform_core.sdk.models import AgentSpec
from platform_core.sdk.validator import SpecValidator
from agent_runtime_agno.adapters import AgnoRuntimeAdapter

# ❌ 错误 - 不能用连字符
from platform-core.sdk.models import AgentSpec  # SyntaxError!
```

## 验证

运行以下命令确认结构正确：

```bash
# 检查 Python 包可以导入
python3 -c "import platform_core; import agent_runtime_agno; print('✅ 导入成功')"

# 检查 CLI 可用
agentctl --help

# 运行测试
pytest tests/ -v

# 完整验证
./verify_mvp.sh
```
