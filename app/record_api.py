#!/usr/bin/env python3

#
# FastAPI API to record and save Browser-Use activity data.
# Save this code to api.py and run with `python api.py`
# 

import json
import base64
from pathlib import Path

from fastapi import FastAPI, Request, Query
import prettyprinter
import uvicorn

prettyprinter.install_extras(exclude=['ipython', 'django', 'attrs'])

# Utility function to save screenshots
def b64_to_png(b64_string: str, output_file):
    """
    Convert a Base64-encoded string to a PNG file.
    
    :param b64_string: A string containing Base64-encoded data
    :param output_file: The path to the output PNG file
    """
    with open(output_file, "wb") as f:
        f.write(base64.b64decode(b64_string))

# Initialize FastAPI app
app = FastAPI()


@app.post("/post_agent_history_step")
async def post_agent_history_step(request: Request):
    data = await request.json()
    
    # Extract task_id from the request query parameters or default to "default"
    task_id = request.query_params.get("task_id", "default")
    
    prettyprinter.cpprint(data)
    print(f"Recording step for task_id: {task_id}")

    # Ensure the main "recordings" folder exists
    recordings_folder = Path("recordings")
    recordings_folder.mkdir(exist_ok=True)
    
    # Create task-specific subfolder
    task_folder = recordings_folder / task_id
    task_folder.mkdir(exist_ok=True)
    
    # Create screenshot folder within task folder
    screenshot_folder = task_folder / "screenshots"
    screenshot_folder.mkdir(exist_ok=True)

    # Determine the next file number by examining existing .json files in this task folder
    existing_numbers = []
    for item in task_folder.iterdir():
        if item.is_file() and item.suffix == ".json":
            try:
                file_num = int(item.stem)
                existing_numbers.append(file_num)
            except ValueError:
                # In case the file name isn't just a number
                pass

    if existing_numbers:
        next_number = max(existing_numbers) + 1
    else:
        next_number = 1

    # Construct the file path
    file_path = task_folder / f"{next_number}.json"

    # Save the JSON data to the file
    with file_path.open("w") as f:
        json.dump(data, f, indent=2)

    # Save screenshot if available
    screenshot_path = None
    if "website_screenshot" in data and data["website_screenshot"]:
        screenshot_path = screenshot_folder / f"{next_number}.png"
        b64_to_png(data["website_screenshot"], screenshot_path)

    return {
        "status": "ok", 
        "message": f"Saved to {file_path}",
        "task_id": task_id,
        "file_number": next_number,
        "screenshot_saved": screenshot_path is not None
    }

if __name__ == "__main__":
    print("Starting Browser-Use recording API on http://0.0.0.0:9000")
    uvicorn.run(app, host="0.0.0.0", port=9000)