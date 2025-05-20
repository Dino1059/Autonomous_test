"""
Pydantic models for serializing request and response data
"""
from typing import Dict, Any, List, Optional, Type, Generic, TypeVar
from pydantic import BaseModel, Field, create_model, Extra

T = TypeVar('T')

class MetadataCampaign(BaseModel):
    campaign_name: str
    campaign_id: str
    thread_id: str

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
    use_own_browser: bool = Field(False, description="Whether to use the user's own browser with user data")

class RunTaskResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Task execution results")
    history: List[Dict[str, Any]] = Field(..., description="Task execution history")

class EnvironmentVariablesRequest(BaseModel):
    openai_api_key: str = Field("", description="OpenAI API key")
    gemini_api_key: str = Field("", description="Google Gemini API key")

class MessageResponse(BaseModel):
    message: str = Field(..., description="Response message")

class DataResponse(BaseModel, Generic[T]):
    data: T
    message: str = "Success" 