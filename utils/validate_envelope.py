"""
Validates a pipeline envelope dict against schema/envelope_schema.json.

Every module should call validate_envelope(envelope) before returning it,
so a corrupted envelope shape is caught immediately instead of silently
breaking three stages downstream.
"""

import json
import os
import jsonschema

_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "schema", "envelope_schema.json")

with open(_SCHEMA_PATH, encoding="utf-8") as f:
    SCHEMA = json.load(f)


def validate_envelope(envelope: dict) -> None:
    """
    Raises jsonschema.exceptions.ValidationError if envelope doesn't match
    the shared schema. Returns None (no return value) if valid.
    """
    jsonschema.validate(instance=envelope, schema=SCHEMA)
