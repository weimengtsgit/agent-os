# Iteration 0：骨架
pip install -e ./control-plane

pip install -e ./agent-runtime/agno

agentctl --help

# Iteration 1：Schema/校验
# 验证单个文件
agentctl validate agents/sample-agent/agent.yaml

# 验证整个目录（递归，默认）
agentctl validate agents/

# 验证目录（详细输出）
agentctl validate agents/ --verbose

# 验证目录（非递归）
agentctl validate agents/ --no-recursive

# Iteration 2：run-local + events
# 1. 使用输入文件
agentctl run-local agents/sample-agent/agent.yaml --input agents/sample-agent/input.json

# 2. 使用 JSON 字符串
agentctl run-local agents/sample-agent/agent.yaml --input-json '{"query": "hello"}'

# 3. 指定 agent 目录（自动查找 agent.yaml）
agentctl run-local agents/sample-agent/ --input agents/sample-agent/input.json

# 4. 指定输出目录
agentctl run-local agents/sample-agent/agent.yaml --input agents/sample-agent/input.json --output my-run

# 5. 指定 runtime（默认是 agno）
agentctl run-local agents/sample-agent/agent.yaml --input agents/sample-agent/input.json --runtime agno

