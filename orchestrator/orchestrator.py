import importlib

from utils.validate_envelope import validate_envelope
from utils.logger import get_logger
import orchestrator.config as cfg

logger = get_logger("orchestrator")


def run_pipeline(envelope: dict) -> dict:
    validate_envelope(envelope)
    original_input = envelope["original_input"]

    for module_name in cfg.ACTIVE_MODULES:
        try:
            module = importlib.import_module(f"modules.{module_name}")
        except Exception:
            logger.warning("Module '%s' not found or broken, skipping.", module_name)
            envelope["errors"].append({
                "module": module_name,
                "error": "module not found or broken, skipped",
            })
            continue

        try:
            envelope = module.process(envelope)
            validate_envelope(envelope)
        except Exception as e:
            logger.error("Module '%s' failed: %s", module_name, e)
            envelope["errors"].append({
                "module": module_name,
                "error": str(e),
            })

        if envelope["original_input"] != original_input:
            envelope["original_input"] = original_input
            envelope["errors"].append({
                "module": module_name,
                "error": "module mutated original_input, reverted",
            })

    return envelope
