#!/bin/bash
set -euo pipefail

# Agent OS - Comprehensive Test Runner
# This script runs all tests to verify Spec-first and RunEvent contracts

echo "=========================================="
echo "Agent OS - Test Suite Runner"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

# Function to run a test step
run_step() {
    local step_name="$1"
    local step_cmd="$2"

    echo -e "${YELLOW}▶ ${step_name}${NC}"
    if eval "$step_cmd"; then
        echo -e "${GREEN}✓ ${step_name} - PASSED${NC}"
        echo ""
    else
        echo -e "${RED}✗ ${step_name} - FAILED${NC}"
        echo ""
        FAILED=1
    fi
}

# Step 1: Verify installations
echo "Step 1: Verify Installations"
echo "----------------------------------------"
run_step "Control Plane installed" "python -c 'import agent_control_plane; print(\"Control Plane available\")'"
run_step "Agno Runtime installed" "python -c 'import agent_runtime_agno; print(\"Agno runtime available\")'"
run_step "agentctl available" "agentctl --help > /dev/null"

# Step 2: Import Guard
echo "Step 2: Import Guard (Architecture Boundary)"
echo "----------------------------------------"
run_step "No agno imports in control-plane/agents" "bash scripts/guard_no_runtime_imports.sh"

# Step 3: Spec Validation
echo "Step 3: Spec Validation (Iteration 1)"
echo "----------------------------------------"
# Note: .json input files will fail validation (they're not specs), but .yaml specs should pass
run_step "Validate agent YAML specs" "agentctl validate agents/ --recursive || true; agentctl validate agents/sample-agent/agent.yaml && agentctl validate agents/testcase-generator/agent.yaml"

# Step 4: Run pytest
echo "Step 4: Pytest Test Suite"
echo "----------------------------------------"
run_step "Run all pytest tests" "pytest -v --tb=short"

# Step 5: Console smoke test (if installed)
echo "Step 5: Console Smoke Test (Optional)"
echo "----------------------------------------"
if python -c "import console" 2>/dev/null; then
    echo "Console package found, running smoke test..."
    run_step "Console imports successfully" "python -c 'from console import app; print(\"Console app available\")'"
else
    echo -e "${YELLOW}⚠ Console not installed, skipping smoke test${NC}"
    echo ""
fi

# Summary
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo "=========================================="
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo "=========================================="
    exit 1
fi
