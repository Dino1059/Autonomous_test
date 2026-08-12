"""
Pydantic models for serializing request and response data
"""
from typing import Dict, Any, List, Optional, Type, Generic, TypeVar
from pydantic import BaseModel, Field, create_model

T = TypeVar('T')

class TaskConfig(BaseModel):
    name: str = Field(..., description="Name of the task")
    prompt: str = Field(..., description="Task prompt with instructions")
    max_steps: int = Field(30, description="Maximum number of steps for this task")
    
    # Controller configuration
    output_model_fields: Optional[Dict[str, Any]] = Field(None, description="Custom output model fields definition (if use_output_model is True)")
    exclude_actions: List[str] = Field(default_factory=list, description="List of actions to exclude from the controller")
    
    # LLM configuration
    llm_provider: str = Field("google", description="LLM provider (google, openai, openrouter)")
    llm_model: str = Field("gemini-2.0-flash", description="LLM model name")
    llm_temperature: float = Field(0.0, description="LLM temperature")

    # Memory configuration
    enable_memory: bool = Field(False, description="Whether to enable memory")
    memory_interval: int = Field(7, description="Memory interval")
    initial_actions: List[Dict[str, Any]] = Field(default_factory=list, description="Initial actions to perform")
    
    # Allow arbitrary additional fields through Config
    class Config:
        extra = "allow"  # Allow any extra attributes to be passed to Agent constructor

class BrowserConfig(BaseModel):
    """Browser configuration for browser-use and playwright settings"""
    # Browser-Use specific parameters
    keep_alive: Optional[bool] = Field(False, description="Keep browser alive after agent finishes")
    allowed_domains: Optional[List[str]] = Field(None, description="List of allowed domains for navigation")
    disable_security: Optional[bool] = Field(None, description="Disable browser security features")
    highlight_elements: Optional[bool] = Field(None, description="Highlight interactive elements")
    viewport_expansion: Optional[int] = Field(None, description="Expand viewport for better element detection")
    
    # Common Playwright launch options
    headless: Optional[bool] = Field(None, description="Run browser in headless mode")
    executable_path: Optional[str] = Field(None, description="Path to browser executable")
    user_data_dir: Optional[str] = Field(None, description="Path to user data directory")
    profile_directory: Optional[str] = Field(None, description="Browser profile directory name")
    args: Optional[List[str]] = Field(None, description="Additional browser arguments")
    
    # Viewport settings
    viewport: Optional[Dict[str, int]] = Field(None, description="Viewport size settings")
    user_agent: Optional[str] = Field(None, description="Custom user agent string")
    device_scale_factor: Optional[float] = Field(None, description="Device scale factor")
    
    # Connection settings
    wss_url: Optional[str] = Field(None, description="WSS URL for playwright-protocol connection")
    cdp_url: Optional[str] = Field(None, description="CDP URL for Chrome DevTools Protocol connection")
    browser_pid: Optional[int] = Field(None, description="PID of running browser process to connect to")
    
    # Security and privacy settings
    ignore_https_errors: Optional[bool] = Field(None, description="Ignore HTTPS errors")
    bypass_csp: Optional[bool] = Field(None, description="Bypass Content Security Policy")
    permissions: Optional[List[str]] = Field(None, description="Browser permissions to grant")
    
    # Recording settings
    record_video_dir: Optional[str] = Field(None, description="Directory to save video recordings")
    record_har_path: Optional[str] = Field(None, description="Path to save HAR file")
    
    # Environment variable fallbacks
    browser_binary_path: Optional[str] = Field(None, description="Browser binary path (fallback to BROWSER_BINARY_PATH env var)")
    
    class Config:
        extra = "allow"  # Allow any additional playwright/browser-use parameters

class CustomAction(BaseModel):
    name: str = Field(..., description="Name of the action to display to the agent")
    code: str = Field(..., description="Python code for the action function")

class RunTaskRequest(BaseModel):
    tasks: List[TaskConfig] = Field(..., description="List of tasks to run")
    laminar_api_key: str = Field("", description="Laminar API key")
    laminar_base_url: str = Field("", description="Laminar base URL")
    laminar_http_port: int = Field(0, description="Laminar HTTP port")
    laminar_grpc_port: int = Field(0, description="Laminar gRPC port")
    session_id: str = Field(..., description="Session ID")
    simulator_provider: str = Field(..., description="User simulator provider")
    simulator_model: str = Field(..., description="User simulator model")
    simulator_temperature: float = Field(..., description="User simulator temperature")
    simulator_task: str = Field("", description="User simulator task description")
    custom_actions: List[CustomAction] = Field(default_factory=list, description="Custom actions to register")
    browser_config: Optional[BrowserConfig] = Field(None, description="Browser configuration settings")

class RunTaskResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Task execution results")
    history: List[Dict[str, Any]] = Field(..., description="Task execution history")

class EnvironmentVariablesRequest(BaseModel):
    openai_api_key: str = Field("", description="OpenAI API key")
    gemini_api_key: str = Field("", description="Google Gemini API key")
    hub1_api_key: str = Field("", description="Hub1 API key")
    hub1_api_base_url: str = Field("https://hub1-api.softaibox.com/v1", description="Hub1 API base URL")

class GeneratePlanRequest(BaseModel):
    prompt: str = Field(..., description="Natural language test prompt")
    llm_provider: str = Field("google", description="LLM provider")
    llm_model: str = Field("gemini-2.0-flash", description="LLM model name")

class GeneratePlanResponse(BaseModel):
    title: str = Field(..., description="Test plan title")
    objective: str = Field(..., description="Test objective")
    target_url: str = Field(..., description="Target web URL")
    preconditions: List[str] = Field(default_factory=list, description="Preconditions")
    test_data: Dict[str, Any] = Field(default_factory=dict, description="Test data key-value pairs")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Test steps list")

class MessageResponse(BaseModel):
    message: str = Field(..., description="Response message")

class DataResponse(BaseModel, Generic[T]):
    data: T
    message: str = "Success" 