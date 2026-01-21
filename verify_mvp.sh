#!/bin/bash
# Agent OS MVP 验证脚本

set -e

echo "=========================================="
echo "Agent OS MVP 验证"
echo "=========================================="
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

echo "1. 测试 CLI 帮助命令..."
agentctl --help > /dev/null
echo "   ✅ CLI 帮助命令正常"
echo ""

echo "2. 测试 Agent 规范校验..."
agentctl validate agents/sample-agent/agent.json --type agent > /dev/null
echo "   ✅ Agent 规范校验通过"
echo ""

echo "3. 测试 Tool 规范校验..."
agentctl validate agents/sample-agent/tools/echo-tool.json --type tool > /dev/null
echo "   ✅ Tool 规范校验通过"
echo ""

echo "4. 测试 Policy 规范校验..."
agentctl validate agents/sample-agent/policies/basic-policy.json --type policy > /dev/null
echo "   ✅ Policy 规范校验通过"
echo ""

echo "5. 测试注册功能..."
agentctl register agents/sample-agent/agent.json --type agent > /dev/null
agentctl register agents/sample-agent/tools/echo-tool.json --type tool > /dev/null
agentctl register agents/sample-agent/policies/basic-policy.json --type policy > /dev/null
echo "   ✅ 注册功能正常"
echo ""

echo "6. 测试列表功能..."
agentctl list --type agent > /dev/null
echo "   ✅ 列表功能正常"
echo ""

echo "7. 测试查看功能..."
agentctl show sample-agent --type agent > /dev/null
echo "   ✅ 查看功能正常"
echo ""

echo "8. 运行测试套件..."
pytest tests/ -q
echo "   ✅ 所有测试通过"
echo ""

echo "=========================================="
echo "✅ MVP 验证完成！所有功能正常工作"
echo "=========================================="
echo ""
echo "下一步："
echo "  - 查看 README.md 了解使用方法"
echo "  - 查看 DELIVERY.md 了解交付内容"
echo "  - 开始实现 agno 运行时"
