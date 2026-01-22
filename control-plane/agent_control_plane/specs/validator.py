"""
Spec Validator

Validates Agent OS specs against JSON Schema.
Supports automatic schema selection based on 'kind' field.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import jsonschema
import yaml
from rich.console import Console
from rich.table import Table

console = Console()

# Schema directory
SCHEMA_DIR = Path(__file__).parent / "schemas"

# Schema mapping: kind -> schema file
SCHEMA_MAP = {
    "Agent": "agent.schema.json",
    "Tool": "tool.schema.json",
    "Policy": "policy.schema.json",
    "RunEvent": "runevent.schema.json",
    "TraceSpan": "tracespan.schema.json",
}


class ValidationError(Exception):
    """Validation error with detailed information"""

    def __init__(self, message: str, path: Optional[str] = None, errors: Optional[List] = None):
        self.message = message
        self.path = path
        self.errors = errors or []
        super().__init__(message)


class SpecValidator:
    """Validator for Agent OS specs"""

    def __init__(self):
        self.schemas: Dict[str, dict] = {}
        self._load_schemas()

    def _load_schemas(self):
        """Load all JSON schemas from the schemas directory"""
        for kind, schema_file in SCHEMA_MAP.items():
            schema_path = SCHEMA_DIR / schema_file
            if not schema_path.exists():
                console.print(f"[yellow]Warning: Schema file not found: {schema_path}[/yellow]")
                continue

            try:
                with open(schema_path, "r") as f:
                    self.schemas[kind] = json.load(f)
            except Exception as e:
                console.print(f"[red]Error loading schema {schema_file}: {e}[/red]")

    def _load_spec_file(self, path: Union[str, Path]) -> dict:
        """Load a spec file (YAML or JSON)"""
        path = Path(path)
        if not path.exists():
            raise ValidationError(f"File not found: {path}", path=str(path))

        try:
            with open(path, "r") as f:
                if path.suffix in [".yaml", ".yml"]:
                    return yaml.safe_load(f)
                elif path.suffix == ".json":
                    return json.load(f)
                else:
                    raise ValidationError(
                        f"Unsupported file format: {path.suffix}. Use .yaml, .yml, or .json",
                        path=str(path),
                    )
        except yaml.YAMLError as e:
            raise ValidationError(f"YAML parsing error: {e}", path=str(path))
        except json.JSONDecodeError as e:
            raise ValidationError(f"JSON parsing error: {e}", path=str(path))
        except Exception as e:
            raise ValidationError(f"Error reading file: {e}", path=str(path))

    def _get_schema_for_kind(self, kind: str) -> Optional[dict]:
        """Get the schema for a given kind"""
        return self.schemas.get(kind)

    def validate_spec(self, spec: dict, path: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate a spec against its schema.

        Args:
            spec: The spec dictionary to validate
            path: Optional file path for error reporting

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check if 'kind' field exists
        if "kind" not in spec:
            errors.append("Missing required field: 'kind'")
            return False, errors

        kind = spec["kind"]

        # Get the appropriate schema
        schema = self._get_schema_for_kind(kind)
        if schema is None:
            errors.append(f"Unknown kind: '{kind}'. Supported kinds: {', '.join(SCHEMA_MAP.keys())}")
            return False, errors

        # Validate against schema
        try:
            jsonschema.validate(instance=spec, schema=schema)
            return True, []
        except jsonschema.ValidationError as e:
            # Format validation error
            error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
            error_msg = f"Validation error at '{error_path}': {e.message}"
            errors.append(error_msg)

            # Add context if available
            if e.context:
                for ctx_error in e.context:
                    ctx_path = " -> ".join(str(p) for p in ctx_error.path) if ctx_error.path else "root"
                    errors.append(f"  - at '{ctx_path}': {ctx_error.message}")

            return False, errors
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e.message}")
            return False, errors
        except Exception as e:
            errors.append(f"Unexpected validation error: {e}")
            return False, errors

    def validate_file(self, path: Union[str, Path], verbose: bool = False) -> bool:
        """
        Validate a single spec file.

        Args:
            path: Path to the spec file
            verbose: Print detailed validation information

        Returns:
            True if validation passed, False otherwise
        """
        path = Path(path)

        try:
            # Load the spec
            spec = self._load_spec_file(path)

            # Validate
            is_valid, errors = self.validate_spec(spec, path=str(path))

            if is_valid:
                console.print(f"[green]✓[/green] {path} - Valid {spec.get('kind', 'Unknown')} spec")
                if verbose:
                    console.print(f"  [dim]→ Name: {spec.get('metadata', {}).get('name', 'N/A')}[/dim]")
                    console.print(f"  [dim]→ API Version: {spec.get('apiVersion', 'N/A')}[/dim]")
                return True
            else:
                console.print(f"[red]✗[/red] {path} - Validation failed")
                for error in errors:
                    console.print(f"  [red]→ {error}[/red]")
                return False

        except ValidationError as e:
            console.print(f"[red]✗[/red] {path} - {e.message}")
            if e.errors:
                for error in e.errors:
                    console.print(f"  [red]→ {error}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]✗[/red] {path} - Unexpected error: {e}")
            return False

    def validate_dir(
        self, dir_path: Union[str, Path], recursive: bool = True, verbose: bool = False
    ) -> Tuple[int, int]:
        """
        Validate all spec files in a directory.

        Args:
            dir_path: Path to the directory
            recursive: Recursively validate subdirectories
            verbose: Print detailed validation information

        Returns:
            Tuple of (valid_count, total_count)
        """
        dir_path = Path(dir_path)

        if not dir_path.exists():
            console.print(f"[red]Directory not found: {dir_path}[/red]")
            return 0, 0

        if not dir_path.is_dir():
            console.print(f"[red]Not a directory: {dir_path}[/red]")
            return 0, 0

        # Find all spec files
        patterns = ["*.yaml", "*.yml", "*.json"]
        spec_files = []

        for pattern in patterns:
            if recursive:
                spec_files.extend(dir_path.rglob(pattern))
            else:
                spec_files.extend(dir_path.glob(pattern))

        if not spec_files:
            console.print(f"[yellow]No spec files found in {dir_path}[/yellow]")
            return 0, 0

        console.print(f"\n[bold]Validating {len(spec_files)} file(s) in {dir_path}[/bold]\n")

        # Validate each file
        valid_count = 0
        for spec_file in sorted(spec_files):
            if self.validate_file(spec_file, verbose=verbose):
                valid_count += 1

        # Summary
        console.print(f"\n[bold]Summary:[/bold]")
        table = Table(show_header=False, box=None)
        table.add_row("Total files:", str(len(spec_files)))
        table.add_row("Valid:", f"[green]{valid_count}[/green]")
        table.add_row("Invalid:", f"[red]{len(spec_files) - valid_count}[/red]")
        console.print(table)

        return valid_count, len(spec_files)


# Convenience functions
_validator = None


def get_validator() -> SpecValidator:
    """Get or create the global validator instance"""
    global _validator
    if _validator is None:
        _validator = SpecValidator()
    return _validator


def validate_file(path: Union[str, Path], verbose: bool = False) -> bool:
    """Validate a single spec file"""
    return get_validator().validate_file(path, verbose=verbose)


def validate_dir(
    dir_path: Union[str, Path], recursive: bool = True, verbose: bool = False
) -> Tuple[int, int]:
    """Validate all spec files in a directory"""
    return get_validator().validate_dir(dir_path, recursive=recursive, verbose=verbose)


def validate_spec(spec: dict, path: Optional[str] = None) -> Tuple[bool, List[str]]:
    """Validate a spec dictionary"""
    return get_validator().validate_spec(spec, path=path)
