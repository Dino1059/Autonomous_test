"""
Utility functions for working with Language Models
"""
import os
import logging
from typing import Dict, Any, Optional, Type
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, create_model, Field
from app.serializers.models import TaskConfig

def create_llm_for_task(task_config: TaskConfig):
    """Create an LLM instance based on task configuration"""
    provider = task_config.llm_provider
    model = task_config.llm_model
    temperature = task_config.llm_temperature
    
    if provider == "google":
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            top_p=1.0,
            top_k=40,
            max_output_tokens=2048,
            google_api_key=os.getenv('GEMINI_API_KEY')
        )
    elif provider == "openai":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
    elif provider == "openrouter":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

def create_dynamic_output_model(fields_definition: Dict[str, Any]) -> Type[BaseModel]:
    """
    Dynamically creates a Pydantic model based on field definitions
    
    Args:
        fields_definition: Dictionary with field names as keys and field types/defaults as values
                           Format: {"field_name": {"type": "str", "description": "Field description", "default": "optional default value"}}
    
    Returns:
        A Pydantic model class
    """
    from app.serializers.models import MetadataCampaign
    
    if not fields_definition:
        return MetadataCampaign  # Fallback to default model
    
    field_dict = {}
    
    for field_name, field_config in fields_definition.items():
        field_type = field_config.get("type", "str")
        field_description = field_config.get("description", "")
        field_default = field_config.get("default", ...)  # ... means required field in Pydantic
        
        # Map string type names to actual Python types
        type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict
        }
        
        python_type = type_mapping.get(field_type, str)
        
        # Create Pydantic Field with description
        if field_default == ...:
            field_dict[field_name] = (python_type, Field(..., description=field_description))
        else:
            field_dict[field_name] = (python_type, Field(field_default, description=field_description))
    
    # Create and return the model
    return create_model("DynamicOutputModel", **field_dict) 