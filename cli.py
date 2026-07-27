#!/usr/bin/env python3
"""
NLP Pipeline CLI

Commands:
  python cli.py run <text>              Run the full pipeline on text
  python cli.py run --file <path>       Run the pipeline on a file
  python cli.py list                    List registered modules
  python cli.py register <manifest>     Register a module from a JSON manifest
  python cli.py remove <module_id>      Unregister a module
  python cli.py config                  Show current pipeline configuration
  python cli.py demo                    Run the sentiment analysis demo
  python cli.py interactive             Interactive REPL mode
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from utils.envelope_factory import new_envelope
from utils.validate_envelope import validate_envelope
from orchestrator.orchestrator import run_pipeline
from registry.registry import Registry
from utils.logger import get_logger

log = get_logger("cli")

LABELS = {
    "positive": "\033[92m+\033[0m",
    "negative": "\033[91m-\033[0m",
    "neutral":  "\033[93m~\033[0m",
}


def _format_sentiment(annotations: dict) -> str:
    s = annotations.get("sentiment", {})
    if not s:
        return ""
    label = s.get("label", "?")
    score = s.get("score", 0.0)
    icon = LABELS.get(label, "?")
    return f" {icon} {label} ({score:.2f})"


def _print_result(result: dict) -> None:
    print()
    print(f"  original : {result['original_input']}")
    if result["current_text"] != result["original_input"]:
        print(f"  cleaned  : {result['current_text']}")

    annotations = result["metadata"].get("annotations", {})

    for step in result["history"]:
        status_char = {"success": "ok", "failed": "!!", "skipped": "--"}.get(step["status"], "??")
        suffix = ""
        if step["module"] in ("sentiment", "sentiment_analyzer", "sentiment-code",
                               "sentiment-hf", "sentiment-api", "modules.sentiment_analyzer"):
            suffix = _format_sentiment(annotations)
        print(f"  [{status_char}] {step['module']}{suffix}")

    if annotations.get("ner", {}).get("entities"):
        entities = annotations["ner"]["entities"]
        parts = [f"{e['text']} ({e['type']})" for e in entities]
        print(f"  [ner] entities: {', '.join(parts)}")

    if result["errors"]:
        for err in result["errors"]:
            print(f"  [err] {err.get('module', '?')}: {err.get('error', '?')}")
    print()


def _ensure_builtins(registry):
    """Auto-register the built-in sentiment module if nothing is registered."""
    if not registry.list_modules():
        manifest_path = os.path.join(os.path.dirname(__file__), "manifests", "sentiment_code.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
            try:
                registry.register(manifest)
            except Exception:
                pass


def cmd_run(args, registry):
    _ensure_builtins(registry)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read().strip()
    else:
        text = " ".join(args.text) if args.text else ""

    if not text:
        print("Error: provide text or --file", file=sys.stderr)
        sys.exit(1)

    envelope = new_envelope(text, language=args.lang)

    # Run the core pipeline (normalizer -> spellcheck -> ner)
    result = run_pipeline(envelope)

    # Run any registered modules (e.g. sentiment)
    for manifest in registry.list_modules():
        try:
            adapter = registry.load(manifest["module_id"])
            result = adapter.process(result)
        except Exception as e:
            print(f"  [err] {manifest['module_id']}: {e}", file=sys.stderr)

    _print_result(result)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_list(args, registry):
    modules = registry.list_modules()
    if not modules:
        print("No modules registered.")
        print("Register one with: python cli.py register <manifest.json>")
        return

    print(f"\n{'ID':<25} {'Type':<14} {'Version':<10} {'Name'}")
    print("-" * 80)
    for m in modules:
        print(f"{m['module_id']:<25} {m['provider_type']:<14} {m['version']:<10} {m['name']}")
    print()


def cmd_register(args, registry):
    path = args.manifest
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading manifest: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        mid = registry.register(manifest)
        print(f"Registered: {mid} ({manifest['provider_type']})")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_remove(args, registry):
    if registry.remove(args.module_id):
        print(f"Removed: {args.module_id}")
    else:
        print(f"Module '{args.module_id}' not found.", file=sys.stderr)
        sys.exit(1)


def cmd_config(args, registry):
    from orchestrator.config import ACTIVE_MODULES
    print("\nCore pipeline stages:")
    for i, mod in enumerate(ACTIVE_MODULES, 1):
        print(f"  {i}. {mod}")

    modules = registry.list_modules()
    if modules:
        print("\nRegistered extensions:")
        for m in modules:
            print(f"  - {m['module_id']} ({m['provider_type']}) v{m['version']}")
    else:
        print("\nNo registered extensions.")
    print()


def cmd_demo(args, registry):
    # Auto-register the built-in sentiment module if not already present
    manifest_path = os.path.join(os.path.dirname(__file__), "manifests", "sentiment_code.json")
    if registry.get_manifest("sentiment-code") is None:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        registry.register(manifest)
        print("Registered built-in sentiment analyzer.\n")

    from orchestrator.config import ACTIVE_MODULES
    stages = " -> ".join(m.split(".")[-1] for m in ACTIVE_MODULES) + " -> sentiment"
    print("=" * 60)
    print("  NLP Pipeline: Sentiment Analysis Demo")
    print(f"  Pipeline: {stages}")
    print("=" * 60)
    print("\nType a sentence in English or Nepali.")
    print("Type 'quit' to exit, 'pipeline' to show pipeline info.\n")

    demo_sentences = [
        "This is an amazing and wonderful day!",
        "The results were terrible and disappointing.",
        "It is raining today.",
        "I love this beautiful city",
        "यो धेरै राम्रो कुरा हो",
        "त्यो बहुत खराब थियो",
    ]
    print("  (or try these pre-loaded sentences:)\n")
    for i, s in enumerate(demo_sentences, 1):
        print(f"  {i}. {s}")
    print()

    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if text.lower() == "quit":
            break
        if text.lower() == "pipeline":
            cmd_config(args, registry)
            continue
        if text.isdigit() and 1 <= int(text) <= len(demo_sentences):
            text = demo_sentences[int(text) - 1]
            print(f"  ({text})")
        if not text:
            continue

        envelope = new_envelope(text)
        result = run_pipeline(envelope)

        adapter = registry.load("sentiment-code")
        result = adapter.process(result)

        _print_result(result)


def cmd_interactive(args, registry):
    print("=== NLP Pipeline Interactive Mode ===")
    print("Commands: 'list' modules, 'config' pipeline, 'quit' to exit\n")

    while True:
        try:
            text = input("nlp> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue
        if text.lower() == "quit":
            break
        if text.lower() == "list":
            cmd_list(args, registry)
            continue
        if text.lower() == "config":
            cmd_config(args, registry)
            continue

        envelope = new_envelope(text)
        result = run_pipeline(envelope)

        for manifest in registry.list_modules():
            try:
                adapter = registry.load(manifest["module_id"])
                result = adapter.process(result)
            except Exception as e:
                print(f"  [err] {manifest['module_id']}: {e}")

        _print_result(result)


def main():
    parser = argparse.ArgumentParser(
        prog="nlp-pipeline",
        description="Modular NLP Pipeline for Nepali and English text.",
    )
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="Run the pipeline on text")
    p_run.add_argument("text", nargs="*", help="Input text")
    p_run.add_argument("--file", "-f", help="Read input from file")
    p_run.add_argument("--lang", default="ne", help="Language code (default: ne)")
    p_run.add_argument("--json", "-j", action="store_true", help="Print full JSON output")

    sub.add_parser("list", help="List registered modules")

    p_reg = sub.add_parser("register", help="Register a module from a manifest JSON file")
    p_reg.add_argument("manifest", help="Path to manifest JSON file")

    p_rem = sub.add_parser("remove", help="Remove a registered module")
    p_rem.add_argument("module_id", help="Module ID to remove")

    sub.add_parser("config", help="Show current pipeline configuration")

    sub.add_parser("demo", help="Run the sentiment analysis demo")

    sub.add_parser("interactive", help="Interactive REPL mode")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    registry = Registry()

    commands = {
        "run": cmd_run,
        "list": cmd_list,
        "register": cmd_register,
        "remove": cmd_remove,
        "config": cmd_config,
        "demo": cmd_demo,
        "interactive": cmd_interactive,
    }

    fn = commands.get(args.command)
    if fn:
        fn(args, registry)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
