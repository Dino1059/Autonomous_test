import requests
import json
import os
import time
import yaml
from dotenv import load_dotenv
from pathlib import Path
import string
load_dotenv()

def poll_results(task_id):
    """Poll the API for task results and return the data"""
    
    print("Polling for task results...")
    max_attempts = 100
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
                # print("Results:")
                # print(json.dumps(data.get("results"), indent=2))
                
                # Check for simulator interactions
                # simulator_interactions = data.get("simulator_interactions", [])
                # if simulator_interactions:
                #     print("\nUser Simulator Interactions:")
                #     print(json.dumps(simulator_interactions, indent=2))
                return data
            elif status == "failed":
                print("Task failed!")
                print("Error:")
                print(data.get("error"))
                return data
            elif status == "cancelled":
                print("Task was cancelled")
                return data
        
        # Wait before polling again
        time.sleep(5)
    
    print("Max polling attempts reached. Task may still be running.")
    return None

def get_template_placeholders(template):

    placeholders = template.get('placeholders', {})
    
    # Return placeholder info in order
    placeholder_list = []
    for placeholder_name, placeholder_config in placeholders.items():
        placeholder_list.append({
            'name': placeholder_name,
            'config': placeholder_config
        })
    
    return placeholder_list

with open("tests_api/custom_action_template.yaml", 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)
    print("Name:", data.get("metadata").get("name"))
placeholders = get_template_placeholders(data)

query = "Sơn Tùng MTP"
placeholder_dict = {}
for i, placeholder_info in enumerate(placeholders):
    print(i, placeholder_info)
    placeholder_name = placeholder_info['name']
    placeholder_dict[placeholder_name] = query


def substitute_template_variables(obj, substitutions):
    """Recursively substitute ${variable} patterns in the template"""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            result[key] = substitute_template_variables(value, substitutions)
        return result
    elif isinstance(obj, list):
        return [substitute_template_variables(item, substitutions) for item in obj]
    elif isinstance(obj, str):
        # Use string.Template for safe substitution
        template = string.Template(obj)
        try:
            return template.substitute(substitutions)
        except KeyError as e:
            # If placeholder is missing, keep the original
            print(f"Warning: Missing placeholder {e} in template")
            return obj
    else:
        return obj
    

def create_payload_from_template(template, placeholder_values, case_id):
    """Create task payload using YAML template and placeholder values, with external code file support"""
    
    # Get root report folder from environment
    root_report = os.getenv("ROOT_REPORT", "E:/official_DopikAI/ai-agent-tester/reports")
    report_folder_path = f"{root_report}/{case_id}"
    
    # Prepare substitutions with user values and system-generated values
    substitutions = dict(placeholder_values)
    substitutions.update({
        'session_id': f"test-session-id-{case_id}",
        'report_folder': report_folder_path
    })
    
    # Convert YAML template to the expected API format
    payload = {
        'tasks': template.get('tasks', []),
        'custom_actions': [],
        'simulator_task': template.get('simulator_task', ''),
        'browser_config': template.get('config', {}).get('browser_config', {})
    }
    
    # Add config values
    config = template.get('config', {})
    payload.update({
        'laminar_api_key': os.getenv("LAMINAR_API_KEY", config.get('laminar_api_key', "")),
        'laminar_base_url': os.getenv("LAMINAR_BASE_URL", config.get('laminar_base_url', "")),
        'laminar_http_port': int(os.getenv("LAMINAR_HTTP_PORT", config.get('laminar_http_port', 0)) or 0),
        'laminar_grpc_port': int(os.getenv("LAMINAR_GRPC_PORT", config.get('laminar_grpc_port', 0)) or 0),
        'simulator_provider': config.get('simulator_provider', 'google'),
        'simulator_model': config.get('simulator_model', 'gemini-2.0-flash'),
        'simulator_temperature': config.get('simulator_temperature', 0.0),
        'session_id': substitutions['session_id']
    })
    
    # Apply substitutions using string Template (safer than format)
    payload = substitute_template_variables(payload, substitutions)

    # Process custom actions - handle both inline code and external files
    custom_actions = []
    for action in template.get("custom_actions", []):
        if 'file' in action and 'function' in action:
            # External file reference
            try:
                file_path = Path(__file__).parent / action['file']
                with open(file_path, 'r', encoding='utf-8') as f:
                    code_content = f.read()
                
                custom_action = {
                    'name': action['name'],
                    'description': action.get('description', ''),
                    'code': code_content
                }
                custom_actions.append(custom_action)
                
            except FileNotFoundError:
                print(f"Warning: Custom action file not found: {action['file']}")
                # Fallback to empty action
                custom_actions.append({
                    'name': action['name'],
                    'description': action.get('description', ''),
                    'code': f"# File not found: {action['file']}\npass"
                })
                
        elif 'code' in action:
            # Inline code (backward compatibility)
            custom_actions.append(action)
        else:
            print(f"Warning: Invalid custom action format: {action.get('name', 'unnamed')}")
    
    payload['custom_actions'] = custom_actions
    
    return payload


payload = create_payload_from_template(data, placeholder_dict, "new_api")

import json
print(json.dumps(payload, indent=4, sort_keys=True))

API_BASE_URL = "http://localhost:8081"
response = requests.post(f"{API_BASE_URL}/tasks/run", json=payload)
# Print response
print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")
if response.status_code == 200:
    # Extract task ID
    task_id = response.json()['data']["message"].split(": ")[1]
    print(f"Task ID: {task_id}")
    
    poll_results(task_id)
else:
    print(f"Failed to start task: {response.text}")