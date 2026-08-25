@echo off
cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Installing dependencies...
venv\Scripts\pip install --quiet --upgrade pip
venv\Scripts\pip install --quiet -r requirements.txt

echo.
echo   Starting NLP Pipeline on http://localhost:5000
echo   Press Ctrl+C to stop.
echo.
venv\Scripts\python run_web.py
