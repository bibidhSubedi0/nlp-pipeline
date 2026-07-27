"""
Adapter for 'code' provider_type.

Imports a Python module by its entry_point (dotted path like
'modules.sentiment_analyzer') and delegates to its process(envelope)
function. This is the simplest adapter — the provider just ships a
Python file that follows the standard module contract.
"""

import importlib

from registry.adapter import BaseAdapter
from utils.envelope_factory import now_iso
from utils.logger import get_logger

log = get_logger("adapter.code")


class CodeAdapter(BaseAdapter):

    def load(self) -> None:
        entry = self.manifest["config"]["entry_point"]
        try:
            self._module = importlib.import_module(entry)
        except ImportError as e:
            raise ImportError(
                f"Cannot import entry_point '{entry}' for module "
                f"'{self.module_id}': {e}"
            ) from e

        if not hasattr(self._module, "process"):
            raise AttributeError(
                f"Module '{entry}' does not expose a process(envelope) function"
            )
        log.info("loaded code adapter: %s -> %s", self.module_id, entry)

    def process(self, envelope: dict) -> dict:
        return self._module.process(envelope)
