#!/bin/bash
set -euo pipefail

# Agent OS - Import Guard Script
# Ensures control-plane and agents do not import agno runtime

echo "🔍 Import Guard: Checking for forbidden agno imports..."
echo ""

VIOLATIONS=0

# Function to check for imports
check_imports() {
    local dir="$1"
    local name="$2"

    echo "Checking ${name}..."

    # Search for direct imports: import agno, from agno
    if grep -r --include="*.py" -E "(^import agno|^from agno|import agent_runtime_agno|from agent_runtime_agno)" "$dir" 2>/dev/null; then
        echo "❌ Found forbidden agno imports in ${name}"
        VIOLATIONS=$((VIOLATIONS + 1))
    else
        echo "✅ No violations in ${name}"
    fi
    echo ""
}

# Check control-plane
if [ -d "control-plane" ]; then
    check_imports "control-plane" "control-plane"
else
    echo "⚠️  control-plane directory not found"
fi

# Check agents
if [ -d "agents" ]; then
    check_imports "agents" "agents"
else
    echo "⚠️  agents directory not found"
fi

# Check console (if exists)
if [ -d "console" ]; then
    check_imports "console" "console"
fi

# Check tests (except agent-runtime tests)
if [ -d "tests" ]; then
    # Exclude tests that are specifically for runtime testing
    if find tests -name "*.py" -type f | xargs grep -l "import agno\|from agno\|import agent_runtime_agno\|from agent_runtime_agno" 2>/dev/null | grep -v "test_runtime" > /dev/null; then
        echo "❌ Found forbidden agno imports in tests"
        VIOLATIONS=$((VIOLATIONS + 1))
    else
        echo "✅ No violations in tests"
    fi
    echo ""
fi

echo "=========================================="
if [ $VIOLATIONS -eq 0 ]; then
    echo "✅ Import Guard PASSED: No forbidden imports found"
    exit 0
else
    echo "❌ Import Guard FAILED: Found ${VIOLATIONS} violation(s)"
    echo ""
    echo "Architecture Rule:"
    echo "  - control-plane, agents, console, tests MUST NOT import agno"
    echo "  - Only agent-runtime/agno can import agno"
    exit 1
fi
