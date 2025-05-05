import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
# API endpoint
API_BASE_URL = "http://localhost:8081"

def test_custom_action():
    """Test the ability to register and use custom actions"""
    
    # Define a custom action
    extract_all_links_action = {
        "name": "Extract all links from the page",
        "code": """async def extract_all_links(temp_params: str, browser: BrowserContext):
    # Get the current page
    page = await browser.get_current_page()
    
    # Extract all links from the page
    links = await page.evaluate('''() => {
        const links = Array.from(document.querySelectorAll('a'));
        return links.map(link => ({
            text: link.textContent.trim(),
            href: link.href,
            visible: link.offsetWidth > 0 && link.offsetHeight > 0
        }));
    }''')
    
    # Format the result
    formatted_links = []
    for idx, link in enumerate(links):
        formatted_links.append(f"{idx+1}. {link['text']} -> {link['href']} (Visible: {link['visible']})")
    
    result = "Extracted links:\\n" + "\\n".join(formatted_links)
    
    # Log the result
    logger = logging.getLogger("EXTRACT ALL LINKS")
    logger.info(f"Extracted {len(links)} links from the page")
    
    return ActionResult(
        extracted_content=result,
        include_in_memory=True
    )"""
    }
    
    count_elements_action = {
        "name": "Count elements by selector",
        "code": """async def count_elements(temp_params: str, browser: BrowserContext):
    # Get the current page
    page = await browser.get_current_page()
    
    # Get the parameters from the format: "selector=.some-class"
    selector = ".button"  # Default selector
    if temp_params and "=" in temp_params:
        key, value = temp_params.split("=", 1)
        if key.strip() == "selector":
            selector = value.strip()
    
    # Count elements with the selector
    count = await page.evaluate(f'''(selector) => {{
        return document.querySelectorAll(selector).length;
    }}''', selector)
    
    result = f"Found {count} elements matching selector: {selector}"
    
    # Log the result
    logger = logging.getLogger("COUNT ELEMENTS")
    logger.info(result)
    
    return ActionResult(
        extracted_content=result,
        include_in_memory=True
    )"""
    }
    
    # Sample task configuration
    payload = {
        "tasks": [
            {
                "name": "Custom Actions Test",
                "prompt": """
                Visit the website and perform the following:
                1. Extract all links from the page using the custom action
                2. Count all button elements on the page using the custom action with selector=button
                """,
                "max_steps": 20,
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
        "session_id": "test_custom_actions",
        "simulator_provider": "google",
        "simulator_model": "gemini-2.0-flash",
        "simulator_temperature": 0.0,
        "simulator_task": "",
        "custom_actions": [extract_all_links_action, count_elements_action]
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

def test_get_action_templates():
    """Test the endpoint that retrieves action templates"""
    
    # Request templates
    response = requests.get(f"{API_BASE_URL}/templates/actions")
    
    # Print response
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        templates = response.json()
        print("Available templates:")
        for template_name, template_code in templates.items():
            print(f"\n--- {template_name} Template ---")
            print(template_code[:100] + "..." if len(template_code) > 100 else template_code)
    else:
        print(f"Failed to get templates: {response.text}")

def test_available_actions():
    """Test the endpoint that lists available actions"""
    
    # Request available actions
    response = requests.get(f"{API_BASE_URL}/actions")
    
    # Print response
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        actions = response.json()
        print("Available actions:")
        for action in actions:
            print(f"- {action}")
    else:
        print(f"Failed to get available actions: {response.text}")

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
                
                # Extract more detailed history to see custom action usage
                if data.get("history"):
                    print("\nTask History (focusing on custom actions):")
                    for idx, history_item in enumerate(data.get("history")):
                        if "history" in history_item:
                            for step in history_item["history"]:
                                if (
                                    "action" in step and 
                                    (step["action"] == "Extract all links from the page" or 
                                     step["action"] == "Count elements by selector")
                                ):
                                    print(f"\nStep {step.get('step', 'unknown')}:")
                                    print(f"Action: {step.get('action')}")
                                    print(f"Result: {step.get('result', {}).get('extracted_content')}")
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
    print("===== Testing Custom Actions =====")
    test_custom_action()
    
    print("\n===== Testing Action Templates =====")
    test_get_action_templates()
    
    print("\n===== Testing Available Actions List =====")
    test_available_actions() 