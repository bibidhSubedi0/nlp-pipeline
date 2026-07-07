"""
utils/benchmark_loader.py

Loads data/benchmark_sentences.json.
Fully independent of all pipeline modules.

Benchmark entry format (per project spec):
    {"id": int, "input": str, "note": str}
"""

import json
import os

BENCHMARK_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "benchmark_sentences.json"
)


def load_all() -> list:
    """Load and return all benchmark sentences."""
    path = os.path.abspath(BENCHMARK_PATH)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_inputs_only() -> list:
    """Return just the raw input strings. Useful for feeding into run_pipeline()."""
    return [s["input"] for s in load_all()]


def summary() -> dict:
    """Return count of sentences that are empty, whitespace, normal, etc."""
    sentences = load_all()
    result = {
        "total":          len(sentences),
        "empty_string":   sum(1 for s in sentences if s["input"] == ""),
        "whitespace_only": sum(1 for s in sentences if s["input"].strip() == "" and s["input"] != ""),
        "mixed_script":   sum(1 for s in sentences if any(c.isascii() and c.isalpha() for c in s["input"])),
        "has_emoji":      sum(1 for s in sentences if any(ord(c) > 127000 for c in s["input"])),
    }
    return result


if __name__ == "__main__":
    print("Benchmark dataset summary:")
    for key, val in summary().items():
        print(f"  {key:20s}: {val}")
