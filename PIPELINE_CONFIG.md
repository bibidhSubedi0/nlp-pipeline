# Pipeline Configuration: Choosing, Ordering & Uploading Modules

This document explains the logic behind **which modules run in the pipeline**,
**how you turn them on/off**, and **how you add brand-new modules** (either by
uploading code or registering a manifest).

Everything described here is implemented — the quickest way to see it working
is the **Config** page of the web UI (`python run_web.py`).

---

## 1. The big idea: one pipeline, two kinds of modules

Every module that can run in the pipeline belongs to one of two kinds, but
they all live in **one ordered list**.

| Kind | What it is | Identifier | Example |
|---|---|---|---|
| **Native module** | A Python file in `modules/` exposing `process(envelope) -> envelope` | Dotted import path | `modules.normalizer` |
| **Registry module** | A module registered via a JSON manifest (code, HuggingFace, or API provider) | Registry `module_id` | `sentiment-code` |

The pipeline is just an ordered list mixing both:

```json
{
  "steps": [
    "modules.normalizer",
    "modules.spellcheck",
    "modules.ner",
    "sentiment-code"
  ]
}
```

This list is the **single source of truth**. It is persisted to
`orchestrator/pipeline_config.json` and is auto-created on the first change
(it is git-ignored, so it never pollutes the repo).

## 2. How "in the pipeline" vs "not in the pipeline" works

There is no per-module boolean flag. **A module is enabled if and only if its
identifier appears in the `steps` list.** Position in the list = position in
the pipeline.

| Operation | What happens |
|---|---|
| **Enable** | The id is appended to the end of `steps` and the file is saved |
| **Disable** | The id is removed from `steps` and the file is saved |
| **Reorder** | The id is swapped one position up/down and the file is saved |

The orchestrator (`run_pipeline`) reads this list for every run, so a change
takes effect on the **next analysis** — no restarts, no code edits.

### Defaults (before anything is saved)

If `pipeline_config.json` does not exist, the pipeline defaults to the three
core modules:

```python
DEFAULT_CORE_MODULES = [
    "modules.normalizer",
    "modules.spellcheck",
    "modules.ner",
]
```

**First-run bootstrap:** the web UI and CLI auto-register the built-in
`sentiment-code` module and enable it *only* when the config file has never
been saved — so the demo behaves exactly as before. The moment you save any
configuration, your saved list wins and nothing is auto-enabled.

## 3. How a module gets resolved and executed

`orchestrator/orchestrator.py` resolves each step id at run time:

```python
if "." in step:            # dotted -> native module
    module = importlib.import_module(step)
else:                      # bare id -> registry extension
    module = Registry().load(step)   # adapter for code/huggingface/api
```

Both kinds expose the same `process(envelope) -> envelope` contract, so the
orchestrator treats them identically: it runs each step in order, rejects
non-dict returns, reverts any mutation of `original_input`, validates the
envelope shape after every step, and **fails soft** (a broken module is
logged into `envelope["errors"]` and the pipeline keeps going).

## 4. Where the controls live

### Web UI (`python run_web.py`)

- **Config page** (`/config`) — the pipeline editor:
  - Active pipeline shown in order with **↑ Up / ↓ Down / Disable** buttons
  - Every available-but-disabled module listed with an **Enable** button
- **Modules page** (`/modules`) — every registered module shows an
  **in pipeline / not in pipeline** badge plus Enable/Disable, Test, Remove.

### CLI

```bash
python cli.py config                          # show pipeline + status
python cli.py enable <module_id>              # add to pipeline
python cli.py disable <module_id>             # remove from pipeline
python cli.py move <module_id> up|down        # reorder
python cli.py run "text"                      # runs only enabled steps
```

The `<module_id>` is either a dotted native path (`modules.ner`) or a
registry id (`sentiment-code`).

## 5. Adding a brand-new module

There are three ways, all ending with the module appearing on the **Modules**
page (and then on the **Config** page as something you can enable).

### A. Upload a Python file (web or CLI) — the fastest path

A `.py` file that exposes `process(envelope) -> envelope` is all you need.

**Web:** Modules → *Upload a new module* → pick the file (optionally give a
`module_id`, display name, description) → **Upload & add to pipeline**.

**CLI:**

```bash
python cli.py upload path/to/my_module.py --module-id my-module --name "My Module"
```

What happens server-side (this is the whole logic):

1. **Sanitize the id** — must match `^[a-z][a-z0-9_-]*$`; defaults to the
   file name if not given.
2. **Collision checks** — the id must not already be registered, and
   `modules/<id>.py` must not already exist.
3. **Syntax check** — the source is `compile()`d before anything is written.
4. **Save** — the file is written to `modules/<id>.py`.
5. **Import check** — the file is imported and must expose a callable
   `process`; on failure the file is deleted and the upload is rejected.
6. **Auto-manifest** — a `provider_type: "code"` manifest is generated
   (`entry_point: "modules.<id>"`) and registered in `registry/modules.json`.
7. **Auto-enable** — the id is appended to the pipeline `steps`, so the new
   module is immediately part of the pipeline. You can disable/reorder it
   from the Config page.

### B. Register a manifest (web or CLI)

For modules that are already importable code, a HuggingFace model, or a
remote API:

- **Web:** Modules → *Register a module by manifest* → upload/paste JSON.
- **CLI:** `python cli.py register manifest.json`

The manifest must match `schema/module_schema.json` (e.g.
`manifests/sentiment_huggingface.json`). Registered modules appear in the
pipeline editor but are **not** auto-enabled — you decide on the Config page
(unless you use the upload path, which auto-enables by design).

### C. Classic native module

Drop `your_module.py` into `modules/` exposing `process(envelope)` and it
automatically appears in the Config page's available list (native modules
are discovered by scanning `modules/*.py`). Enable it from the Config page —
no need to edit `ACTIVE_MODULES` in code anymore.

## 6. File reference

| Path | Purpose |
|---|---|
| `orchestrator/config.py` | `PipelineConfig` class; `ACTIVE_MODULES` live list; `DEFAULT_CORE_MODULES`; `enable/disable/move/set_steps` |
| `orchestrator/pipeline_config.json` | Persisted `{"steps": [...]}` (auto-created, git-ignored) |
| `orchestrator/orchestrator.py` | `run_pipeline(envelope, steps=None, registry=None)` — resolves native + registry steps |
| `registry/registry.py` + `registry/modules.json` | Extension module manifests and adapter lifecycle |
| `registry/adapter.py`, `registry/adapters/*` | Adapters that turn manifests into `process()` objects |
| `web/pipeline_runner.py` | `ensure_builtins()` bootstrap, native module discovery, `analyze()` |
| `web/app.py` | Config/Modules routes, `.py` upload endpoint |
| `modules/` | Native module files (core + uploaded) |

## 7. Design decisions worth knowing

- **One list, not two** — the old split (hardcoded core stages + "run every
  registered extension") made it impossible to choose. A single ordered
  `steps` list makes "which modules run" and "in what order" one simple
  question. `ACTIVE_MODULES` still exists as the live in-memory list the
  orchestrator reads, so the existing integration tests that pin it keep
  working.
- **Runtime, not code-editing** — the old way to disable a module was to
  comment out a line in `config.py`. Now a POST from the UI or a CLI command
  persists the choice, and every subsequent run honours it.
- **Fail soft everywhere** — a missing or broken module is recorded in
  `envelope["errors"]` with *"module 'X' not found or broken: …"* and the
  rest of the pipeline continues.
- **Uploads are code modules** — an uploaded `.py` becomes a `provider_type:
  "code"` registry entry pointing at itself, so it gets schema validation,
  testing, removal, and pipeline membership for free.
- **Tests are deterministic** — config file is git-ignored and tests that
  assert an exact module order pin `ACTIVE_MODULES` to
  `DEFAULT_CORE_MODULES` first, so a locally-saved pipeline can't break them.

## 8. Example walkthrough

```
1. python run_web.py
2. Modules -> Upload a new module -> my_length.py  -> Upload & add to pipeline
   (file saved to modules/my_length.py, manifest registered, enabled)
3. Config -> my_length is at the end of the pipeline
4. Config -> ↑ Up twice, Disable modules.spellcheck
5. Analyze a sentence -> history shows normalizer -> ner -> sentiment-code -> my_length
6. python cli.py config          # same state, now persisted to pipeline_config.json
```
