# NLP Pipeline

Modular Nepali NLP pipeline with plug-and-play modules.
Built for Software Engineering class project.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python cli.py
```

Type a Nepali sentence, press Enter. The pipeline runs every active module
in sequence and shows the result. Type `quit` to exit.

## Web UI

```bash
python run_web.py
```

Then open http://127.0.0.1:5000 in your browser.

- **Analyze** — run any Nepali/English text through the pipeline with
  sentiment, NER highlighting, spellcheck suggestions, stage-by-stage
  audit trail, and the full envelope JSON
- **Modules** — upload a new `.py` module (auto-added to the pipeline),
  register extension modules from a manifest file or pasted JSON, test
  them, and remove them
- **Config** — interactively choose which modules run in the pipeline and
  in what order (enable / disable / reorder); changes persist to
  `orchestrator/pipeline_config.json` and apply to the next analysis

See [PIPELINE_CONFIG.md](PIPELINE_CONFIG.md) for the full design: how
module selection works, how uploading new modules works, and how to do it
all from the CLI.

## Run Tests

```bash
pytest tests/ -v
# or without pytest:
python run_tests.py
```

## Project Structure

```
modules/          — one file per module, each exposes process(envelope) -> envelope
orchestrator/     — glue code: run_pipeline() and config
utils/            — shared envelope factory, schema validator, logger
tests/            — unit + integration tests
data/             — benchmark sentences
cli.py            — demo REPL
run_web.py        — web UI entry point (Flask)
web/              — Flask app: templates, static assets, pipeline runner
```

## Adding a Module

The pipeline is runtime-configurable now — you pick which modules run and in
what order, no code edits needed.

```bash
python cli.py enable my-module      # add a module to the pipeline
python cli.py disable modules.ner   # remove one
python cli.py move sentiment-code up
python cli.py upload my_module.py   # upload a new module, added automatically
```

Or use the web UI **Config** page. See [PIPELINE_CONFIG.md](PIPELINE_CONFIG.md)
for the full explanation of the logic.

## Team

- Bibidh Subedi
- Biprash Pandey
- Bhim Prasad Upadhaya
- Bibek Gautam

## Status

Complete

test
