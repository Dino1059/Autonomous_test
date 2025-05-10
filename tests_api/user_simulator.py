import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
# API endpoint
API_BASE_URL = "http://localhost:8081"

def test_user_simulator():
    """Test the user simulator functionality with image understanding ability."""
    
    # Sample task that focuses on testing chat interactions
    payload = {
        "tasks": [
            {
                "name": "User Simulator Chat Test",
                "prompt": """
                1. Call `get_system_message` to get the system message and image_url
                3. Call the user simulator to generate a response
                4. Paste the response into the url and return the response
                """,
                "max_steps": 40,
                "output_model_fields": None,
                "exclude_actions": ["search_google", "go_back", "input_text", "save_pdf", "switch_tab", "close_tab", "extract_content", "send_keys", "get_dropdown_options", "select_dropdown_options", "drag_drop", "get_drag_elements", "get_element_coordinates", "execute_drag_operation", "click_element", "click_element_by_text", "scroll", "click_the_send_button"],
                "llm_provider": "google",
                "llm_model": "gemini-2.0-flash",
                "llm_temperature": 0.0,
                "enable_memory": False,
                "memory_interval": 10,
                "initial_actions": [
                    {"open_tab": {"url": "https://kittyclysm.com/"}}
                ]
            }
        ],
        "laminar_api_key": os.getenv("LAMINAR_API_KEY", ""),
        "laminar_base_url": os.getenv("LAMINAR_BASE_URL", ""),
        "laminar_http_port": int(os.getenv("LAMINAR_HTTP_PORT", "0") or 0),
        "laminar_grpc_port": int(os.getenv("LAMINAR_GRPC_PORT", "0") or 0),
        "session_id": "test_user_simulator",
        "simulator_provider": "google",
        "simulator_model": "gemini-2.0-flash",
        "simulator_temperature": 0.7,  # Higher temperature for more creative responses
        "simulator_task": "The system have give you image, please describe each image in short and concise.",
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
                
                # Check for simulator interactions
                simulator_interactions = data.get("simulator_interactions", [])
                if simulator_interactions:
                    print("\nUser Simulator Interactions:")
                    print(json.dumps(simulator_interactions, indent=2))
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
    print("===== Testing Basic User Simulator =====")
    test_user_simulator()
    
    # print("\n===== Testing User Simulator with Image Processing =====")
    # test_user_simulator_with_images() 