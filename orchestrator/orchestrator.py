"""
Loads ACTIVE_MODULES from config.py, imports each one, and calls its
process(envelope) function in order. Pure in-process function calls —
no network, no serialization between stages.

Contract (per team-wide integration spec):
    run_pipeline(envelope: dict) -> dict

Callers build the envelope themselves via utils.envelope_factory.new_envelope
and pass it in — the orchestrator does not build envelopes, it only runs
modules against one.

Usage:
    from utils.envelope_factory import new_envelope
    from orchestrator.orchestrator import run_pipeline

    envelope = new_envelope("some raw nepali text")
    result = run_pipeline(envelope)
"""

import importlib

import orchestrator.config as config
from utils.validate_envelope import validate_envelope
from utils.logger import get_logger

log = get_logger(__name__)


def run_pipeline(envelope: dict) -> dict:
    original_input = envelope.get("original_input")

    for module_path in config.ACTIVE_MODULES:
        try:
            module = importlib.import_module(module_path)
            result = module.process(envelope)

            # Compatibility rule: modules must accept and return the exact
            # same envelope dict shape. If a module returns something else,
            # reject its output entirely rather than propagate a corrupted
            # envelope downstream.
            if not isinstance(result, dict):
                raise TypeError(
                    f"{module_path}.process() must return a dict, got {type(result).__name__}"
                )
            envelope = result
            validate_envelope(envelope)

            # Compatibility rule: original_input is read-only. If a module
            # mutated it, revert and log an error rather than letting the
            # rest of the pipeline see corrupted provenance.
            if envelope.get("original_input") != original_input:
                log.error("module %s mutated original_input; reverting", module_path)
                envelope["original_input"] = original_input
                envelope["errors"].append({
                    "module": module_path,
                    "error": "original_input mutated by module; reverted by orchestrator"
                })

            log.info("ran %s successfully", module_path)
        except Exception as e:
            # Fail soft: log the error into the envelope, keep going.
            # A bad module should not kill the whole pipeline run.
            log.error("module %s failed: %s", module_path, e)
            envelope["errors"].append({
                "module": module_path,
                "error": str(e),
            })
            # restore provenance in case the exception happened mid-mutation
            envelope["original_input"] = original_input

    return envelope


if __name__ == "__main__":
    import json
    from utils.envelope_factory import new_envelope

    envelope = new_envelope("नमस्ते, यो एक परीक्षण वाक्य हो।")
    result = run_pipeline(envelope)
    print(json.dumps(result, ensure_ascii=False, indent=2))
