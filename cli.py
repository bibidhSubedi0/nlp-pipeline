#!/usr/bin/env python3
"""
NLP Pipeline CLI

Commands:
  python cli.py run <text>              Run the full pipeline on text
  python cli.py run --file <path>       Run the pipeline on a file
  python cli.py list                    List registered modules
  python cli.py register <manifest>     Register a module from a JSON manifest
  python cli.py upload <file.py>        Upload a Python module and add it to the pipeline
  python cli.py remove <module_id>      Unregister a module
  python cli.py config                  Show current pipeline configuration
  python cli.py enable <module_id>      Add a module to the pipeline
  python cli.py disable <module_id>     Remove a module from the pipeline
  python cli.py move <module_id> <up|down>  Reorder a module in the pipeline
  python cli.py demo                    Run the sentiment analysis demo
  python cli.py interactive             Interactive REPL mode
"""

import argparse
import importlib
import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from utils.envelope_factory import new_envelope
from utils.validate_envelope import validate_envelope
from orchestrator.orchestrator import run_pipeline
from orchestrator.config import is_native_step, pipeline_config, step_label
from registry.registry import Registry
from utils.logger import get_logger

log = get_logger("cli")

_MODULE_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")

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


def _bootstrap(registry):
    """First-run bootstrap: register built-ins and enable sentiment if the
    pipeline config has never been saved (mirrors the web UI behaviour)."""
    _ensure_builtins(registry)
    if not pipeline_config.file_exists:
        if registry.get_manifest("sentiment-code") is not None:
            pipeline_config.enable("sentiment-code")


def cmd_run(args, registry):
    _bootstrap(registry)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read().strip()
    else:
        text = " ".join(args.text) if args.text else ""

    if not text:
        print("Error: provide text or --file", file=sys.stderr)
        sys.exit(1)

    envelope = new_envelope(text, language=args.lang)

    # One ordered step list: native modules + enabled registry modules.
    result = run_pipeline(envelope, registry=registry)

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
    manifest = registry.get_manifest(args.module_id) or {}
    entry_point = manifest.get("config", {}).get("entry_point", "")
    if registry.remove(args.module_id):
        pipeline_config.disable(args.module_id)
        if entry_point == f"modules.{args.module_id}":
            target = os.path.join(os.path.dirname(__file__),
                                  "modules", f"{args.module_id}.py")
            try:
                os.remove(target)
            except OSError:
                pass
        print(f"Removed: {args.module_id}")
    else:
        print(f"Module '{args.module_id}' not found.", file=sys.stderr)
        sys.exit(1)


def cmd_upload(args, registry):
    _ensure_builtins(registry)
    path = args.file
    with open(path, encoding="utf-8") as f:
        source = f.read()

    module_id = args.module_id or os.path.splitext(os.path.basename(path))[0]
    module_id = module_id.lower().replace(" ", "-")
    if not _MODULE_ID_RE.match(module_id):
        print(f"Error: invalid module_id '{module_id}'. Use [a-z][a-z0-9_-]*",
              file=sys.stderr)
        sys.exit(1)
    if registry.get_manifest(module_id) is not None:
        print(f"Error: module '{module_id}' is already registered.", file=sys.stderr)
        sys.exit(1)

    target = os.path.join(os.path.dirname(__file__), "modules", f"{module_id}.py")
    if os.path.exists(target):
        print(f"Error: modules/{module_id}.py already exists.", file=sys.stderr)
        sys.exit(1)

    try:
        compile(source, f"{module_id}.py", "exec")
    except SyntaxError as e:
        print(f"Error: syntax error in uploaded file: {e}", file=sys.stderr)
        sys.exit(1)

    with open(target, "w", encoding="utf-8") as f:
        f.write(source)

    try:
        mod = importlib.import_module(f"modules.{module_id}")
        if not callable(getattr(mod, "process", None)):
            raise ValueError("module does not expose a process(envelope) function")
    except Exception as e:
        os.remove(target)
        print(f"Error: uploaded module failed to load: {e}", file=sys.stderr)
        sys.exit(1)

    manifest = {
        "module_id": module_id,
        "name": args.name or module_id,
        "version": "1.0.0",
        "provider_type": "code",
        "description": "Uploaded via CLI",
        "language": ["ne"],
        "behavior": "annotate",
        "annotations_key": module_id,
        "config": {"entry_point": f"modules.{module_id}"},
    }
    registry.register(manifest)
    pipeline_config.enable(module_id)
    print(f"Uploaded and enabled in pipeline: {module_id}")


def cmd_enable(args, registry):
    step = args.module_id
    if registry.get_manifest(step) is None and not is_native_step(step):
        print(f"Error: '{step}' is not a registered module or native module.",
              file=sys.stderr)
        sys.exit(1)
    if pipeline_config.enable(step):
        print(f"Added to pipeline: {step}")
    else:
        print(f"Already in pipeline: {step}")


def cmd_disable(args, registry):
    if pipeline_config.disable(args.module_id):
        print(f"Removed from pipeline: {args.module_id}")
    else:
        print(f"Not in pipeline: {args.module_id}")


def cmd_move(args, registry):
    if args.direction not in ("up", "down"):
        print("Error: direction must be 'up' or 'down'.", file=sys.stderr)
        sys.exit(1)
    if pipeline_config.move(args.module_id, args.direction):
        print(f"Moved {args.module_id} {args.direction}.")
    else:
        print(f"Could not move {args.module_id} {args.direction}.", file=sys.stderr)
        sys.exit(1)


def cmd_config(args, registry):
    print("\nActive pipeline (in order):")
    steps = pipeline_config.get_active_steps()
    if not steps:
        print("  (empty — no modules enabled)")
    for i, mod in enumerate(steps, 1):
        marker = "" if is_native_step(mod) else " [extension]"
        print(f"  {i}. {mod}{marker}")

    registered = {m["module_id"] for m in registry.list_modules()}
    print("\nRegistered modules:")
    if registered:
        for mid in sorted(registered):
            status = "enabled" if mid in steps else "disabled"
            print(f"  - {mid} ({status})")
    else:
        print("  (none)")

    print(f"\nConfig file: {pipeline_config.path}")
    if not pipeline_config.file_exists:
        print("  (not saved yet — defaults in use; any enable/disable/move creates it)")
    print()


def cmd_demo(args, registry):
    _bootstrap(registry)

    from orchestrator.config import pipeline_config
    stages = " -> ".join(step_label(s) for s in pipeline_config.get_active_steps())
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
        result = run_pipeline(envelope, registry=registry)

        _print_result(result)


def cmd_interactive(args, registry):
    _bootstrap(registry)
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
        result = run_pipeline(envelope, registry=registry)

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

    p_up = sub.add_parser("upload", help="Upload a Python module file and add it to the pipeline")
    p_up.add_argument("file", help="Path to the .py module file")
    p_up.add_argument("--module-id", dest="module_id", help="module_id (default: file name)")
    p_up.add_argument("--name", default=None, help="Display name (default: module_id)")

    sub.add_parser("config", help="Show current pipeline configuration")

    p_en = sub.add_parser("enable", help="Add a module to the pipeline")
    p_en.add_argument("module_id", help="Native dotted path or registry module ID")

    p_dis = sub.add_parser("disable", help="Remove a module from the pipeline")
    p_dis.add_argument("module_id", help="Native dotted path or registry module ID")

    p_mv = sub.add_parser("move", help="Reorder a module in the pipeline")
    p_mv.add_argument("module_id", help="Native dotted path or registry module ID")
    p_mv.add_argument("direction", choices=["up", "down"], help="Direction to move")

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
        "upload": cmd_upload,
        "remove": cmd_remove,
        "config": cmd_config,
        "enable": cmd_enable,
        "disable": cmd_disable,
        "move": cmd_move,
        "demo": cmd_demo,
        "interactive": cmd_interactive,
    }

    fn = commands.get(args.command)
    if fn:
        fn(args, registry)
    else:
        parser.print_help()


if __name__ == "__main__":
    # Windows consoles often default to cp1252, which cannot encode the
    # Devanagari text the pipeline outputs. Reconfigure to UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
