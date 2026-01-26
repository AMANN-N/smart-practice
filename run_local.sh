#!/bin/bash
export PYTHONPATH=$PYTHONPATH:.
# Ensure virtual environment is active (optional check)
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not detected. Usage might fail if dependencies aren't installed globally."
    echo "💡 Tip: source venv/bin/activate"
fi

# Set python path to current directory
export PYTHONPATH=$PYTHONPATH:.

# Check for API Key
if [[ -z "$GEMINI_API_KEY" ]]; then
    echo "❌ Error: GEMINI_API_KEY is not set."
    echo "👉 Run: export GEMINI_API_KEY='your_key' && ./run_local.sh"
    exit 1
fi

echo "🚀 Starting Smart Practice Tutor..."
# Use the venv python/streamlit explicitly
./venv/bin/pip install -r requirements.txt > /dev/null 2>&1
./venv/bin/streamlit run src/ui/app.py
