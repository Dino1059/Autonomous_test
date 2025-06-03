import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
# API endpoint
API_BASE_URL = "http://localhost:8081"

def test_custom_params():
    """Test sending arbitrary parameters to the Agent via TaskConfig"""
    
    # Sample task with custom parameters
    payload = {
        "tasks": [
            {
                "name": "Test Custom Parameters",
                "prompt": "Go to example.com and extract the heading text and subheading",
                "max_steps": 20,
                
                # Standard TaskConfig parameters
                "llm_provider": "google",
                "llm_model": "gemini-2.0-flash",
                "llm_temperature": 0.0,
                "enable_memory": True,
                "memory_interval": 5,
                "initial_actions": [
                    {"open_tab": {"url": "https://example.com"}}
                ],
                
                # Example 1: Using a different LLM for planning (optional)
                # Note: Now planner_llm is completely optional - if not specified,
                # no default will be added to the Agent parameters
                "planner_llm": {
                    "provider": "google",           
                    "model": "gemini-1.5-pro",      
                    "temperature": 0.1              
                },
                
                # Example 2: Configuring Agent behavior with custom parameters 
                "use_vision_for_planner": True,     # Enable vision for planner
                "planner_interval": 4,              # Run planner every 4 steps
                
                # Example 3: Adding arbitrary parameters (if supported by Agent)
                "max_retries": 3,                   # Custom retry parameter if supported
                "timeout": 60                       # Custom timeout parameter if supported
            },
            # Second task without explicit planner_llm to demonstrate optional behavior
            {
                "name": "Test Without Planner LLM",
                "prompt": "Go to example.com and extract the meta description",
                "max_steps": 15,
                "llm_provider": "google",
                "llm_model": "gemini-2.0-flash",
                "llm_temperature": 0.0,
                "enable_memory": True,
                "initial_actions": [
                    {"open_tab": {"url": "https://example.com"}}
                ],
                # No planner_llm specified - will not be passed to Agent
                "use_vision_for_planner": True,
                "planner_interval": 3
            }
        ],
        "laminar_api_key": os.getenv("LAMINAR_API_KEY", ""),
        "laminar_base_url": os.getenv("LAMINAR_BASE_URL", ""),
        "laminar_http_port": int(os.getenv("LAMINAR_HTTP_PORT", "0") or 0),
        "laminar_grpc_port": int(os.getenv("LAMINAR_GRPC_PORT", "0") or 0),
        "session_id": "test_custom_params",
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
                print("Traceback:")
                print(data.get("traceback"))
                return
            elif status == "cancelled":
                print("Task was cancelled")
                return
        
        # Wait before polling again
        import time
        time.sleep(5)
    
    print("Max polling attempts reached. Task may still be running.")

if __name__ == "__main__":
    test_custom_params() 