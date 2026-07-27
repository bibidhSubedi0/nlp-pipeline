"""
Base adapter interface for all module provider types.

Every provider_type (huggingface, code, api) gets an adapter class that:
1. Takes a module manifest dict
2. Exposes process(envelope) -> dict  (same contract as native modules)

The orchestrator never knows which adapter is behind a module — it just
calls process() on whatever the registry hands it.
"""

from abc import ABC, abstractmethod


class BaseAdapter(ABC):

    def __init__(self, manifest: dict):
        self.manifest = manifest
        self.module_id = manifest["module_id"]
        self.annotations_key = manifest.get("annotations_key", self.module_id)
        self.behavior = manifest.get("behavior", "annotate")

    @abstractmethod
    def load(self) -> None:
        """Initialize resources (download model, import module, verify endpoint)."""
        ...

    @abstractmethod
    def process(self, envelope: dict) -> dict:
        """Run the module against an envelope, returning the (possibly mutated) envelope."""
        ...

    def unload(self) -> None:
        """Release resources. Default is no-op."""
        pass
