"""
Module registry: stores manifests, creates adapters, manages the
module lifecycle.

The registry persists to registry/modules.json. Each entry is a full
manifest dict. The registry can create adapter instances on demand,
which expose the same process(envelope) interface the orchestrator
expects.

Usage:
    from registry.registry import Registry
    reg = Registry()
    reg.register(manifest)        # add a module
    adapter = reg.load("sentiment-code")  # get a working adapter
    result = adapter.process(envelope)
"""

import json
import os

import jsonschema

from registry.adapter import BaseAdapter
from registry.adapters.code import CodeAdapter
from registry.adapters.huggingface import HuggingFaceAdapter
from registry.adapters.api import APIAdapter
from utils.logger import get_logger

log = get_logger("registry")

_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "modules.json")
_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "schema", "module_schema.json")

_ADAPTER_MAP = {
    "code": CodeAdapter,
    "huggingface": HuggingFaceAdapter,
    "api": APIAdapter,
}

with open(_SCHEMA_PATH, encoding="utf-8") as f:
    MANIFEST_SCHEMA = json.load(f)


class Registry:

    def __init__(self, path: str = _REGISTRY_PATH):
        self._path = path
        self._manifests: dict[str, dict] = {}
        self._adapters: dict[str, BaseAdapter] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path, encoding="utf-8") as f:
                entries = json.load(f)
            for m in entries:
                self._manifests[m["module_id"]] = m
            log.info("loaded %d modules from registry", len(self._manifests))

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(list(self._manifests.values()), f, indent=2, ensure_ascii=False)

    def validate(self, manifest: dict) -> None:
        jsonschema.validate(instance=manifest, schema=MANIFEST_SCHEMA)

    def register(self, manifest: dict) -> str:
        self.validate(manifest)
        mid = manifest["module_id"]
        self._manifests[mid] = manifest
        self._save()
        log.info("registered module: %s (%s)", mid, manifest["provider_type"])
        return mid

    def remove(self, module_id: str) -> bool:
        if module_id in self._adapters:
            self._adapters[module_id].unload()
            del self._adapters[module_id]
        if module_id in self._manifests:
            del self._manifests[module_id]
            self._save()
            log.info("removed module: %s", module_id)
            return True
        return False

    def list_modules(self) -> list[dict]:
        return list(self._manifests.values())

    def get_manifest(self, module_id: str) -> dict | None:
        return self._manifests.get(module_id)

    def load(self, module_id: str) -> BaseAdapter:
        if module_id in self._adapters:
            return self._adapters[module_id]

        manifest = self._manifests.get(module_id)
        if manifest is None:
            raise KeyError(f"Module '{module_id}' not found in registry")

        ptype = manifest["provider_type"]
        adapter_cls = _ADAPTER_MAP.get(ptype)
        if adapter_cls is None:
            raise ValueError(f"Unknown provider_type '{ptype}' for module '{module_id}'")

        adapter = adapter_cls(manifest)
        adapter.load()
        self._adapters[module_id] = adapter
        return adapter

    def load_all(self) -> list[BaseAdapter]:
        adapters = []
        for mid in self._manifests:
            try:
                adapters.append(self.load(mid))
            except Exception as e:
                log.error("failed to load module '%s': %s", mid, e)
        return adapters

    def unload_all(self) -> None:
        for adapter in self._adapters.values():
            adapter.unload()
        self._adapters.clear()
