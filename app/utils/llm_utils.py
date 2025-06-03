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
from datetime import datetime
import logging
from app.utils.prompts import ReportPrompt
import json
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()
def create_llm_for_task(task_config: TaskConfig):
    """Create an LLM instance based on task configuration"""
    provider = task_config.llm_provider
    model = task_config.llm_model
    temperature = task_config.llm_temperature
    
    return create_custom_llm(provider, model, temperature)

def create_custom_llm(provider: str, model: str, temperature: float):
    """Create a custom LLM instance with specified provider, model and temperature"""
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
            #temperature=temperature,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
    elif provider == "openrouter":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv('OPENROUTER_API_KEY'),
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

async def generate_report(
    task: str,
    **kwargs
) -> None:
    """
    Generate a markdown report summarizing the agent's execution and save it to a file.

    Args:
        task (str): The task description.
        reporter (LangchainModel): The reporter model.
        report_folder (str): The folder to save the report.
        state (State): The state of the agent.
        is_report_reasoning (bool): Whether to include reasoning in the report.
        extend_report_system_message (str): An optional system message to extend the report.
        use_vision_for_report (bool): Whether to use vision for the report.
    """
    logger = logging.getLogger(__name__)
    
    # Ensure report directory exists
    os.makedirs(kwargs['report_folder'], exist_ok=True)
    
    # Generate timestamp once and reuse
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"report_{timestamp}.md"
    report_path = os.path.join(kwargs['report_folder'], report_filename)
    
    logger.info(f"Generating report at: {report_path}")

    # Pre-collect data from history to avoid multiple iterations
    history_data = {
        "urls": kwargs['state'].history.urls(),
        "screenshots": kwargs['state'].history.screenshots(),
        "errors": kwargs['state'].history.errors(),
        "is_successful": kwargs['state'].history.is_successful(),
        "final_result": kwargs['state'].history.final_result(),
        "total_input_tokens": kwargs['state'].history.total_input_tokens(),
        "total_duration": kwargs['state'].history.total_duration_seconds()
    }
    
    # Build history summary using a list for better performance
    history_summary = [
        f"# Task: {task}",
        f"- Steps completed: {kwargs['state'].n_steps}",
        f"- Success: {history_data['is_successful']}",
        f"- Final Result: {json.dumps(history_data['final_result'], indent=2)}",
        f"- Tokens used (approx.): {history_data['total_input_tokens']}",
        f"- Duration: {history_data['total_duration']} seconds",
        "\n## URLs Visited:"
    ]
    
    # Add URLs
    history_summary.extend([f"- {url}" for url in history_data["urls"]])
    
    # Add execution steps
    history_summary.append("\n## Execution Steps:")
    for i, history_item in enumerate(kwargs['state'].history.history):
        history_summary.append(f"\n### Step {i + 1}:")
        
        # Add state info if available
        if history_item.state:
            history_summary.append(f"- URL: {history_item.state.url}")
            history_summary.append(f"- Title: {history_item.state.title}")
        
        # Add actions if available
        if history_item.model_output and history_item.model_output.action:
            history_summary.append("\n#### Actions:")
            actions = [
                f"- Action {j + 1}: `{json.dumps(action.model_dump(exclude_unset=True))}`" 
                for j, action in enumerate(history_item.model_output.action)
            ]
            history_summary.extend(actions)
        
        # Add results if available
        if history_item.result:
            history_summary.append("\n#### Results:")
            for j, result in enumerate(history_item.result):
                if result.extracted_content:
                    history_summary.append(f"- Result {j + 1}: {result.extracted_content}")
                if result.error:
                    history_summary.append(f"- Error {j + 1}: {result.error}")
        
        # Add metadata if available
        if history_item.metadata:
            duration = history_item.metadata.step_end_time - history_item.metadata.step_start_time
            history_summary.append("\n#### Metadata:")
            history_summary.append(f"- Duration: {duration:.2f} seconds")
            history_summary.append(f"- Input tokens: {history_item.metadata.input_tokens}")
    
    # Add errors if any
    if history_data["errors"]:
        history_summary.append("\n## Errors Encountered:")
        history_summary.extend([f"- {error}" for error in history_data["errors"] if error])
    
    # Join all lines into a single string
    summary_text = "\n".join(history_summary)
    
    # Save plain history summary
    history_path = os.path.join(kwargs['report_folder'], f"history_summary_{timestamp}.txt")
    try:
        with open(history_path, "w", encoding="utf-8") as f:
            f.write(summary_text)
    except Exception as e:
        logger.error(f"Failed to write history summary: {str(e)}")
    
    # Create the report messages
    report_messages = [
        ReportPrompt(task=task).get_system_message(
            is_report_reasoning=kwargs['is_report_reasoning'],
            extend_report_system_message=kwargs['extend_report_system_message'],
        )
    ]
    
    # Handle message content with or without screenshots
    message_content = summary_text
    if kwargs['use_vision_for_report'] and history_data["screenshots"]:
        # Find the last valid screenshot
        last_screenshot = next((s for s in reversed(history_data["screenshots"]) if s), None)
        if last_screenshot:
            message_content = [
                {'type': 'text', 'text': summary_text},
                {
                    'type': 'image_url',
                    'image_url': {'url': f'data:image/png;base64,{last_screenshot}'},
                },
            ]
    
    report_messages.append(HumanMessage(content=message_content))
    
    try:
        # Generate report using LLM
        response = await kwargs['reporter'].ainvoke(report_messages)
        report_content = str(response.content)
        
        # Clean up report content
        report_content = (report_content
                          .replace("<start_of_report>", "")
                          .replace("<end_of_report>", "")
                          .strip())
        
        # Write report to file
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        logger.info(f"Report generated successfully at: {report_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        # Re-raise with contextual information
        raise Exception(f"Failed to generate report: {str(e)}") from e