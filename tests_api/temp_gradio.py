"""
AI Agent Test Runner - Dynamic Gradio Interface

This application provides a dynamic web interface for running automated browser tests
using configurable templates from marketplace.json.

Required Environment Variables:
- LAMINAR_API_KEY: Your Laminar API key
- LAMINAR_BASE_URL: Your Laminar base URL  
- LAMINAR_HTTP_PORT: Laminar HTTP port (default: 0)
- LAMINAR_GRPC_PORT: Laminar gRPC port (default: 0)
- ROOT_REPORT: Root directory for test reports (default: E:/official_DopikAI/ai-agent-tester/reports)

The application will:
1. Dynamically detect placeholders from template JSON
2. Create appropriate UI fields based on metadata
3. Run tests with the selected template
4. Display results and markdown reports when available

ID Structure:
- case_id: Locally generated ID based on test parameters (e.g., TEST_1234)
- task_id: API-returned ID for the running task
- Reports are organized by case_id for consistency and predictability

Report Structure:
- Reports are stored in {ROOT_REPORT}/{case_id}/
- Markdown reports (.md files) are automatically displayed in the web UI
- Report folders use case_id (not task_id) for deterministic organization
"""

import requests
import json
import os
import time
import gradio as gr
from dotenv import load_dotenv
from pathlib import Path
import re

load_dotenv()

# CONFIG
API_BASE_URL = "http://localhost:8081"

def load_templates():
    """Load templates from marketplace.json using actual template keys"""
    try:
        marketplace_path = Path(__file__).parent / "marketplace.json"
        with open(marketplace_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        templates = {}
        for item in data:
            # Get the template key (e.g., 'game_campaign_template', 'ecommerce_template')
            for key, value in item.items():
                templates[key] = value
        
        return templates
    except Exception as e:
        print(f"Error loading templates: {e}")
        return {}

def extract_placeholders_from_template(template):
    """Extract all placeholders from a template recursively"""
    placeholders = set()
    
    def find_placeholders(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                find_placeholders(value)
        elif isinstance(obj, list):
            for item in obj:
                find_placeholders(item)
        elif isinstance(obj, str):
            # Find all {placeholder} patterns
            matches = re.findall(r'\{([^}]+)\}', obj)
            placeholders.update(matches)
    
    find_placeholders(template)
    
    # Remove common system placeholders that are auto-generated
    system_placeholders = {'session_id', 'report_folder'}
    return sorted(list(placeholders - system_placeholders))

def get_parameter_info_from_metadata(template, placeholder):
    """Get parameter information from template metadata"""
    metadata = template.get('metadata', {})
    parameters = metadata.get('parameters', {})
    
    if placeholder in parameters:
        param_info = parameters[placeholder]
        param_type = param_info.get('type', 'string')
        description = param_info.get('description', f'Value for {placeholder}')
        
        # Generate label from placeholder name
        label = f'📄 {placeholder.replace("_", " ").title()}'
        
        # Add emoji based on placeholder name or type
        emoji_map = {
            'title': '📝',
            'query': '🔍',
            'url': '🌐',
            'step_action': '🎯',
            'step_expected_result': '✅',
            'max_retry': '🔄',
            'product_name': '🛍️',
            'category': '📂',
            'price_range': '💰'
        }
        
        if placeholder in emoji_map:
            label = f'{emoji_map[placeholder]} {placeholder.replace("_", " ").title()}'
        
        return {
            'label': label,
            'description': description,
            'placeholder_text': f'Enter {placeholder.replace("_", " ")}...',
            'type': 'textarea' if 'action' in placeholder or 'result' in placeholder else ('number' if param_type == 'number' else 'text')
        }
    
    # Default info for unknown placeholders
    return {
        'label': f'📄 {placeholder.replace("_", " ").title()}',
        'description': f'Value for {placeholder}',
        'placeholder_text': f'Enter {placeholder.replace("_", " ")}...',
        'type': 'text'
    }

def substitute_template_placeholders(template, substitutions):
    """Recursively substitute placeholders in template"""
    if isinstance(template, dict):
        result = {}
        for key, value in template.items():
            result[key] = substitute_template_placeholders(value, substitutions)
        return result
    elif isinstance(template, list):
        return [substitute_template_placeholders(item, substitutions) for item in template]
    elif isinstance(template, str):
        result = template
        for placeholder, value in substitutions.items():
            result = result.replace(f"{{{placeholder}}}", str(value))
        return result
    else:
        return template

def create_payload_from_template(template_name, placeholder_values, case_id):
    """Create task payload using selected template and placeholder values"""
    templates = load_templates()
    
    if template_name not in templates:
        raise ValueError(f"Template '{template_name}' not found")
    
    template = templates[template_name].copy()
    
    # Get root report folder from environment
    root_report = os.getenv("ROOT_REPORT", "E:/official_DopikAI/ai-agent-tester/reports")
    report_folder_path = f"{root_report}/{case_id}"
    
    # Prepare substitutions with system-generated values
    substitutions = dict(placeholder_values)
    substitutions.update({
        'session_id': f"test-session-id-{case_id}",
        'report_folder': report_folder_path
    })
    
    # Add default URL if not provided
    # if 'url' not in substitutions:
    #     raise ValueError("URL is required for test execution")
    
    # Apply substitutions to the template
    payload = substitute_template_placeholders(template, substitutions)
    
    # Special handling for empty report_folder values in report_config
    def fix_empty_report_folders(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == 'report_folder' and (value == '' or value is None):
                    obj[key] = report_folder_path
                elif isinstance(value, (dict, list)):
                    fix_empty_report_folders(value)
        elif isinstance(obj, list):
            for item in obj:
                fix_empty_report_folders(item)
    
    # Fix any empty report_folder values
    fix_empty_report_folders(payload)
    
    # Add environment variables
    payload['laminar_api_key'] = os.getenv("LAMINAR_API_KEY", "")
    payload['laminar_base_url'] = os.getenv("LAMINAR_BASE_URL", "")
    payload['laminar_http_port'] = int(os.getenv("LAMINAR_HTTP_PORT", "0") or 0)
    payload['laminar_grpc_port'] = int(os.getenv("LAMINAR_GRPC_PORT", "0") or 0)
    
    return payload

def get_available_templates():
    """Get list of available template names"""
    templates = load_templates()
    return list(templates.keys())

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
    
    # Add description from metadata
    description = metadata.get('description', 'No description available')
    preview += f"**Description:** {description}\n\n"
    
    # Add tags from metadata
    tags = metadata.get('tags', [])
    if tags:
        preview += f"**Tags:** {', '.join(tags)}\n\n"
    
    # Tasks info
    tasks = template.get('tasks', [])
    preview += f"**Tasks ({len(tasks)}):**\n"
    for i, task in enumerate(tasks):
        preview += f"  {i+1}. {task.get('name', 'Unnamed Task')}\n"
        preview += f"     - Max Steps: {task.get('max_steps', 'N/A')}\n"
        preview += f"     - LLM: {task.get('llm_provider', 'N/A')} / {task.get('llm_model', 'N/A')}\n"
    
    # Simulator info
    preview += f"\n**Simulator:**\n"
    preview += f"  - Provider: {template.get('simulator_provider', 'N/A')}\n"
    preview += f"  - Model: {template.get('simulator_model', 'N/A')}\n"
    preview += f"  - Temperature: {template.get('simulator_temperature', 'N/A')}\n"
    
    # Custom actions
    custom_actions = template.get('custom_actions', [])
    preview += f"\n**Custom Actions ({len(custom_actions)}):**\n"
    for action in custom_actions:
        preview += f"  - {action.get('name', 'Unnamed Action')}\n"
    
    # Parameters from metadata
    parameters = metadata.get('parameters', {})
    if parameters:
        preview += f"\n**Parameters ({len(parameters)}):**\n"
        for param_name, param_info in parameters.items():
            param_type = param_info.get('type', 'string')
            param_desc = param_info.get('description', 'No description')
            preview += f"  - **{param_name}** ({param_type}): {param_desc}\n"
    
    # Extract placeholders dynamically for validation
    detected_placeholders = extract_placeholders_from_template(template)
    # preview += f"\n**Detected Placeholders ({len(detected_placeholders)}):**\n"
    # for placeholder in detected_placeholders:
    #     preview += f"  - {{{placeholder}}}\n"
    
    return preview, detected_placeholders

def update_input_visibility(template_name):
    """Update input field visibility based on selected template"""
    if not template_name:
        # Hide all inputs if no template selected
        return [gr.update(visible=False)] * 10
    
    templates = load_templates()
    if template_name not in templates:
        return [gr.update(visible=False)] * 10
        
    template = templates[template_name]
    _, placeholders = preview_template_and_get_placeholders(template_name)
    
    # All possible input field names (we'll create 10 max)
    all_possible_placeholders = [
        'title', 'step_action', 'step_expected_result', 'max_retry', 'url',
        'product_name', 'category', 'price_range', 'ecommerce_url', 'query'
    ]
    
    updates = []
    for i, field_name in enumerate(all_possible_placeholders):
        if i < len(placeholders):
            placeholder = placeholders[i]
            info = get_parameter_info_from_metadata(template, placeholder)
            
            if info['type'] == 'number':
                updates.append(gr.update(
                    visible=True,
                    label=info['label'],
                    info=info['description'],
                    value=3 if placeholder == 'max_retry' else None
                ))
            else:
                updates.append(gr.update(
                    visible=True,
                    label=info['label'],
                    placeholder=info['placeholder_text'],
                    info=info['description'],
                    lines=3 if info['type'] == 'textarea' else 1
                ))
        else:
            updates.append(gr.update(visible=False))
    
    return updates

def read_markdown_report(case_id):
    """Read markdown report from the task folder"""
    try:
        root_report = os.getenv("ROOT_REPORT", "E:/official_DopikAI/ai-agent-tester/reports")
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
        _, placeholders = preview_template_and_get_placeholders(template_name)
        
        # Map inputs to placeholders
        inputs = [input1, input2, input3, input4, input5, input6, input7, input8, input9, input10]
        placeholder_dict = {}
        
        for i, placeholder in enumerate(placeholders):
            if i < len(inputs) and inputs[i] is not None and str(inputs[i]).strip():
                placeholder_dict[placeholder] = inputs[i]
        
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
                root_report = os.getenv("ROOT_REPORT", "E:/official_DopikAI/ai-agent-tester/reports")
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
    
    with gr.Blocks(title="AI Agent Tester", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🤖 AI Agent Test Runner")
        gr.Markdown("Run automated browser tests with configurable templates. Input fields change dynamically based on the selected template's placeholders.")
        
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
                        root_report = os.getenv("ROOT_REPORT", "E:/official_DopikAI/ai-agent-tester/reports")
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
