#!/bin/bash
# txt-snippets launcher for macOS
# Double-click this file to start txt-snippets
# Terminal window will close automatically after launch

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Run the application in background and close terminal
nohup python main.py &>/dev/null &

# Close this terminal window
osascript -e 'tell application "Terminal" to close front window' &>/dev/null &

exit 0
