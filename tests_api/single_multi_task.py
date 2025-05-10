import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
# API endpoint
API_BASE_URL = "http://localhost:8081"

def test_basic_task_execution():
    """Test the basic functionality of running a simple task"""
    
    # Sample task configuration
    payload = {
        "tasks": [
            {
                "name": "Basic Navigation Test",
                "prompt": "Visit the website and verify the page has loaded correctly",
                "max_steps": 20,
                "output_model_fields": None,
                "exclude_actions": [],
                "llm_provider": "google",
                "llm_model": "gemini-2.0-flash",
                "llm_temperature": 0.0,
                "enable_memory": False,
                "memory_interval": 10,
                "initial_actions": [
                    {"open_tab": {"url": os.getenv("TARGET_URL")}}
                ]
            }
        ],
        "laminar_api_key": os.getenv("LAMINAR_API_KEY", ""),
        "laminar_base_url": os.getenv("LAMINAR_BASE_URL", ""),
        "laminar_http_port": int(os.getenv("LAMINAR_HTTP_PORT", "0") or 0),
        "laminar_grpc_port": int(os.getenv("LAMINAR_GRPC_PORT", "0") or 0),
        "session_id": "test_basic_task_execution",
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
        task_id = response.json()['data']["message"].split(": ")[1]
        print(f"Task ID: {task_id}")
        
        # Poll for results
        poll_results(task_id)
    else:
        print(f"Failed to start task: {response.text}")

def test_multiple_tasks():
    """Test running multiple sequential tasks in the same browser context"""
    # Define custom output model fields for task 1
    output_model_task1 = {
        "type": "object",
        "properties": {
            "pageTitle": {
                "type": "string",
                "description": "The title of the loaded webpage"
            },
            "pageUrl": {
                "type": "string",
                "description": "The URL of the loaded webpage"
            },
            "loadStatus": {
                "type": "string",
                "enum": ["success", "partial", "failed"],
                "description": "Status of the page load"
            }
        },
        "required": ["pageTitle", "pageUrl", "loadStatus"]
    }
    
    # Define custom output model fields for task 2
    output_model_task2 = {
        "type": "object",
        "properties": {
            "interactionType": {
                "type": "string",
                "enum": ["button", "link", "form", "other"],
                "description": "Type of element interacted with"
            },
            "elementText": {
                "type": "string",
                "description": "Text content of the interacted element"
            },
            "resultingPage": {
                "type": "string",
                "description": "URL or title of the page after interaction"
            },
            "success": {
                "type": "boolean",
                "description": "Whether the interaction was successful"
            }
        },
        "required": ["interactionType", "success"]
    }
    
    # Sample tasks configuration
    payload = {
        "tasks": [
            {
                "name": "Navigate to Website",
                "prompt": "Visit the website and verify the page has loaded correctly",
                "max_steps": 15,
                "output_model_fields": output_model_task1,
                "exclude_actions": [],
                "llm_provider": "google",
                "llm_model": "gemini-2.0-flash",
                "llm_temperature": 0.0,
                "enable_memory": False,
                "memory_interval": 10,
                "initial_actions": [
                    {"open_tab": {"url": os.getenv("TARGET_URL")}}
                ]
            },
            {
                "name": "Interact with Page",
                "prompt": "Find and click on a button or link on the page",
                "max_steps": 15,
                "output_model_fields": output_model_task2,
                "exclude_actions": [],
                "llm_provider": "google",
                "llm_model": "gemini-2.0-flash",
                "llm_temperature": 0.0,
                "enable_memory": False,
                "memory_interval": 10
            }
        ],
        "laminar_api_key": os.getenv("LAMINAR_API_KEY", ""),
        "laminar_base_url": os.getenv("LAMINAR_BASE_URL", ""),
        "laminar_http_port": int(os.getenv("LAMINAR_HTTP_PORT", "0") or 0),
        "laminar_grpc_port": int(os.getenv("LAMINAR_GRPC_PORT", "0") or 0),
        "session_id": "test_multiple_tasks",
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
        task_id = response.json()['data']["message"].split(": ")[1]
        print(f"Task ID: {task_id}")
        
        # Poll for results
        poll_results(task_id)
    else:
        print(f"Failed to start task: {response.text}")
    
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
        time.sleep(5)
    
    print("Max polling attempts reached. Task may still be running.")

if __name__ == "__main__":
    print("===== Testing Single Task Execution =====")
    test_basic_task_execution()
    
    print("\n===== Testing Multiple Sequential Tasks =====")
    test_multiple_tasks() 