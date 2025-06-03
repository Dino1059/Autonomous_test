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
        "type": "object",
        "properties": {
          "list_features": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "title": {
                  "type": "string"
                },
                "description": {
                  "type": "string"
                },
                "status": {
                  "type": "string"
                },
                "reason": {
                  "type": "string"
                }
              }
            }
          }
        }
    }

    # Sample task with custom output model
    payload = {
        "tasks": [
            {
                "name": "Test Custom Output Model",
                "prompt": "List all the features of the product. Each feature should have a title and a description, status(working or not working) and reason. You also should go for each feature and test it. If it is not working, you should say it is not working and give a reason.",
                "max_steps": 30,
                "output_model_fields": output_model_fields,
                "exclude_actions": [],
                "llm_provider": "google",
                "llm_model": "gemini-2.0-flash",
                "llm_temperature": 0.0,
                "enable_memory": True,
                "memory_interval": 10,
                "initial_actions": [
                    {"open_tab": {"url": "https://developer-devnet.eragon.gg/dashboard"}}
                ],
                # Custom parameters that will be passed directly to Agent:
                "use_vision_for_planner": True,  # Example of custom param
                "planner_interval": 5,           # Example of custom param
                # Custom planner LLM configuration:
                "planner_llm": {
                    "provider": "google",        # Can be different from main LLM
                    "model": "gemini-2.0-flash",   # Different model for planner
                    "temperature": 0.2           # Different temperature for planner
                },
            }
        ],
        "laminar_api_key": os.getenv("LAMINAR_API_KEY", ""),
        "laminar_base_url": os.getenv("LAMINAR_BASE_URL", ""),
        "laminar_http_port": int(os.getenv("LAMINAR_HTTP_PORT", "0") or 0),
        "laminar_grpc_port": int(os.getenv("LAMINAR_GRPC_PORT", "0") or 0),
        "session_id": "test_custom_output_model",
        "simulator_provider": "google",
        "simulator_model": "gemini-2.0-flash",
        "simulator_temperature": 0.0,
        "simulator_task": "dsdsadsa",
        "custom_actions": [],
        "use_own_browser": True
    }

    # Make API request
    response = requests.post(f"{API_BASE_URL}/tasks/run", json=payload)
    
    # Print response
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        # Extract task ID
        task_id = response.json()['data']["message"].split(": ")[1]
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
            data = response.json()['data']
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