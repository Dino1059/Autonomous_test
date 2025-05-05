import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
# API endpoint
API_BASE_URL = "http://localhost:8081"

def test_user_simulator():
    """Test the user simulator functionality for realistic user interactions"""
    
    # Sample task that focuses on testing chat interactions
    payload = {
        "tasks": [
            {
                "name": "User Simulator Chat Test",
                "prompt": """
                Visit the website which is a chat application. 
                1. Wait for the initial message from the system
                2. Extract the system message
                3. Call the user simulator to generate a response
                4. Paste the response into the chat input
                5. Click the send button
                6. Repeat steps 2-5 at least 3 times to simulate a conversation
                """,
                "max_steps": 40,
                "use_output_model": False,
                "output_model_fields": None,
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
        "session_id": "test_user_simulator",
        "simulator_provider": "google",
        "simulator_model": "gemini-2.0-flash",
        "simulator_temperature": 0.7,  # Higher temperature for more creative responses
        "simulator_task": "You are testing a customer service chatbot. Be conversational but brief. Ask about product features, pricing, and support options.",
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
    else:
        print(f"Failed to start task: {response.text}")

def test_user_simulator_with_images():
    """Test the user simulator with image processing capability"""
    
    # Custom prompt that instructs the agent to handle images
    image_handling_prompt = """
    Visit the website which is a chat application that may send images. 
    1. Wait for the initial message from the system
    2. Extract the system message and any image URLs
    3. Call the user simulator to generate a response that acknowledges the images
    4. Paste the response into the chat input
    5. Click the send button
    6. Repeat steps 2-5 at least 3 times to simulate a conversation
    """
    
    # Sample task configuration
    payload = {
        "tasks": [
            {
                "name": "User Simulator Image Test",
                "prompt": image_handling_prompt,
                "max_steps": 40,
                "use_output_model": False,
                "output_model_fields": None,
                "exclude_actions": [],
                "llm_provider": "openai",  # Using OpenAI for better multimodal capabilities
                "llm_model": "gpt-4",
                "llm_temperature": 0.0
            }
        ],
        "target_url": os.getenv("TARGET_URL"), 
        "laminar_api_key": os.getenv("LAMINAR_API_KEY", ""),
        "laminar_base_url": os.getenv("LAMINAR_BASE_URL", ""),
        "laminar_http_port": int(os.getenv("LAMINAR_HTTP_PORT", "0") or 0),
        "laminar_grpc_port": int(os.getenv("LAMINAR_GRPC_PORT", "0") or 0),
        "session_id": "test_user_simulator_images",
        "simulator_provider": "openai",  # Using OpenAI for better multimodal capabilities
        "simulator_model": "gpt-4",
        "simulator_temperature": 0.7,
        "simulator_task": "You are testing a visual product recommendation chatbot. Respond to the images shown by commenting on the visible products and asking questions about them.",
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
        
        # Poll for results with additional focus on simulator interactions
        poll_simulator_results(task_id)
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
            data = response.json()
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

def poll_simulator_results(task_id):
    """Poll the API for task results with focus on simulator interactions"""
    
    print("Polling for user simulator results...")
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
                
                # Check for simulator interactions
                simulator_interactions = data.get("simulator_interactions", [])
                if simulator_interactions:
                    print("\nUser Simulator Interactions:")
                    for idx, interaction in enumerate(simulator_interactions):
                        print(f"\n--- Interaction {idx+1} ---")
                        print(f"System: {interaction.get('system_message')}")
                        if interaction.get('image_url'):
                            print(f"Images: {', '.join(interaction.get('image_url'))}")
                        print(f"User: {interaction.get('user_response')}")
                        print(f"Feedback: {interaction.get('feedback')}")
                else:
                    print("No simulator interactions recorded")
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
    
    print("\n===== Testing User Simulator with Image Processing =====")
    test_user_simulator_with_images() 