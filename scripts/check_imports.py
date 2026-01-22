#!/usr/bin/env python3
"""
Import Guard Script

Ensures architectural boundaries are maintained:
- control-plane MUST NOT import agno
- agents MUST NOT import agno
- Only agent-runtime/agno can import agno
"""

import ast
import sys
from pathlib import Path
from typing import List, Set, Tuple


class ImportChecker(ast.NodeVisitor):
    """AST visitor to check imports"""

    def __init__(self):
        self.imports: Set[str] = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module.split('.')[0])
        self.generic_visit(node)


def check_file(file_path: Path) -> Set[str]:
    """Check a single Python file for imports"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        checker = ImportChecker()
        checker.visit(tree)
        return checker.imports
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")
        return set()


def check_directory(
    directory: Path,
    forbidden_imports: List[str],
    exclude_dirs: List[str] = None
) -> List[Tuple[Path, str]]:
    """
    Check all Python files in directory for forbidden imports.

    Returns:
        List of (file_path, forbidden_import) tuples
    """
    violations = []
    exclude_dirs = exclude_dirs or []

    for py_file in directory.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue

        imports = check_file(py_file)

        for forbidden in forbidden_imports:
            if forbidden in imports:
                violations.append((py_file, forbidden))

    return violations


def main():
    """Run import guard checks"""
    repo_root = Path(__file__).parent.parent

    print("🔍 Running Import Guard checks...")
    print()

    all_violations = []

    # Check 1: control-plane must not import agno
    print("Checking control-plane for agno imports...")
    control_plane_dir = repo_root / "control-plane"
    if control_plane_dir.exists():
        violations = check_directory(
            control_plane_dir,
            ["agno", "agent_runtime_agno"],
            exclude_dirs=["__pycache__", ".pytest_cache", "build", "dist"]
        )

        if violations:
            print(f"  ❌ Found {len(violations)} violation(s):")
            for file_path, import_name in violations:
                rel_path = file_path.relative_to(repo_root)
                print(f"     {rel_path}: imports '{import_name}'")
            all_violations.extend(violations)
        else:
            print("  ✅ No violations found")

    print()

    # Check 2: agents directory must not import agno
    print("Checking agents for agno imports...")
    agents_dir = repo_root / "agents"
    if agents_dir.exists():
        violations = check_directory(
            agents_dir,
            ["agno", "agent_runtime_agno"],
            exclude_dirs=["__pycache__"]
        )

        if violations:
            print(f"  ❌ Found {len(violations)} violation(s):")
            for file_path, import_name in violations:
                rel_path = file_path.relative_to(repo_root)
                print(f"     {rel_path}: imports '{import_name}'")
            all_violations.extend(violations)
        else:
            print("  ✅ No violations found")

    print()

    # Check 3: console must not import agno
    print("Checking console for agno imports...")
    console_dir = repo_root / "console"
    if console_dir.exists():
        violations = check_directory(
            console_dir,
            ["agno", "agent_runtime_agno"],
            exclude_dirs=["__pycache__"]
        )

        if violations:
            print(f"  ❌ Found {len(violations)} violation(s):")
            for file_path, import_name in violations:
                rel_path = file_path.relative_to(repo_root)
                print(f"     {rel_path}: imports '{import_name}'")
            all_violations.extend(violations)
        else:
            print("  ✅ No violations found")

    print()
    print("=" * 60)

    if all_violations:
        print(f"❌ Import Guard FAILED: {len(all_violations)} violation(s) found")
        print()
        print("Architectural Rule:")
        print("  - control-plane, agents, console MUST NOT import agno")
        print("  - Only agent-runtime/agno can import agno")
        print()
        sys.exit(1)
    else:
        print("✅ Import Guard PASSED: All checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
