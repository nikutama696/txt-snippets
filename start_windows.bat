@echo off
REM txt-snippets launcher for Windows
REM Double-click this file to start txt-snippets

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv" (
    echo Setting up virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

REM Run the application
python main.py
