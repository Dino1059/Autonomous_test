"""
Utility functions for working with Language Models
"""
import os
import logging
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, create_model, Field
from app.serializers.models import TaskConfig
from typing import Dict, Any, Type, List as TypingList, Union

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

def _map_json_schema_type_to_python(schema_type: Union[str, list]) -> Any:
    """Maps JSON schema type(s) to a Python type."""
    # Handles cases like "type": ["string", "null"] by picking the first non-null type.
    # For Pydantic, if a field is not required and has no default, it becomes Optional.
    # If a default of None is provided, it also implies Optional.
    if isinstance(schema_type, list):
        py_type_str = next((t for t in schema_type if t != "null"), "string") # Default to string if only "null" or empty
    else:
        py_type_str = schema_type

    mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": TypingList[Any],  # Generic list, refined by "items"
        "object": Any             # Generic object, refined by "properties" / becomes a nested model
    }
    return mapping.get(py_type_str, Any) # Default to Any if type is unknown or not directly mapped

def create_model_from_schema(
    schema: Dict[str, Any],
    model_name: str = "DynamicOutputModel"
) -> Type[BaseModel]:
    """
    Dynamically creates a Pydantic model from a JSON schema definition.

    Args:
        schema: A dictionary representing the JSON schema for the model.
                Example:
                {
                  "type": "object",
                  "properties": {
                    "response": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "title": {"type": "string", "description": "The title"},
                          "url": {"type": "string"}
                        },
                        "required": ["title", "url"]
                      },
                      "description": "A list of responses"
                    }
                  },
                  "required": ["response"]
                }
        model_name: The name for the Pydantic model to be created.
                    Nested models will be named based on this and the field name.

    Returns:
        A Pydantic model class.
    """
    pydantic_fields: Dict[str, Any] = {}

    if schema.get("type") != "object":
        raise ValueError(f"The root schema 'type' must be 'object' to create a Pydantic model, got '{schema.get('type')}' for model '{model_name}'.")

    schema_properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    for field_name, field_schema in schema_properties.items():
        field_type_str_or_list = field_schema.get("type")
        if field_type_str_or_list is None:
            # If type is not specified, default to 'any' or handle as error
            # For now, let's assume 'any' (str for simplicity if no further info)
            # A stricter schema would always have a type.
            actual_field_type = Any
        else:
            actual_field_type = _map_json_schema_type_to_python(field_type_str_or_list)

        field_description = field_schema.get("description", "")
        # Pydantic's Field uses `...` (Ellipsis) for required fields without a default.
        # If a field is not in 'required' and has no 'default', it's optional (default=None).
        # If 'default' is explicitly in field_schema, that value is used.
        field_default_value = field_schema.get("default")
        is_required = field_name in required_fields

        pydantic_param_default = ...

        if "default" in field_schema: # Explicit default is provided in schema
            pydantic_param_default = field_default_value
        elif not is_required: # Not required and no explicit default, so optional (Pydantic default is None)
            pydantic_param_default = None
        # Else (is_required and no "default" in field_schema): pydantic_param_default remains ...


        if actual_field_type is Any and field_schema.get("type") == "object" and "properties" in field_schema: # Check original type
            # Nested model definition
            nested_model_name = f"{model_name}_{field_name.capitalize()}"
            actual_field_type = create_model_from_schema(field_schema, model_name=nested_model_name)
        elif actual_field_type == TypingList[Any] and field_schema.get("type") == "array": # Check original type
            items_schema = field_schema.get("items")
            if items_schema:
                item_type_str_or_list = items_schema.get("type")
                if item_type_str_or_list is None:
                    item_python_type = Any
                else:
                    item_python_type = _map_json_schema_type_to_python(item_type_str_or_list)

                if item_python_type is Any and items_schema.get("type") == "object" and "properties" in items_schema: # Check original type
                    # List of nested models
                    item_model_name = f"{model_name}_{field_name.capitalize()}Item"
                    nested_item_model = create_model_from_schema(items_schema, model_name=item_model_name)
                    actual_field_type = TypingList[nested_item_model]
                else:
                    # List of primitive types (or Any if item type couldn't be resolved)
                    actual_field_type = TypingList[item_python_type] # type: ignore
            else:
                # Array type with no "items" specified, defaults to List[Any]
                actual_field_type = TypingList[Any] # type: ignore

        pydantic_fields[field_name] = (actual_field_type, Field(default=pydantic_param_default, description=field_description))

    # Create the dynamic Pydantic model
    DynamicModel = create_model(model_name, **pydantic_fields) # type: ignore

    # Configure model (optional, based on your previous function)
    # Pydantic v2 uses model_config as a dict or a ConfigDict
    DynamicModel.model_config = {
        "json_encoders": {},
        "arbitrary_types_allowed": True,
        "extra": "ignore" # Ignores extra fields during parsing
    }

    return DynamicModel