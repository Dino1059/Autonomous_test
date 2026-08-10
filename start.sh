#!/bin/bash

# Auto-detect and activate python virtual environment
if [ -d "agent_tester" ]; then
    echo "Activating virtual environment 'agent_tester'..."
    source agent_tester/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment '.venv'..."
    source .venv/bin/activate
fi

# Start FastAPI app in the background
echo "Starting FastAPI Backend Server on port 8081..."
python app/main.py --port 8081 --host 0.0.0.0 &
BACKEND_PID=$!

# Start Gradio web UI in the foreground
echo "Starting Gradio Web UI on port 7860..."
python gradio_ui/webui.py

# Cleanup on exit
kill $BACKEND_PID 2>/dev/null