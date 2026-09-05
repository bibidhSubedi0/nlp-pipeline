#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

VENV_DIR="venv"
PORT="${PORT:-5000}"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate and install dependencies
echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r requirements.txt

# Run the web server
echo ""
echo "  Starting NLP Pipeline on http://localhost:$PORT"
echo "  Press Ctrl+C to stop."
echo ""
"$VENV_DIR/bin/python3" run_web.py
