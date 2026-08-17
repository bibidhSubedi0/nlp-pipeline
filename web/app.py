"""
Flask application for the NLP Pipeline web UI.

Pages:
  /              - analyze text through the pipeline
  /modules       - manage registered extension modules (+ upload new ones)
  /config        - choose which modules run in the pipeline and in what order

Run with: python run_web.py
"""

import importlib
import json
import os
import re
from datetime import datetime, timezone

from flask import Flask, flash, redirect, render_template, request, session, url_for

from orchestrator.config import is_native_step, pipeline_config, step_label
from registry.registry import Registry
from web.pipeline_runner import (
    analyze,
    available_steps,
    ensure_builtins,
    highlight_entities,
)

MAX_HISTORY = 8

MODULE_DESCRIPTIONS = {
    "modules.normalizer": "Unicode + punctuation normalization of raw Devanagari text",
    "modules.spellcheck": "Dictionary + Levenshtein spell checking (annotation only)",
    "modules.ner": "Gazetteer-based named entity recognition (annotation only)",
}

SAMPLE_SENTENCES = [
    "This is an amazing and wonderful day!",
    "The results were terrible and disappointing.",
    "It is raining today.",
    "I love this beautiful city",
    "यो धेरै राम्रो कुरा हो",
    "त्यो बहुत खराब थियो",
    "राम काठमाडौं जान्छ",
]

_MODULE_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


def _module_short(module_path: str) -> str:
    return module_path.split(".")[-1]


def _remove_uploaded_file(module_id: str, entry_point: str) -> None:
    """
    Uploaded modules are stored as modules/<id>.py with entry_point
    'modules.<id>'. Core modules never use that pattern, so if the manifest
    matches, clean up the file too — otherwise the removed module would
    reappear in the pipeline editor as a native module.
    """
    if entry_point != f"modules.{module_id}":
        return
    target = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "modules", f"{module_id}.py")
    try:
        os.remove(target)
    except OSError:
        pass


def _summarize(result: dict) -> dict:
    annotations = result["metadata"].get("annotations", {})
    sentiment = annotations.get("sentiment", {}) or {}
    ner = annotations.get("ner", {}) or {}
    spellcheck = annotations.get("spellcheck", {}) or {}
    return {
        "text": result.get("original_input", ""),
        "pipeline_id": result.get("pipeline_id", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cleaned": result.get("current_text", "") != result.get("original_input", ""),
        "sentiment_label": sentiment.get("label"),
        "sentiment_score": sentiment.get("score"),
        "entity_count": len(ner.get("entities", [])),
        "unknown_words": len(spellcheck.get("unknown_words", [])),
        "error_count": len(result.get("errors", [])),
    }


def _config_rows(registry: Registry) -> list[dict]:
    """
    Build the rows for the pipeline editor. Enabled steps come first, in
    pipeline order; disabled steps follow alphabetically.
    """
    by_id = {m["module_id"]: m for m in registry.list_modules()}
    enabled = pipeline_config.get_active_steps()

    rows = []
    for step in available_steps(registry):
        if is_native_step(step):
            label = step_label(step)
            kind = "core"
            desc = MODULE_DESCRIPTIONS.get(step, "Native module")
            tag = "native"
        else:
            manifest = by_id.get(step, {})
            label = manifest.get("name") or step
            kind = f"extension · {manifest.get('provider_type', '?')}"
            desc = manifest.get("description") or "Registered extension module"
            tag = "extension"
        rows.append({
            "id": step,
            "label": label,
            "kind": kind,
            "desc": desc,
            "tag": tag,
            "enabled": step in enabled,
            "index": enabled.index(step) if step in enabled else None,
        })

    rows.sort(key=lambda r: (r["enabled"] is False, r["index"] if r["index"] is not None else 10**9))
    return rows


def _upload_module(registry: Registry, module_file, form: dict) -> tuple[str, str]:
    """
    Save an uploaded .py file into modules/, register it as a 'code' module,
    and add it to the pipeline. Returns (status, message).
    """
    filename = (module_file.filename or "").strip()
    if not filename.endswith(".py"):
        return "error", "Upload a single .py file containing a process(envelope) function."

    module_id = (form.get("module_id") or "").strip() or os.path.splitext(os.path.basename(filename))[0]
    module_id = module_id.lower().replace(" ", "-")
    if not _MODULE_ID_RE.match(module_id):
        return "error", (
            f"Invalid module_id '{module_id}'. Use lowercase letters, digits, "
            "'-' or '_', starting with a letter (e.g. 'spam-detector')."
        )
    if registry.get_manifest(module_id) is not None:
        return "error", f"A module with id '{module_id}' is already registered."

    target = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "modules", f"{module_id}.py")
    if os.path.exists(target):
        return "error", (
            f"modules/{module_id}.py already exists. Pick a different module_id "
            "or remove the file first."
        )

    source = module_file.read().decode("utf-8", errors="replace")
    try:
        compile(source, f"{module_id}.py", "exec")
    except SyntaxError as e:
        return "error", f"Syntax error in uploaded file: {e}"

    with open(target, "w", encoding="utf-8") as f:
        f.write(source)

    try:
        mod = importlib.import_module(f"modules.{module_id}")
        if not callable(getattr(mod, "process", None)):
            raise ValueError("module does not expose a process(envelope) function")
    except Exception as e:
        os.remove(target)
        return "error", f"Uploaded module failed to load: {e}"

    manifest = {
        "module_id": module_id,
        "name": (form.get("name") or "").strip() or module_id,
        "version": "1.0.0",
        "provider_type": "code",
        "description": (form.get("description") or "").strip() or "Uploaded module",
        "language": ["ne"],
        "behavior": "annotate",
        "annotations_key": module_id,
        "config": {"entry_point": f"modules.{module_id}"},
    }
    try:
        registry.register(manifest)
    except Exception as e:
        os.remove(target)
        return "error", f"Registration failed: {e}"

    pipeline_config.enable(module_id)
    return "success", f"Uploaded and enabled in pipeline: {module_id}"


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "nlp-pipeline-dev-key")

    registry = Registry()
    ensure_builtins(registry)

    @app.context_processor
    def inject_globals():
        return {
            "active_steps": pipeline_config.get_active_steps(),
            "step_label": step_label,
            "module_short": _module_short,
            "module_descriptions": MODULE_DESCRIPTIONS,
        }

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            samples=SAMPLE_SENTENCES,
            history=session.get("runs", []),
        )

    @app.route("/analyze", methods=["POST"])
    def analyze_route():
        text = request.form.get("text", "").strip()
        lang = request.form.get("language", "ne")

        if not text:
            flash("Please enter some text to analyze.", "error")
            return redirect(url_for("index"))

        try:
            result = analyze(text, language=lang, registry=registry)
        except Exception as e:
            flash(f"Pipeline failed: {e}", "error")
            return redirect(url_for("index"))

        annotations = result["metadata"].get("annotations", {})
        ner = annotations.get("ner", {}) or {}
        entities = ner.get("entities", [])

        runs = session.get("runs", [])
        runs.insert(0, _summarize(result))
        session["runs"] = runs[:MAX_HISTORY]

        return render_template(
            "index.html",
            result=result,
            samples=SAMPLE_SENTENCES,
            history=session.get("runs", []),
            text=text,
            lang=lang,
            segments=highlight_entities(result.get("current_text", ""), entities),
            sentiment=annotations.get("sentiment", {}) or {},
            spellcheck=annotations.get("spellcheck", {}) or {},
        )

    @app.route("/modules")
    def modules():
        modules_list = registry.list_modules()
        enabled = set(pipeline_config.get_active_steps())
        return render_template("modules.html", modules=modules_list, enabled_steps=enabled)

    @app.route("/modules/register", methods=["POST"])
    def register_module():
        manifest = None

        file = request.files.get("manifest_file")
        if file and file.filename:
            try:
                manifest = json.load(file)
            except Exception as e:
                flash(f"Could not parse uploaded file as JSON: {e}", "error")
                return redirect(url_for("modules"))

        pasted = request.form.get("manifest_json", "").strip()
        if manifest is None and pasted:
            try:
                manifest = json.loads(pasted)
            except Exception as e:
                flash(f"Could not parse pasted JSON: {e}", "error")
                return redirect(url_for("modules"))

        if manifest is None:
            flash("Provide a manifest file or paste manifest JSON.", "error")
            return redirect(url_for("modules"))

        try:
            mid = registry.register(manifest)
            flash(f"Registered module: {mid} ({manifest.get('provider_type')})", "success")
        except Exception as e:
            flash(f"Registration failed: {e}", "error")
        return redirect(url_for("modules"))

    @app.route("/modules/upload", methods=["POST"])
    def upload_module():
        file = request.files.get("module_file")
        if file is None or not (file.filename or "").strip():
            flash("Choose a .py file to upload.", "error")
            return redirect(url_for("modules"))
        status, message = _upload_module(registry, file, request.form)
        flash(message, status)
        return redirect(url_for("modules"))

    @app.route("/modules/remove", methods=["POST"])
    def remove_module():
        module_id = request.form.get("module_id", "")
        entry_point = (registry.get_manifest(module_id) or {}).get("config", {}).get("entry_point", "")
        if registry.remove(module_id):
            pipeline_config.disable(module_id)
            _remove_uploaded_file(module_id, entry_point)
            flash(f"Removed module: {module_id}", "success")
        else:
            flash(f"Module '{module_id}' not found.", "error")
        return redirect(url_for("modules"))

    @app.route("/modules/test", methods=["POST"])
    def test_module():
        module_id = request.form.get("module_id", "")
        try:
            adapter = registry.load(module_id)
            flash(f"{module_id}: load OK ({type(adapter).__name__})", "success")
        except Exception as e:
            flash(f"{module_id}: load FAILED — {e}", "error")
        return redirect(url_for("modules"))

    @app.route("/config")
    def config():
        rows = _config_rows(registry)
        enabled_count = sum(1 for r in rows if r["enabled"])
        return render_template(
            "config.html",
            rows=rows,
            enabled_count=enabled_count,
            config_path=pipeline_config.path,
        )

    @app.route("/config/enable", methods=["POST"])
    def config_enable():
        step = request.form.get("step_id", "")
        if pipeline_config.enable(step):
            flash(f"Added to pipeline: {step}", "success")
        else:
            flash(f"{step} is already in the pipeline.", "info")
        return redirect(url_for("config"))

    @app.route("/config/disable", methods=["POST"])
    def config_disable():
        step = request.form.get("step_id", "")
        if pipeline_config.disable(step):
            flash(f"Removed from pipeline: {step}", "success")
        else:
            flash(f"{step} is not in the pipeline.", "info")
        return redirect(url_for("config"))

    @app.route("/config/move", methods=["POST"])
    def config_move():
        step = request.form.get("step_id", "")
        direction = request.form.get("direction", "")
        if pipeline_config.move(step, direction):
            flash(f"Moved {step} {direction}.", "success")
        else:
            flash(f"Could not move {step} {direction}.", "error")
        return redirect(url_for("config"))

    return app
