#!/bin/bash
# Activate the virtual environment for this project

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/venv/bin/activate"
echo "✓ Virtual environment activated"
echo "  Python: $(which python3)"
echo "  Pip: $(which pip)"
echo ""
echo "You can now run:"
echo "  python3 chatgpt_example.py"
echo "  python3 test_search_trials.py"
echo ""

