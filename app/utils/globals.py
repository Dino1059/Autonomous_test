"""
Global variables and settings for the application
"""
from typing import Dict, Any, List

# Global variables for settings and task storage
SETTINGS = {
    "web_app_url": "",
    "laminar_project_api_key": "",
    "laminar_base_url": "",
    "laminar_http_port": 0,
    "laminar_grpc_port": 0,
    "session_id": "",
    "user_simulator_task": ""
}

# Global dictionary to store background tasks
# Format: {task_id: {"status": "running|completed|failed|cancelled|cancelling", "results": [...], ...}}
BACKGROUND_TASKS: Dict[str, Dict[str, Any]] = {}

# Global dictionary to store user simulator interactions
USER_SIMULATOR_INTERACTIONS: Dict[str, List[Dict[str, Any]]] = {}

# Global dictionary to track cancellation status
# Format: {task_id: bool} where True means the task should be cancelled
CANCELLATION_FLAGS: Dict[str, bool] = {}

# Global variables for simulation settings
simulator_provider = ""
simulator_model = ""
simulator_temperature = 0.0
llm_worker = None

def update_settings(new_settings):
    """Update the global settings dictionary"""
    SETTINGS.update(new_settings) 