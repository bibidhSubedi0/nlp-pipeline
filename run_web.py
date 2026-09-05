#!/usr/bin/env python3
"""
Entry point for the NLP Pipeline web UI.

Usage:
    python run_web.py
Then open http://127.0.0.1:5000 in your browser.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from web.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  NLP Pipeline UI -> http://0.0.0.0:{port}\n")
    app.run(debug=False, host="0.0.0.0", port=port)