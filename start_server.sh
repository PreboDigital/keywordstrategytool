#!/bin/bash
# Start Keyword Strategy Tool web server
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q streamlit pandas openai 2>/dev/null || pip install streamlit pandas openai

echo ""
echo "Starting server at http://localhost:8501"
echo "Press Ctrl+C to stop"
echo ""
streamlit run app.py --server.port 8501
