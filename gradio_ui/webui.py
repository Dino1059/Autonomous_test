"""
AI Agent Test Runner - Dynamic Gradio Interface (YAML Version)

This application provides a dynamic web interface for running automated browser tests
using configurable templates from marketplace_v2.yaml.

Key improvements:
- Uses YAML format with explicit placeholder definitions
- No more placeholder detection confusion
- Cleaner separation of user inputs vs system placeholders vs code variables
- Better UI generation based on explicit field types
"""

import requests
import json
import os
import time
import gradio as gr
from dotenv import load_dotenv
from pathlib import Path
import yaml
import string

load_dotenv()

# CONFIG
API_BASE_URL = "http://localhost:8081"


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

def load_templates(template_path="templates_agent"):
    """Load templates from YAML files in the templates_agent directory"""
    try:
        templates_dir = Path(__file__).parent / template_path
        templates = {}
        
        # Load all YAML files in the templates directory
        for yaml_file in templates_dir.glob("*.yaml"):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
                template_name = yaml_file.stem
                templates[template_name] = template_data
        
        return templates
    except Exception as e:
        print(f"Error loading YAML templates: {e}")
        return {}

def get_available_templates():
    """Get list of available template names"""
    templates = load_templates()
    return list(templates.keys())

def get_template_placeholders(template_name):
    """Get placeholders for a specific template"""
    templates = load_templates()
    if template_name not in templates:
        return []
    
    template = templates[template_name]
    placeholders = template.get('placeholders', {})
    
    # Return placeholder info in order
    placeholder_list = []
    for placeholder_name, placeholder_config in placeholders.items():
        placeholder_list.append({
            'name': placeholder_name,
            'config': placeholder_config
        })
    
    return placeholder_list

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
    
def create_payload_from_template(template_name, placeholder_values, case_id):
    """Create task payload using YAML template and placeholder values, with external code file support"""
    
    # Load templates and get the specific template
    templates = load_templates()
    if template_name not in templates:
        raise ValueError(f"Template '{template_name}' not found")
    
    template = templates[template_name]
    
    # Get root report folder from environment
    root_report = os.getenv("ROOT_REPORT", "E:/official_DopikAI/ai-agent-tester/gradio_ui/reports")
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

    # Fix empty report_folder values with the case-specific path
    def fix_empty_report_folders(obj, report_path):
        """Recursively replace empty report_folder values with the case-specific path"""
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if key == 'report_folder' and (value == "" or value is None):
                    result[key] = report_path
                else:
                    result[key] = fix_empty_report_folders(value, report_path)
            return result
        elif isinstance(obj, list):
            return [fix_empty_report_folders(item, report_path) for item in obj]
        else:
            return obj
    
    payload = fix_empty_report_folders(payload, report_folder_path)

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



def preview_template_and_get_placeholders(template_name):
    """Preview the selected template and return placeholders info"""
    if not template_name:
        return "No template selected", []
    
    templates = load_templates()
    if template_name not in templates:
        return f"Template '{template_name}' not found", []
    
    template = templates[template_name]
    metadata = template.get('metadata', {})
    
    # Create a preview with key information
    template_display_name = metadata.get('name', template_name.replace('_', ' ').title())
    preview = f"**Template: {template_display_name}**\n\n"

    ## Model used in the template
    model_used = []
    
    # Extract models from config
    config = template.get('config', {})
    if config.get('simulator_model'):
        model_used.append(f"Simulator: {config.get('simulator_provider', 'N/A')} / {config['simulator_model']}")
    
    # Extract models from tasks
    tasks = template.get('tasks', [])
    for i, task in enumerate(tasks):
        task_name = task.get('name', f'Task {i+1}')
        if task.get('llm_model'):
            model_used.append(f"{task_name}: {task.get('llm_provider', 'N/A')} / {task['llm_model']}")
        
        # Check planner LLM
        planner_llm = task.get('planner_llm', {})
        if planner_llm.get('model'):
            model_used.append(f"{task_name} Planner: {planner_llm.get('provider', 'N/A')} / {planner_llm['model']}")
        
        # Check report config
        report_config = task.get('report_config', {})
        if report_config.get('model'):
            model_used.append(f"{task_name} Report: {report_config.get('provider', 'N/A')} / {report_config['model']}")
    
    if model_used:
        preview += f"**Models Used:**\n"
        for model in model_used:
            preview += f"  - {model}\n"
        preview += "\n"
    else:
        preview += f"**Models Used:** None specified\n\n"
    
    # Add description from metadata
    description = metadata.get('description', 'No description available')
    preview += f"**Description:** {description}\n\n"
    
    # Add tags from metadata
    tags = metadata.get('tags', [])
    if tags:
        preview += f"**Tags:** {', '.join(tags)}\n\n"
    
    # User placeholders info
    placeholders = template.get('placeholders', {})
    if placeholders:
        preview += f"**User Parameters ({len(placeholders)}):**\n"
        for param_name, param_info in placeholders.items():
            param_type = param_info.get('type', 'string')
            param_desc = param_info.get('description', 'No description')
            required = "Required" if param_info.get('required', False) else "Optional"
            emoji = param_info.get('emoji', '📄')
            preview += f"  \n{emoji} **{param_name}** ({param_type}, {required}): {param_desc}\n"
    
    # System placeholders
    system_placeholders = template.get('system_placeholders', [])
    if system_placeholders:
        preview += f"\n**System Parameters:** {', '.join(system_placeholders)} (auto-generated)\n"
    
    # Tasks info (reuse the tasks variable from model extraction)
    preview += f"\n**Tasks ({len(tasks)}):**\n"
    for i, task in enumerate(tasks):
        preview += f"  {i+1}. {task.get('name', 'Unnamed Task')}\n"
        preview += f"     - Max Steps: {task.get('max_steps', 'N/A')}\n"
        preview += f"     - LLM: {task.get('llm_provider', 'N/A')} / {task.get('llm_model', 'N/A')}\n"
    
    # Config info (reuse the config variable from model extraction)
    preview += f"\n**Configuration:**\n"
    preview += f"  - Simulator: {config.get('simulator_provider', 'N/A')} / {config.get('simulator_model', 'N/A')}\n"
    preview += f"  - Temperature: {config.get('simulator_temperature', 'N/A')}\n"
    preview += f"  - Own Browser: {config.get('use_own_browser', False)}\n"
    
    # Custom actions
    custom_actions = template.get('custom_actions', [])
    preview += f"\n**Custom Actions ({len(custom_actions)}):**\n"
    for action in custom_actions:
        preview += f"  - {action.get('name', 'Unnamed Action')}\n"
    
    # Return placeholders for UI generation
    placeholder_list = get_template_placeholders(template_name)
    
    return preview, placeholder_list

def update_input_visibility(template_name):
    """Update input field visibility based on selected template"""
    if not template_name:
        # Hide all inputs if no template selected
        return [gr.update(visible=False)] * 10
    
    _, placeholder_list = preview_template_and_get_placeholders(template_name)
    
    updates = []
    for i in range(10):  # We have 10 input fields
        if i < len(placeholder_list):
            placeholder_info = placeholder_list[i]
            placeholder_name = placeholder_info['name']
            config = placeholder_info['config']
            
            emoji = config.get('emoji', '📄')
            ui_type = config.get('ui_type', 'text')
            description = config.get('description', f'Value for {placeholder_name}')
            required = config.get('required', False)
            default_value = config.get('default', None)
            
            label = f"{emoji} {placeholder_name.replace('_', ' ').title()}"
            if required:
                label += " *"
            
            placeholder_text = f"Enter {placeholder_name.replace('_', ' ')}..."
            
            if ui_type == 'number':
                updates.append(gr.update(
                    visible=True,
                    label=label,
                    info=description,
                    value=default_value,
                    placeholder=placeholder_text
                ))
            elif ui_type == 'textarea':
                updates.append(gr.update(
                    visible=True,
                    label=label,
                    placeholder=placeholder_text,
                    info=description,
                    lines=3,
                    value=default_value
                ))
            else:  # text
                updates.append(gr.update(
                    visible=True,
                    label=label,
                    placeholder=placeholder_text,
                    info=description,
                    lines=1,
                    value=default_value
                ))
        else:
            updates.append(gr.update(visible=False))
    
    return updates

def read_markdown_report(case_id):
    """Read markdown report from the task folder"""
    try:
        root_report = os.getenv("ROOT_REPORT", "E:/official_DopikAI/ai-agent-tester/gradio_ui/reports")
        report_folder = Path(root_report) / case_id
        
        if not report_folder.exists():
            return None
        
        # Look for markdown files in the report folder
        markdown_files = list(report_folder.glob("*.md"))
        
        if not markdown_files:
            return None
        
        # Read the first markdown file found
        markdown_file = markdown_files[0]
        with open(markdown_file, 'r', encoding='utf-8') as f:
            return f.read()
            
    except Exception as e:
        print(f"Error reading markdown report: {e}")
        return None

def run_test_case(template_name, input1, input2, input3, input4, input5, input6, input7, input8, input9, input10):
    """Run a test case with the specified template and input values"""
    try:
        if not template_name:
            yield "❌ Please select a template first!\n"
            return
        
        # Get template placeholders
        _, placeholder_list = preview_template_and_get_placeholders(template_name)
        
        # Map inputs to placeholders
        inputs = [input1, input2, input3, input4, input5, input6, input7, input8, input9, input10]
        placeholder_dict = {}
        
        for i, placeholder_info in enumerate(placeholder_list):
            if i < len(inputs) and inputs[i] is not None and str(inputs[i]).strip():
                placeholder_name = placeholder_info['name']
                placeholder_dict[placeholder_name] = inputs[i]
        
        # Check required fields
        missing_required = []
        for placeholder_info in placeholder_list:
            placeholder_name = placeholder_info['name']
            config = placeholder_info['config']
            if config.get('required', False) and placeholder_name not in placeholder_dict:
                missing_required.append(placeholder_name)
        
        if missing_required:
            yield f"❌ Missing required fields: {', '.join(missing_required)}\n"
            return
        
        if not placeholder_dict:
            yield "❌ Please fill in at least one field!\n"
            return
        
        # Generate a simple case ID
        case_id = f"TEST_{hash(str(placeholder_dict)) % 10000:04d}"
        
        payload = create_payload_from_template(template_name, placeholder_dict, case_id)
        
        yield f"🚀 Starting test case\n"
        yield f"📋 Template: {template_name.replace('_', ' ').title()}\n"
        yield f"🆔 Case ID: {case_id}\n"
        
        # Display placeholder values
        for placeholder, value in placeholder_dict.items():
            yield f"📄 {placeholder}: {value}\n"
        yield "\n"
        
        response = requests.post(f"{API_BASE_URL}/tasks/run", json=payload)
        
        yield f"📡 API Response Status: {response.status_code}\n"
        
        if response.status_code == 200:
            # Extract task ID from API response
            response_data = response.json()
            task_id = response_data['data']["message"].split(": ")[1]
            yield f"🆔 Task ID: {task_id}\n\n"
            
            # Poll for results, but use case_id for reports
            yield "⏳ Polling for results...\n"
            result = poll_results_streaming(task_id, case_id)
            
            for update in result:
                yield update
                
        else:
            yield f"❌ Failed to start task: {response.text}\n"
            
    except Exception as e:
        yield f"💥 Error occurred: {str(e)}\n"

def poll_results_streaming(task_id, case_id):
    """Poll the API for task results with streaming updates"""
    max_attempts = 100
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
        
        if response.status_code == 200:
            data = response.json()['data']
            status = data.get("status")
            
            yield f"📊 Attempt {attempts}: Task status: {status}\n"
            
            if status == "completed":
                yield "🎉 Task completed successfully!\n\n"
                
                # Display results
                results = data.get("results", [])
                if results:
                    for i, result in enumerate(results):
                        yield f"📋 Task {i+1} Results:\n"
                        if result:
                            yield f"  Feature: {result.get('feature', 'N/A')}\n"
                            yield f"  Status: {result.get('feature_status', 'N/A')}\n"
                            yield f"  Details: {result.get('detail_reason', 'N/A')}\n\n"
                
                # Display simulator interactions
                simulator_interactions = data.get("simulator_interactions", [])
                if simulator_interactions:
                    yield "🤖 Simulator Interactions:\n"
                    for interaction in simulator_interactions[-3:]:  # Show last 3 interactions
                        yield f"  Response: {interaction.get('response', 'N/A')}\n"
                        yield f"  Feedback: {interaction.get('feedback', 'N/A')}\n"
                        yield f"  Grade: {interaction.get('grade', 'N/A')}\n\n"
                
                # Note about report using case_id
                root_report = os.getenv("ROOT_REPORT", "E:/official_DopikAI/ai-agent-tester/gradio_ui/reports")
                yield f"📄 Report will be available at: {root_report}/{case_id}/\n"
                
                return
                
            elif status == "failed":
                yield "❌ Task failed!\n"
                error = data.get("error", "Unknown error")
                yield f"Error: {error}\n"
                return
                
            elif status == "cancelled":
                yield "⚠️ Task was cancelled\n"
                return
        
        # Wait before polling again
        time.sleep(5)
    
    yield "⏰ Max polling attempts reached. Task may still be running.\n"

def create_gradio_interface():
    """Create the dynamic Gradio interface"""
    available_templates = get_available_templates()
    
    with gr.Blocks(title="AI Agent Tester (YAML)", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🤖 AI Agent Test Runner (YAML Version)")
        gr.Markdown("Run automated browser tests with YAML-based templates. **No more placeholder detection issues!** Input fields are explicitly defined in template metadata.")
        
        with gr.Row():
            with gr.Column(scale=1):
                # Template selection
                template_dropdown = gr.Dropdown(
                    label="📋 Select Template",
                    choices=available_templates,
                    value=available_templates[0] if available_templates else None,
                    interactive=True
                )
                
                # Template preview
                template_preview = gr.Markdown(
                    label="📖 Template Preview",
                    value="Select a template to see preview"
                )
                
                # Create 10 dynamic input fields (will be shown/hidden based on template)
                dynamic_inputs = []
                for i in range(10):
                    text_input = gr.Textbox(
                        label=f"Input {i+1}",
                        placeholder="Enter value...",
                        lines=1,
                        visible=False
                    )
                    dynamic_inputs.append(text_input)
                
                run_button = gr.Button("🚀 Run Test", variant="primary", size="lg")
                
            with gr.Column(scale=2):
                # Combined test results and report output
                output_display = gr.Textbox(
                    label="📊 Test Results & Report",
                    lines=30,
                    max_lines=30,
                    show_copy_button=True,
                    interactive=False
                )
        
        # Event handlers
        def update_preview_and_inputs(template_name):
            """Update both preview and input visibility"""
            preview, _ = preview_template_and_get_placeholders(template_name)
            input_updates = update_input_visibility(template_name)
            return [preview] + input_updates
        
        def run_test_with_report(template_name, *inputs):
            """Run test and display both results and markdown report in single output"""
            output_text = ""
            case_id = None
            
            # Stream test execution updates
            for update in run_test_case(template_name, *inputs):
                output_text += update
                
                # Extract case_id for report loading
                if 'Case ID:' in update and case_id is None:
                    lines = update.split('\n')
                    for line in lines:
                        if 'Case ID:' in line:
                            case_id = line.split('Case ID:')[1].strip()
                            break
                
                yield output_text
            
            # After test completion, append markdown report to the same output
            if case_id:
                try:
                    # Wait for report generation
                    time.sleep(2)
                    
                    markdown_report = read_markdown_report(case_id)
                    if markdown_report:
                        separator = "\n" + "="*80 + "\n"
                        report_section = f"{separator}📄 MARKDOWN REPORT FOR CASE: {case_id}\n{separator}\n{markdown_report}\n"
                        yield output_text + report_section
                    else:
                        root_report = os.getenv("ROOT_REPORT", "E:/official_DopikAI/ai-agent-tester/gradio_ui/reports")
                        no_report_msg = f"\n\n📄 No markdown report found for case `{case_id}`\nExpected location: `{root_report}/{case_id}/`\n"
                        yield output_text + no_report_msg
                        
                except Exception as e:
                    error_msg = f"\n\n📄 Error loading report: {str(e)}\n"
                    yield output_text + error_msg
            else:
                no_case_msg = "\n\n📄 Could not extract case ID to load report\n"
                yield output_text + no_case_msg
        
        # Handle template changes
        template_dropdown.change(
            fn=update_preview_and_inputs,
            inputs=[template_dropdown],
            outputs=[template_preview] + dynamic_inputs
        )
        
        # Handle test run
        run_button.click(
            fn=run_test_with_report,
            inputs=[template_dropdown] + dynamic_inputs,
            outputs=output_display,
            show_progress=True
        )
        
        # Load initial template preview and inputs
        demo.load(
            fn=update_preview_and_inputs,
            inputs=[template_dropdown],
            outputs=[template_preview] + dynamic_inputs
        )
        
    return demo

if __name__ == "__main__":
    # Create and launch the Gradio interface
    demo = create_gradio_interface()
    demo.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True
    ) 