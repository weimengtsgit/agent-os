"""Spec validator using JSON Schema."""

import json
from pathlib import Path
from typing import Dict, Any
import jsonschema
from jsonschema import validate, ValidationError


class SpecValidator:
    """Validates specs against JSON schemas."""

    def __init__(self, schema_dir: Path = None):
        """Initialize validator with schema directory."""
        if schema_dir is None:
            schema_dir = Path(__file__).parent.parent / "specs"
        self.schema_dir = schema_dir
        self._schemas: Dict[str, Any] = {}
        self._load_schemas()

    def _load_schemas(self):
        """Load all JSON schemas."""
        for schema_file in self.schema_dir.glob("*.schema.json"):
            schema_name = schema_file.stem.replace(".schema", "")
            with open(schema_file) as f:
                self._schemas[schema_name] = json.load(f)

    def validate_agent(self, spec: Dict[str, Any]) -> bool:
        """Validate agent spec."""
        try:
            validate(instance=spec, schema=self._schemas["agent"])
            return True
        except ValidationError as e:
            raise ValueError(f"Agent validation failed: {e.message}")

    def validate_tool(self, spec: Dict[str, Any]) -> bool:
        """Validate tool spec."""
        try:
            validate(instance=spec, schema=self._schemas["tool"])
            return True
        except ValidationError as e:
            raise ValueError(f"Tool validation failed: {e.message}")

    def validate_policy(self, spec: Dict[str, Any]) -> bool:
        """Validate policy spec."""
        try:
            validate(instance=spec, schema=self._schemas["policy"])
            return True
        except ValidationError as e:
            raise ValueError(f"Policy validation failed: {e.message}")
