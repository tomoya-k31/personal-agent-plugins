#!/usr/bin/env python3
"""Validate a Re-TRAC state JSON file against state-schema.json.

Usage:
    python validate_state.py <path/to/state-rN.json>

Exits 0 if the state conforms, 1 if it violates the schema (printing each
violation), 2 on usage / IO errors. Uses the `jsonschema` package if installed,
otherwise a stdlib-only fallback covering the subset of draft-07 that
state-schema.json actually uses (type, required, properties, items, enum,
minimum, maximum). Keeping the fallback means this skill has zero runtime
dependencies — it works regardless of venv state.
"""
import json
import sys
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "state-schema.json"

_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def _type_ok(value, type_name):
    # bool is a subclass of int — never accept True/False as integer/number.
    if type_name in ("integer", "number") and isinstance(value, bool):
        return False
    py = _TYPE_MAP.get(type_name)
    return py is not None and isinstance(value, py)


def _validate(instance, schema, path, errors):
    declared = schema.get("type")
    if declared is not None:
        types = declared if isinstance(declared, list) else [declared]
        if not any(_type_ok(instance, t) for t in types):
            loc = path or "<root>"
            errors.append(f"{loc}: expected type {types}, got {type(instance).__name__}")
            return  # type mismatch — deeper checks would be noise

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in allowed {schema['enum']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} < minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: {instance} > maximum {schema['maximum']}")

    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                loc = path or "<root>"
                errors.append(f"{loc}: missing required field '{req}'")
        for key, subschema in schema.get("properties", {}).items():
            if key in instance:
                child = f"{path}.{key}" if path else key
                _validate(instance[key], subschema, child, errors)

    if isinstance(instance, list):
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(instance):
                _validate(item, item_schema, f"{path}[{i}]", errors)


def validate(instance, schema):
    """Return a list of violation strings (empty == valid)."""
    try:
        import jsonschema
        validator = jsonschema.Draft7Validator(schema)
        return [
            f"{'.'.join(map(str, e.path)) or '<root>'}: {e.message}"
            for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
        ]
    except ImportError:
        errors = []
        _validate(instance, schema, "", errors)
        return errors


def main():
    if len(sys.argv) != 2:
        print("usage: validate_state.py <state.json>", file=sys.stderr)
        return 2
    state_path = Path(sys.argv[1])
    if not state_path.is_file():
        print(f"ERROR: state file not found: {state_path}", file=sys.stderr)
        return 2
    try:
        schema = json.loads(SCHEMA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: cannot load schema {SCHEMA_PATH}: {e}", file=sys.stderr)
        return 2
    try:
        instance = json.loads(state_path.read_text())
    except json.JSONDecodeError as e:
        print(f"INVALID: {state_path} is not valid JSON: {e}", file=sys.stderr)
        return 1

    errors = validate(instance, schema)
    if errors:
        print(f"INVALID: {state_path} ({len(errors)} violation(s)):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"VALID: {state_path} conforms to state-schema.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
