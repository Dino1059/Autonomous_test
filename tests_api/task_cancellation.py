import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
# API endpoint
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8081")

def test_task_cancellation():
    """Test the ability to cancel a running task"""
    
    # Sample task with a high max_steps to ensure it runs long enough to be cancelled
    payload = {
        "tasks": [
            {
                "name": "Long-Running Task",
                "prompt": "Visit the website and perform a series of complex interactions such as scrolling through multiple pages, clicking on various elements, and extracting data from different sections",
                "max_steps": 50,  # High number of steps
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
        "session_id": "test_task_cancellation",
        "simulator_provider": "google",
        "simulator_model": "gemini-2.0-flash",
        "simulator_temperature": 0.0,
        "simulator_task": "",
        "custom_actions": []
    }

    # List all tasks before starting
    print("Checking existing tasks before test...")
    list_all_tasks()

    # Make API request to start the task
    try:
        response = requests.post(f"{API_BASE_URL}/tasks/run", json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error starting task: {e}")
        return
    
    # Print response
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Extract task ID
    try:
        task_id = response.json()['data']["message"].split(": ")[1]
        print(f"Task ID: {task_id}")
    except (KeyError, IndexError) as e:
        print(f"Could not extract task ID from response: {e}")
        return
    
    # Wait a bit to make sure task has started
    print("Waiting for task to start running...")
    time.sleep(5)
    
    # Check task status
    try:
        status_response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
        status_response.raise_for_status()
        status_data = status_response.json()
        print(f"Task status before cancellation: {status_data.get('status')}")
        print(f"Task details: {json.dumps(status_data, indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"Error checking task status: {e}")
    
    # Cancel the task
    print("\nCancelling task...")
    try:
        cancel_response = requests.post(f"{API_BASE_URL}/tasks/{task_id}/cancel")
        cancel_response.raise_for_status()
        print(f"Cancellation status code: {cancel_response.status_code}")
        print(f"Cancellation response: {cancel_response.json()}")
    except requests.exceptions.HTTPError as e:
        # Handle specific HTTP errors from the improved API
        if e.response.status_code == 400:
            error_data = e.response.json()
            print(f"Could not cancel task: {error_data.get('detail', 'Unknown error')}")
        elif e.response.status_code == 404:
            print(f"Task {task_id} not found")
        else:
            print(f"HTTP error during cancellation: {e}")
        return
    except requests.exceptions.RequestException as e:
        print(f"Error during cancellation request: {e}")
        return
    
    # Poll for final status
    poll_for_cancellation(task_id)
    
    # List all tasks after test
    print("\nChecking tasks after test...")
    list_all_tasks()

def poll_for_cancellation(task_id):
    """Poll the API to monitor the cancellation status"""
    
    print("\nPolling for task cancellation status...")
    max_attempts = 20  # Increased for longer tasks
    attempts = 0
    poll_interval = 3  # seconds
    
    while attempts < max_attempts:
        attempts += 1
        try:
            response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
            response.raise_for_status()
            
            data = response.json()['data']
            status = data.get("status")
            message = data.get("message", "")
            
            print(f"Attempt {attempts}/{max_attempts} - Task status: {status}")
            
            if message:
                print(f"Message: {message}")
            
            if status == "cancelled":
                print("✅ SUCCESS: Task was successfully cancelled")
                return True
            elif status == "cancelling":
                print("Task is still in the process of being cancelled...")
            elif status == "completed":
                print("❌ FAIL: Task completed before it could be cancelled")
                return False
            elif status == "failed":
                error = data.get("error", "Unknown error")
                print(f"❌ FAIL: Task failed with error: {error}")
                return False
            elif status == "running":
                print("Task is still running despite cancellation request...")
            else:
                print(f"Unknown status: {status}")
        except requests.exceptions.RequestException as e:
            print(f"Error checking task status: {e}")
        
        # Wait before polling again
        print(f"Waiting {poll_interval} seconds before next check...")
        time.sleep(poll_interval)
    
    print("❌ FAIL: Max polling attempts reached. Task may still be running or stuck in cancellation.")
    return False

def list_all_tasks():
    """List all tasks using the new API endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/tasks")
        response.raise_for_status()
        
        tasks_data = response.json()['data']
        task_count = tasks_data.get("count", 0)
        tasks = tasks_data.get("tasks", {})
        
        print(f"Found {task_count} tasks:")
        for task_id, task_info in tasks.items():
            status = task_info.get("status", "unknown")
            message = task_info.get("message", "")
            print(f"- {task_id}: {status} {message}")
    except requests.exceptions.RequestException as e:
        print(f"Error listing tasks: {e}")

if __name__ == "__main__":
    print("===== Testing Task Cancellation =====")
    test_task_cancellation() 