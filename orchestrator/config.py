# Order matters — modules run in this sequence.
# Add or remove module names to add/remove pipeline stages.
ACTIVE_MODULES = [
    "spellcheck",
    "normalizer",
    "ner",
    "sentiment",
]
