#!/bin/bash

# Start FastAPI app in the background
python app/main.py --port 8081 --host 0.0.0.0 &

# Start Gradio web UI in the foreground
python gradio_ui/webui.py 