import requests
import json
import os
import time
import pandas as pd
import gradio as gr
import csv
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from reports.prompt_templates import *

# API endpoint
API_BASE_URL = "http://localhost:8081"

def create_payload(case_row):
    """Create task payload with prompts populated from CSV data row"""
    # Classify the test case into FC or other types
    if case_row['case_id'][:2] == "FC":
        row_prompt = FC_PROMPT.format(
            title=case_row['title'],
            step_action=case_row['step_action'],
            step_expected_result=case_row['step_expected_result'],
            max_retry=case_row['max_retry']
        )
        FC_TASK['prompt'] = row_prompt
        FC_TASK['report_folder'] = FC_TASK['report_folder'] + f"/{case_row['case_id']}"

        payload = {
            "tasks": [
                FC_TASK
            ],
            "laminar_api_key": os.getenv("LAMINAR_API_KEY", ""),
            "laminar_base_url": os.getenv("LAMINAR_BASE_URL", ""),
            "laminar_http_port": int(os.getenv("LAMINAR_HTTP_PORT", "0") or 0),
            "laminar_grpc_port": int(os.getenv("LAMINAR_GRPC_PORT", "0") or 0),
            "session_id": f"test-session-id-{case_row['case_id']}",
            "simulator_provider": "google",
            "simulator_model": "gemini-2.0-flash",
            "simulator_temperature": 0.0,
            "simulator_task": "",
            "custom_actions": [screenshot_action],
            "use_own_browser": True,
        }

        return payload
    else:
        row_prompt_setup = PROMPT_TASK_SETUP.format(campaign_name=case_row['case_id'])
        row_prompt_simulator = PROMPT_SIMULATOR.format(
            title=case_row['title'], 
            step_action=case_row['step_action'], 
            step_expected_result=case_row['step_expected_result'], 
            max_retry=case_row['max_retry']
        )
    
        TASK_SETUP['prompt'] = row_prompt_setup
    
        payload = {
            "tasks": [
                TASK_SETUP,
                TASK_CHAT
            ],
            "laminar_api_key": os.getenv("LAMINAR_API_KEY", ""),
            "laminar_base_url": os.getenv("LAMINAR_BASE_URL", ""),
            "laminar_http_port": int(os.getenv("LAMINAR_HTTP_PORT", "0") or 0),
            "laminar_grpc_port": int(os.getenv("LAMINAR_GRPC_PORT", "0") or 0),
            "session_id": f"test-session-id-{case_row['case_id']}",
            "simulator_provider": "google",
            "simulator_model": "gemini-2.0-flash",
            "simulator_temperature": 0.0,
            "simulator_task": row_prompt_simulator,
            "custom_actions": []
        }
    
        return payload


def run_test_case(case_row):
    """Run a test case with the specified case row and return the results"""
    payload = create_payload(case_row)
    
    try:
        response = requests.post(f"{API_BASE_URL}/tasks/run", json=payload)
    
        if response.status_code == 200:
            # Extract task ID
            task_id = response.json()['data']["message"].split(": ")[1]
            
            # Poll for results
            return poll_results(task_id)
        else:
            return {
                "status": "failed", 
                "error": f"API Error: {response.status_code} - {response.text}", 
                "results": [], 
                "simulator_interactions": []
            }
    except Exception as e:
        return {
            "status": "failed",
            "error": f"Exception: {str(e)}",
            "results": [],
            "simulator_interactions": []
        }


def poll_results(task_id):
    """Poll the API for task results and return the data"""
    
    max_attempts = 100
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        try:
            response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
        
            if response.status_code == 200:
                data = response.json()['data']
                status = data.get("status")
            
                if status in ["completed", "failed", "cancelled"]:
                    return {
                        "status": status,
                        "results": data.get("results", []),
                        "simulator_interactions": data.get("simulator_interactions", []),
                        "error": data.get("error", ""),
                    }
        except Exception as e:
            pass  # Continue polling on error
        
        # Wait before polling again
        time.sleep(5)
    
    return {"status": "timeout", "error": "Max polling attempts reached", "results": [], "simulator_interactions": []}


def process_csv(file_obj):
    """Process the uploaded CSV file and return a DataFrame"""
    csv_data = pd.read_csv(file_obj.name)
    
    # Ensure required columns exist
    required_cols = ['case_id', 'category', 'title', 'step_action', 'step_expected_result', 'max_retry']
    for col in required_cols:
        if col not in csv_data.columns:
           # raise error
           raise ValueError(f"Column {col} is required but not found in the CSV file")
        
    if 'status' not in csv_data.columns:
        csv_data['status'] = 'pending'

    if 'error' not in csv_data.columns:
        csv_data['error'] = ''
    
    if 'last_run' not in csv_data.columns:
        csv_data['last_run'] = ''

    if 'report_path' not in csv_data.columns:
        csv_data['report_path'] = ''

    if 'result' not in csv_data.columns:
        csv_data['result'] = ''
        
    return csv_data


def run_single_test(df, row_idx):
    """Run a single test case and update the DataFrame"""
    case_row = df.iloc[row_idx].to_dict()
    
    # Update status to 'running'
    df.at[row_idx, 'status'] = 'running'
    
    # Run the test case
    result = run_test_case(case_row)
    
    # Update status, grade, and last_run
    df.at[row_idx, 'status'] = result['status']
    df.at[row_idx, 'result'] = result['results']
    df.at[row_idx, 'last_run'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.at[row_idx, 'error'] = result['error']
    
    return df


def run_pending_tests_sequentially(df, progress=gr.Progress()):
    """Run pending tests sequentially and update the DataFrame with progress bar"""
    if df is None or len(df) == 0:
        return df, None, "No data loaded"
    
    # Find indices of pending tests
    pending_indices = df[df['status'] == 'pending'].index.tolist()
    
    if not pending_indices:
        return df, None, "No pending tests found"
    
    # Make a copy of the dataframe to avoid modifying the original during iteration
    working_df = df.copy()
    total_tests = len(pending_indices)
    
    # Initialize progress
    progress(0, desc=f"Starting {total_tests} pending tests...")
    
    # Process each test sequentially
    for i, idx in enumerate(pending_indices):
        case_row = working_df.iloc[idx].to_dict()
        case_id = case_row['case_id']
        
        # Update progress
        progress((i/total_tests), desc=f"Running test {i+1}/{total_tests}: {case_id}")
        
        # Set status to running
        working_df.at[idx, 'status'] = 'running'
        
        # Run the test
        result = run_test_case(case_row)
        
        # Update dataframe with results
        working_df.at[idx, 'status'] = result['status']
        working_df.at[idx, 'result'] = result['results']
        working_df.at[idx, 'last_run'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        working_df.at[idx, 'error'] = result['error']
    
    # Complete progress
    progress(1.0, desc=f"Completed {total_tests} pending tests")
    
    return working_df, None, f"Completed {total_tests} pending tests."


def save_results_to_csv(df, original_file=None):
    """Save results to the original CSV file"""
    if original_file:
        # Save directly to the original file
        original_path = Path(original_file)
        df.to_csv(original_path, index=False)
        return f"Results saved to original file: {original_path}"
    else:
        # Fallback: Create new file with timestamp if original not available
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create the temp_result_gradio directory if it doesn't exist
        result_dir = Path(__file__).parent / "temp_result_gradio"
        result_dir.mkdir(exist_ok=True)
        
        output_path = result_dir / f"test_results_{timestamp}.csv"
        df.to_csv(output_path, index=False)
        return str(output_path)


def get_report_folders():
    """Get all folders in the reports directory"""
    reports_dir = Path("E:/official_DopikAI/ai-agent-tester/reports")
    if not reports_dir.exists():
        return []
    
    # Get only directories in the reports folder
    folders = [str(f.name) for f in reports_dir.iterdir() if f.is_dir()]
    return folders


def get_markdown_files(folder_name):
    """Get all markdown files in the specified folder"""
    folder_path = Path(f"E:/official_DopikAI/ai-agent-tester/reports/{folder_name}")
    if not folder_path.exists():
        return []
    
    # Get only .md files
    md_files = [str(f.name) for f in folder_path.iterdir() if f.is_file() and f.suffix.lower() == '.md']
    return md_files


def read_markdown_file(folder_name, file_name):
    """Read the content of a markdown file"""
    file_path = Path(f"E:/official_DopikAI/ai-agent-tester/reports/{folder_name}/{file_name}")
    if not file_path.exists():
        return f"File not found: {file_path}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


def create_ui():
    """Create the Gradio UI"""
    with gr.Blocks(title="AI Agent Test Runner", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🤖 AI Agent Test Runner")
        
        with gr.Row():
            with gr.Column(scale=2):
                csv_file = gr.File(label="Upload Test Cases CSV", file_types=[".csv"])
            with gr.Column(scale=1):
                load_btn = gr.Button("📂 Load CSV", variant="primary")
        
        with gr.Row():
            with gr.Column(scale=4):
                df_output = gr.Dataframe(
                    headers=["case_id", "category", "title", "step_action", "step_expected_result", "max_retry", "status", "error", "result", "report_path", "last_run"],
                    datatype=["str", "str", "str", "str", "str", "str", "str", "str", "str", "str", "str"],
                    label="Test Cases",
                    interactive=False,
                    elem_id="test_cases_table"
                )
            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### 🚀 Test Controls")
                    case_id_input = gr.Textbox(
                        label="Case ID",
                        placeholder="Enter a case ID to run a single test",
                        elem_id="case_id_input"
                    )
                    run_single_btn = gr.Button("▶️ Run Single Test", variant="primary")
                    run_pending_btn = gr.Button("🔄 Run Pending Tests Sequentially", variant="secondary")
                    export_btn = gr.Button("💾 Save Results", variant="secondary")
        
        # Test Results section
        gr.Markdown("### 📊 Report Viewer")
        with gr.Row():
            with gr.Column(scale=1):
                report_folders = gr.Dropdown(label="Report Folders", choices=get_report_folders(), interactive=True)
                refresh_folders_btn = gr.Button("🔄 Refresh Folders", size="sm")
            
            with gr.Column(scale=3):
                markdown_content = gr.Markdown("Select a folder to view report", elem_id="markdown_content")
        
        status_bar = gr.Markdown("Ready to load test cases", elem_id="status_bar")
        csv_path = gr.State(None)  # Store the path to the loaded CSV file
        results_json = gr.State(None)  # Keep this for compatibility with existing code
        
        # Load CSV event
        def load_csv(file_obj):
            if file_obj is None:
                return None, None, "Please upload a CSV file", None
            
            try:
                df = process_csv(file_obj)
                return df, None, f"Loaded {len(df)} test cases from {file_obj.name}", file_obj.name
            except Exception as e:
                return None, None, f"Error loading CSV: {str(e)}", None
        
        load_btn.click(
            fn=load_csv,
            inputs=[csv_file],
            outputs=[df_output, results_json, status_bar, csv_path]
        )
        
        # Run single test by case ID
        def run_single_by_id(df, case_id, progress=gr.Progress()):
            if df is None:
                return df, None, "No data loaded"
            
            if not case_id:
                return df, None, "Please enter a case ID"
            
            # Find the case in the dataframe
            matching_rows = df[df['case_id'] == case_id]
            if len(matching_rows) == 0:
                return df, None, f"Case ID {case_id} not found"
            
            row_idx = matching_rows.index[0]
            
            # Update the status message
            progress(0, desc=f"Running test for case ID: {case_id}")

            # Update dataframe and get results
            df, results, _ = run_single_test(df, row_idx)
            
            progress(1.0, desc=f"Completed test for case ID: {case_id}")
            status_msg = f"Completed test for case ID: {case_id} - Status: {df.at[row_idx, 'status']}"
            
            return df, results, status_msg
        
        run_single_btn.click(
            fn=run_single_by_id,
            inputs=[df_output, case_id_input],
            outputs=[df_output, results_json, status_bar]
        )
        
        run_pending_btn.click(
            fn=run_pending_tests_sequentially,
            inputs=[df_output],
            outputs=[df_output, results_json, status_bar]
        )
        
        # Save results to original file
        def save_results(df, csv_path_val):
            if df is None or len(df) == 0:
                return "No data to save"
            
            if not csv_path_val:
                return "Original file path not available"
            
            try:
                result = save_results_to_csv(df, csv_path_val)
                return result
            except Exception as e:
                return f"Error saving results: {str(e)}"
        
        export_btn.click(
            fn=save_results,
            inputs=[df_output, csv_path],
            outputs=[status_bar]
        )
        
        # Report viewer event handlers
        def update_folders():
            """Refresh the list of folders in the reports directory"""
            return get_report_folders()
        
        def display_markdown_from_folder(folder):
            """Display the markdown file from the selected folder"""
            if not folder:
                return "Please select a folder to view the report"
            
            # Get the first markdown file in the folder
            md_files = get_markdown_files(folder)
            if not md_files:
                return f"No markdown files found in folder: {folder}"
            
            # Read the first markdown file
            return read_markdown_file(folder, md_files[0])
        
        # Connect event handlers
        refresh_folders_btn.click(
            fn=update_folders,
            inputs=[],
            outputs=[report_folders]
        )
        
        report_folders.change(
            fn=display_markdown_from_folder,
            inputs=[report_folders],
            outputs=[markdown_content]
        )
        
        # Add some custom CSS for better styling
        gr.Markdown("""
        <style>
        #test_cases_table .selected { background-color: #e6f7ff !important; }
        #status_bar { 
            margin-top: 10px; 
            padding: 10px; 
            background-color: #f0f0f0; 
            border-radius: 5px;
            font-weight: bold;
        }
        #markdown_content {
            border: 1px solid #e0e0e0;
            padding: 15px;
            border-radius: 5px;
            background-color: #ffffff;
            max-height: 600px;
            overflow-y: auto;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        #markdown_content h1, #markdown_content h2, #markdown_content h3 {
            margin-top: 16px;
            margin-bottom: 8px;
            font-weight: 600;
        }
        #markdown_content pre {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        #markdown_content code {
            font-family: Consolas, Monaco, 'Andale Mono', monospace;
            background-color: rgba(0,0,0,0.05);
            padding: 2px 4px;
            border-radius: 4px;
        }
        #markdown_content img {
            max-width: 100%;
            height: auto;
        }
        #markdown_content table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        #markdown_content th, #markdown_content td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        #markdown_content th {
            background-color: #f2f2f2;
        }
        </style>
        """)
    
    return demo

demo = create_ui()
demo.launch()