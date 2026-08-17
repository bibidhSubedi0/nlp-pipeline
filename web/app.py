"""
Flask application for the NLP Pipeline web UI.

Pages:
  /              - analyze text through the pipeline
  /modules       - manage registered extension modules
  /config        - show the active pipeline configuration

Run with: python run_web.py
"""

import json
import os
from datetime import datetime, timezone

from flask import Flask, flash, redirect, render_template, request, session, url_for

from orchestrator.config import ACTIVE_MODULES
from registry.registry import Registry
from web.pipeline_runner import analyze, ensure_builtins, highlight_entities

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


def _module_short(module_path: str) -> str:
    return module_path.split(".")[-1]


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


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "nlp-pipeline-dev-key")

    registry = Registry()
    ensure_builtins(registry)

    @app.context_processor
    def inject_globals():
        return {
            "active_modules": ACTIVE_MODULES,
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
        return render_template("modules.html", modules=modules_list)

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

    @app.route("/modules/remove", methods=["POST"])
    def remove_module():
        module_id = request.form.get("module_id", "")
        if registry.remove(module_id):
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
        modules_list = registry.list_modules()
        return render_template("config.html", modules=modules_list)

    return app