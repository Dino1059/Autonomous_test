import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
# API endpoint
API_BASE_URL = "http://localhost:8081"

def test_custom_output_model():
    # Define custom output model fields
    output_model_fields = {
        "main_title": {
            "type": "str",
            "description": "Main title of the page"
        },
    }

    # Sample task with custom output model
    payload = {
        "tasks": [
            {
                "name": "Test Custom Output Model",
                "prompt": "Visit the website and extract the main title",
                "max_steps": 30,
                "use_output_model": True,
                "output_model_fields": output_model_fields,
                "exclude_actions": [],
                "llm_provider": "google",
                "llm_model": "gemini-2.0-flash",
                "llm_temperature": 0.0
            }
        ],
        "target_url": os.getenv("TARGET_URL"), 
        "laminar_api_key": os.getenv("LAMINAR_API_KEY", ""),
        "laminar_base_url": os.getenv("LAMINAR_BASE_URL", ""),
        "laminar_http_port": int(os.getenv("LAMINAR_HTTP_PORT", "0") or 0),
        "laminar_grpc_port": int(os.getenv("LAMINAR_GRPC_PORT", "0") or 0),
        "session_id": "test_custom_output_model",
        "simulator_provider": "google",
        "simulator_model": "gemini-2.0-flash",
        "simulator_temperature": 0.0,
        "simulator_task": "",
        "custom_actions": []
    }

    # Make API request
    response = requests.post(f"{API_BASE_URL}/tasks/run", json=payload)
    
    # Print response
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        # Extract task ID
        task_id = response.json()["message"].split(": ")[1]
        print(f"Task ID: {task_id}")
        
        # Poll for results
        poll_results(task_id)
    
def poll_results(task_id):
    """Poll the API for task results"""
    
    print("Polling for task results...")
    max_attempts = 30
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            
            print(f"Task status: {status}")
            
            if status == "completed":
                print("Task completed!")
                print("Results:")
                print(json.dumps(data.get("results"), indent=2))
                return
            elif status == "failed":
                print("Task failed!")
                print("Error:")
                print(data.get("error"))
                return
            elif status == "cancelled":
                print("Task was cancelled")
                return
        
        # Wait before polling again
        import time
        time.sleep(5)
    
    print("Max polling attempts reached. Task may still be running.")

if __name__ == "__main__":
    test_custom_output_model()