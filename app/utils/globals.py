"""
Global variables and settings for the application
"""
from typing import Dict, Any, List

# Global variables for settings and task storage
SETTINGS = {
    "laminar_project_api_key": "",
    "laminar_base_url": "",
    "laminar_http_port": 0,
    "laminar_grpc_port": 0,
    "session_id": "",
    "user_simulator_task": "",
    "use_own_browser": False
}

# Global dictionary to store background tasks
# Format: {task_id: {"status": "running|completed|failed|cancelled|cancelling", "results": [...], ...}}
BACKGROUND_TASKS: Dict[str, Dict[str, Any]] = {}

# Global dictionary to store user simulator interactions
USER_SIMULATOR_INTERACTIONS: Dict[str, List[Dict[str, Any]]] = {}

# Global dictionary to track cancellation status
# Format: {task_id: bool} where True means the task should be cancelled
CANCELLATION_FLAGS: Dict[str, bool] = {}

# Global dictionary to store active Orchestrator instances for Human-in-the-Loop interactions
# Format: {task_id: Orchestrator}
ACTIVE_ORCHESTRATORS: Dict[str, Any] = {}


# Global variables for simulation settings
simulator_provider = ""
simulator_model = ""
simulator_temperature = 0.0
llm_worker = None

def update_settings(new_settings):
    """Update the global settings dictionary"""
    SETTINGS.update(new_settings)
    
def get_or_initialize_llm_worker(provider=None, model=None, temperature=None):
    """
    Get the current LLM worker or initialize a new one if needed
    
    Args:
        provider (str, optional): LLM provider name
        model (str, optional): Model name
        temperature (float, optional): Temperature setting
        
    Returns:
        BaseLLMWorker: The initialized LLM worker instance
    """
    global llm_worker
    
    # If llm_worker is already initialized, return it
    if llm_worker is not None:
        return llm_worker
        
    # If we have arguments to initialize a new worker
    if provider and model and temperature is not None:
        from src.llms.base import BaseLLMWorker
        llm_worker = BaseLLMWorker(
            provider=provider,
            model=model,
            temperature=temperature
        )
        return llm_worker
        
    # If we can use settings values
    if SETTINGS.get("simulator_provider") and SETTINGS.get("simulator_model") and SETTINGS.get("simulator_temperature") is not None:
        from src.llms.base import BaseLLMWorker
        llm_worker = BaseLLMWorker(
            provider=SETTINGS["simulator_provider"],
            model=SETTINGS["simulator_model"],
            temperature=SETTINGS["simulator_temperature"]
        )
        return llm_worker
        
    # If no way to initialize, return None
    return None